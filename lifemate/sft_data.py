"""SFT examples from train labels, in exactly the message format the agent uses at inference.

One example per sample: [system, *history, user, (assistant tool_call, tool result)*, assistant final].
Only the assistant messages after the last user message are trained on (see train_lora.py).

Augmentation for apps never seen in train (65% of public samples install one):
  * app renaming: a random half of the installed apps get an alias prefix (door_lock -> smart_lock) everywhere —
    schema, descriptions, history calls, gold calls, ask_missing tool_name — so the model learns to read the schema
    instead of memorising tool names
  * tool order shuffled; for samples that act (not out-of-scope), 1-3 unrelated apps added as distractors

python -m lifemate.sft_data --root data --ids splits/train_fit.txt --aug-copies 1 --out sft_fit.jsonl
"""
from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path

from .prompt import build_messages, tools_for_sample

FINAL_ACT = "Xong."
FINAL_NONE = "Không cần gọi tool nào."

ALIASES = {
    "smart_home": ["home_iot", "nha_thong_minh", "smarthome_hub"], "home_security": ["security_cam", "an_ninh"],
    "door_lock": ["smart_lock", "khoa_cua"], "robot_vacuum": ["vacuum_bot", "robot_hut_bui"],
    "appliances": ["home_devices", "thiet_bi"], "home_energy": ["power_meter", "dien_nang"],
    "alarm": ["wake_alarm", "clock"], "reminders": ["reminder_app", "nhac_viec"], "calendar": ["agenda", "schedule"],
    "notes": ["notebook", "memo"], "tasks": ["todo", "task_list"], "contacts": ["phonebook", "address_book"],
    "phone": ["dialer", "voice_call"], "sms": ["text_message", "tin_nhan"], "chat_ott": ["messenger", "chat_app"],
    "email": ["mail", "mailbox"], "video_meeting": ["meet", "video_call"], "banking": ["bank_app", "ngan_hang"],
    "ewallet": ["wallet", "vi_dien_tu"], "bill_payment": ["bills", "pay_bills"], "loyalty": ["rewards", "member_points"],
    "weather": ["forecast", "thoi_tiet"], "gold_price": ["gold_rate", "gia_vang"], "fuel_price": ["gas_price", "xang_dau"],
    "lottery": ["lotto", "xo_so"], "exchange_rate": ["fx_rate", "ty_gia"], "news": ["newsfeed", "tin_tuc"],
    "calculator": ["calc", "math_tool"], "maps": ["navigation", "ban_do"], "food_delivery": ["food_order", "giao_do_an"],
    "ride_hailing": ["ride", "taxi_app"], "flights": ["air_ticket", "ve_may_bay"], "shopping_list": ["grocery_list", "di_cho"],
    "package_tracking": ["parcel", "van_don"], "music": ["music_player", "nhac"], "tv": ["smart_tv", "television"],
    "podcast_radio": ["audio_shows", "radio"], "medication": ["pill_reminder", "thuoc"], "fitness": ["health_tracker", "tap_luyen"],
    "learning": ["courses", "hoc_tap"], "bike_rental": ["bike_share", "thue_xe_dap"], "home_automation": ["automation", "kich_ban"],
    "household_chores": ["chores", "viec_nha"], "library": ["books", "thu_vien"], "subscriptions": ["subs", "goi_dich_vu"],
    # apps that appear only in public test (used when augmenting synthetic samples)
    "ecommerce": ["online_shop", "mua_sam"], "grocery": ["supermarket", "sieu_thi"], "pantry": ["food_store", "tu_bep"],
    "recipes": ["cookbook", "cong_thuc"], "habit_tracker": ["habits", "thoi_quen"], "stocks": ["trading", "chung_khoan"],
    "event_tickets": ["events", "ve_su_kien"], "train_bus_tickets": ["coach_tickets", "ve_tau_xe"],
    "public_transit": ["transit", "xe_cong_cong"], "parking": ["car_park", "do_xe"], "translator": ["translate_app", "dich"],
}


def _rename_str(s: str, mp: dict) -> str:
    for old, new in mp.items():
        s = s.replace(old + ".", new + ".")
    return s


def _rename_call(c: dict, mp: dict) -> dict:
    c = copy.deepcopy(c)
    c["name"] = _rename_str(c["name"], mp)
    if c["name"] == "sys.ask_missing_info" and isinstance(c.get("arguments", {}).get("tool_name"), str):
        c["arguments"]["tool_name"] = _rename_str(c["arguments"]["tool_name"], mp)
    return c


