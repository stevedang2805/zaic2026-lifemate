"""Build verified synthetic samples (train format) from hand- or LLM-written specs, using the organisers' simulator.

Spec: one JSON object per line (see synth_specs/example_parking.jsonl):
{
  "id": "synth_parking_0001",
  "context": {"current_time": "2026-11-20T08:30:00+07:00", "timezone": "Asia/Ho_Chi_Minh",
              "location": {"lat": 10.77, "lng": 106.70},
              "user_profile": {"name": "...", "home_address": "...", "work_address": "...", "city": "TP.HCM"},
              "installed_apps": ["parking", "calendar", "contacts"]},          # app ids; tools come from the catalog
  "state": {"parking": {...}, "calendar": {...}, "contacts": {...}},       # INITIAL data of every installed app
  "history": [{"role": "user", "audio_text": "..."},
              {"role": "assistant", "text": "...", "tool_calls": [{"name": "...", "arguments": {...}}]}],
  "audio_text": "câu yêu cầu cuối, viết như người nói",
  "gold": [{"name": "parking.find", "arguments": {}}, {"name": "parking.reserve", "arguments": {...}}]
}

What the builder does (same as the organisers' data):
  * runs the history tool calls on the initial state -> their tool_results, and state.json = state AFTER history
  * replays gold on a fresh env from that state.json -> tool_results, final_state (apps changed)
  * lints the gold against the conventions measured on train (see README): every call ok, no repeated read,
    no re-read of a fresh history read, IDs only from earlier results, ask_missing_info last with one param, ...
  * writes <root>/synth/synth.jsonl (train format) + synth_environment/<id>/state.json + catalog + zaic_tools

python -m lifemate.synth_build --root DATA --tools-from public_test --specs synth_specs/*.jsonl
Then: python -m lifemate.sft_data --root DATA --split synth --out sft_synth.jsonl
"""
from __future__ import annotations

import argparse
import copy
import glob
import json
import shutil
import sys
from pathlib import Path


def _dump(x):
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