def augment(item: dict, catalog_tools: dict, rng: random.Random) -> tuple[dict, dict]:
    """Returns (item', catalog_tools') with renamed apps / distractors."""
    item = copy.deepcopy(item)
    apps = item["context"]["installed_apps"]
    mp = {}
    for a in list(apps):
        if a in ALIASES and rng.random() < 0.5:
            mp[a] = rng.choice(ALIASES[a])
    acts = bool(item["label"]["tool_calls"])
    if acts:  # distractor apps (never for out-of-scope: an added app could make the request doable)
        pool = sorted({n.split(".", 1)[0] for n in catalog_tools} - set(apps) - {"sys"})
        for a in rng.sample(pool, k=min(len(pool), rng.randint(1, 3))):
            apps[a] = {"tools": sorted(n for n in catalog_tools if n.startswith(a + "."))}
    # shuffle app order
    order = list(apps)
    rng.shuffle(order)
    item["context"]["installed_apps"] = {mp.get(a, a): apps[a] for a in order}
    for a, v in item["context"]["installed_apps"].items():
        v["tools"] = [_rename_str(n, mp) for n in v["tools"]]
    cat2 = {}
    for n, t in catalog_tools.items():
        t2 = copy.deepcopy(t)
        t2["name"] = _rename_str(n, mp)
        t2["description"] = _rename_str(t2.get("description", ""), mp)
        for p in ((t2.get("parameters") or {}).get("properties") or {}).values():
            if isinstance(p.get("description"), str):
                p["description"] = _rename_str(p["description"], mp)
            if isinstance(p.get("x-ref"), str):
                p["x-ref"] = _rename_str(p["x-ref"] + ".", mp)[:-1]
        cat2[t2["name"]] = t2
    for h in item["history"]:
        if h.get("tool_calls"):
            h["tool_calls"] = [_rename_call(c, mp) for c in h["tool_calls"]]
    item["label"]["tool_calls"] = [_rename_call(c, mp) for c in item["label"]["tool_calls"]]
    return item, cat2


def asr_ok(item: dict, asr: dict, max_wer: float) -> bool:
    """True when every user turn of the sample is recognised well enough to still carry the gold call's values."""
    from .asr import clips_of, edit_distance, looks_bad, norm_words
    for p, gold in clips_of(item):
        hyp = asr.get(p, "")
        if not gold:
            continue
        if not hyp.strip() or looks_bad(hyp):
            return False
        g = norm_words(gold)
        if g and edit_distance(g, norm_words(hyp)) / len(g) > max_wer:
            return False
    return True


def _dump(x) -> str:
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


def example(item: dict, catalog_tools: dict, asr: dict | None = None) -> dict:
    """asr: {audio_path: text} -> user turns use ASR text (noisy input, same gold output) to make the LLM robust
    to recognition errors; an empty ASR text falls back to the gold transcript."""
    def tr(path, h):
        if asr is not None and asr.get(path, "").strip():
            return asr[path]
        return (h or item).get("audio_text", "")
    msgs = build_messages(item, tr)
    n_prompt = len(msgs)
    calls, results = item["label"]["tool_calls"], item["label"]["tool_results"]
    for c, r in zip(calls, results):
        msgs.append({"role": "assistant", "content": "", "tool_calls": [
            {"type": "function", "function": {"name": c["name"], "arguments": c.get("arguments") or {}}}]})
        msgs.append({"role": "tool", "content": _dump(r)})
    if calls and calls[-1]["name"] == "sys.ask_missing_info":
        msgs.pop()  # the agent stops right after ask_missing_info: no tool result, no final answer
    else:
        msgs.append({"role": "assistant", "content": FINAL_ACT if calls else FINAL_NONE})
    return {"id": item["id"], "n_prompt": n_prompt, "messages": msgs, "tools": tools_for_sample(item, catalog_tools)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data")
    ap.add_argument("--ids")
    ap.add_argument("--split", default="train", help="train, or a synthetic split built by synth_build")
    ap.add_argument("--aug-copies", type=int, default=1)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--drop-empty", action="store_true",
                    help="skip samples whose gold is [] (v6: formulaic synthetic out-of-scope samples taught the model to answer "
                         "[] to clear requests — 'no call but gold acts' rose 17->27 on val_unseen and 5->19 on val_seen)")
    ap.add_argument("--asr", help="json {audio_path: text}: adds one copy per sample with ASR transcripts")
    ap.add_argument("--asr-max-wer", type=float, default=0.25,
                    help="skip the ASR copy when a user turn of that sample is recognised worse than this. "
                         "A badly recognised turn no longer contains what the gold call needs, so the copy would "
                         "teach the model to invent the missing value instead of asking for it.")
    a = ap.parse_args()
    root = Path(a.root)
    rows = [json.loads(l) for l in open(root / a.split / f"{a.split}.jsonl", encoding="utf-8")]
    if a.ids:
        keep = set(open(a.ids).read().split())
        rows = [r for r in rows if r["id"] in keep]
    if a.drop_empty:
        n_before = len(rows)
        rows = [r for r in rows if r["label"]["tool_calls"]]
        print(f"--drop-empty: {n_before - len(rows)} samples with gold [] removed")
    cat = json.load(open(root / a.split / f"{a.split}_tools_catalog.json", encoding="utf-8"))
    tools = {t["name"]: t for ap_ in cat["apps"] for t in ap_["tools"]}
    rng = random.Random(a.seed)
    asr = json.load(open(a.asr, encoding="utf-8")) if a.asr else None
    n = n_asr = n_skip = 0
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(example(r, tools), ensure_ascii=False) + "\n")
            n += 1
            for k in range(a.aug_copies):
                r2, t2 = augment(r, tools, rng)
                ex = example(r2, t2)
                ex["id"] = f"{r['id']}#aug{k}"
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
                n += 1
            if asr is not None and asr_ok(r, asr, a.asr_max_wer):
                n_asr += 1
                ex = example(r, tools, asr)
                ex["id"] = f"{r['id']}#asr"
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
                n += 1
    print(f"{a.out}: {n} examples from {len(rows)} samples")


if __name__ == "__main__":
    main()