def lint(spec: dict, tools: dict, hist_results: list, gold_results: list) -> list[str]:
    errs = []
    gold = spec["gold"]
    installed = {t for a in spec["context"]["installed_apps"] for t in tools if t.startswith(a + ".")}
    seen = _dump(hist_results) + _dump(spec.get("history", []))
    read_keys = set()
    # fresh history reads (no later write to the same app in history)
    fresh = {}
    for h in spec.get("history", []):
        for c in h.get("tool_calls") or []:
            k = (tools.get(c["name"]) or {}).get("kind")
            app = c["name"].split(".")[0]
            if k == "write":
                fresh = {kk: v for kk, v in fresh.items() if not kk.startswith(app + ".")}
            elif k == "read":
                fresh[c["name"] + _dump(dict(sorted((c.get("arguments") or {}).items())))] = True
    for i, (c, r) in enumerate(zip(gold, gold_results)):
        name = c["name"]
        if name != "sys.ask_missing_info" and name not in installed:
            errs.append(f"call {i}: {name} is not an installed tool")
        if not r.get("ok", False) and name != "sys.ask_missing_info":
            errs.append(f"call {i}: {name} failed: {r.get('error')}")
        if r.get("done") is False:
            errs.append(f"call {i}: {name} did nothing: {r.get('error') or r.get('reason') or r}")
        kind = (tools.get(name) or {}).get("kind")
        key = name + _dump(dict(sorted((c.get("arguments") or {}).items())))
        if kind == "read":
            if key in read_keys:
                errs.append(f"call {i}: repeated read {key}")
            if key in fresh:
                errs.append(f"call {i}: re-reads {name} although the history already has that result")
            read_keys.add(key)
        props = ((tools.get(name) or {}).get("parameters") or {}).get("properties") or {}
        for k, v in (c.get("arguments") or {}).items():
            if (props.get(k) or {}).get("x-ref") or k.endswith("_id"):
                for x in (v if isinstance(v, list) else [v]):
                    if isinstance(x, str) and x not in seen:
                        errs.append(f"call {i}: {k}={x!r} never appeared in an earlier tool result (gold reads before using an ID)")
        if name == "sys.ask_missing_info":
            if i != len(gold) - 1:
                errs.append("ask_missing_info must be the last call")
            a = c.get("arguments") or {}
            if a.get("tool_name") not in installed or len(a.get("params") or []) != 1:
                errs.append("ask_missing_info needs an installed tool_name and exactly one param")
        seen += _dump(r)
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data")
    ap.add_argument("--tools-from", default="public_test", help="split whose zaic_tools + catalog define the apps")
    ap.add_argument("--specs", nargs="+", required=True)
    ap.add_argument("--split", default="synth")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    src, dst = root / a.tools_from, root / a.split
    (dst / f"{a.split}_environment").mkdir(parents=True, exist_ok=True)
    if not (dst / "zaic_tools").exists():
        shutil.copytree(src / "zaic_tools", dst / "zaic_tools", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(src / f"{a.tools_from}_tools_catalog.json", dst / f"{a.split}_tools_catalog.json")
    cat = json.load(open(dst / f"{a.split}_tools_catalog.json", encoding="utf-8"))
    tools = {t["name"]: t for ap_ in cat["apps"] for t in ap_["tools"]}
    app_tools = {ap_["id"]: [t["name"] for t in ap_["tools"]] for ap_ in cat["apps"]}
    sys.path.insert(0, str(dst))
    from zaic_tools import ToolEnv  # noqa: E402

    specs = [json.loads(l) for p in a.specs for f in sorted(glob.glob(p)) for l in open(f, encoding="utf-8") if l.strip()]
    ok_rows, bad = [], 0
    for sp in specs:
        sid = sp["id"]
        try:
            apps = sp["context"]["installed_apps"]
            unknown = [x for x in apps if x not in app_tools]
            if unknown:
                raise ValueError(f"unknown apps {unknown}")
            installed = {x: {"tools": app_tools[x]} for x in apps}
            meta = {"question_id": sid, "current_time": sp["context"]["current_time"],
                    "tools": sorted(t for x in apps for t in app_tools[x])}
            init = {"_meta": meta, **{k: v for k, v in sp["state"].items() if k in apps}}
            for x in apps:
                init.setdefault(x, {})
            env_dir = dst / f"{a.split}_environment" / sid
            env_dir.mkdir(parents=True, exist_ok=True)
            # 1) history on the initial state
            (env_dir / "state.json").write_text(_dump(init), encoding="utf-8")
            henv = ToolEnv(a.split, sid, root=root)
            history = copy.deepcopy(sp.get("history", []))
            hist_results = []
            for h in history:
                if h.get("tool_calls"):
                    h["tool_results"] = [henv.call(c["name"], c.get("arguments") or {}) for c in h["tool_calls"]]
                    hist_results.append(h["tool_results"])
                    bad_h = [r for r in h["tool_results"] if not r.get("ok")]
                    if bad_h:
                        raise ValueError(f"history call failed: {bad_h[0]}")
            after = henv.get_state()  # dev-time only (building data); never used at inference
            after["_meta"] = meta
            (env_dir / "state.json").write_text(_dump(after), encoding="utf-8")
            # 2) gold on the post-history state
            env = ToolEnv(a.split, sid, root=root)
            before = copy.deepcopy(env.get_state())
            results = [env.call(c["name"], c.get("arguments") or {}) for c in sp["gold"]]
            errs = lint(sp, tools, hist_results, results)
            if errs:
                raise ValueError("; ".join(errs))
            final = env.get_state()
            changed = {k: v for k, v in final.items() if k != "_meta" and before.get(k) != v}
            for i, h in enumerate(history, 1):
                if h["role"] == "user":
                    h["audio"] = f"audio/{sid}/{sid}_u{i}.wav"
            ctx = {k: v for k, v in sp["context"].items() if k != "installed_apps"}
            ctx["installed_apps"] = installed
            ok_rows.append({"id": sid, "audio": f"audio/{sid}/{sid}.wav", "context": ctx, "history": history,
                            "audio_text": sp["audio_text"],
                            "label": {"tool_calls": sp["gold"], "tool_results": results, "final_state": changed}})
        except Exception as e:  # report and keep going
            bad += 1
            print(f"REJECT {sid}: {e}")
    with open(dst / f"{a.split}.jsonl", "w", encoding="utf-8") as f:
        for r in ok_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(ok_rows)} samples OK, {bad} rejected -> {dst / (a.split + '.jsonl')}")


if __name__ == "__main__":
    main()
