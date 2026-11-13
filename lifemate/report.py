"""Error breakdown of a train-split run: where the points are lost.

python -m lifemate.report --root data --split train --pred runs/x/submission.jsonl [--ids splits/val_unseen.txt] [--show 5]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from score import fuzzy_keys, gold_hashes, max_matching, sample_score  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data")
    ap.add_argument("--split", default="train")
    ap.add_argument("--pred", required=True)
    ap.add_argument("--ids")
    ap.add_argument("--show", type=int, default=3, help="examples printed per category")
    a = ap.parse_args()
    root = Path(a.root)
    rows = {json.loads(l)["id"]: json.loads(l) for l in open(root / a.split / f"{a.split}.jsonl", encoding="utf-8")}
    preds = {json.loads(l)["id"]: json.loads(l) for l in open(a.pred, encoding="utf-8")}
    ids = [i for i in preds if i in rows]
    if a.ids:
        keep = set(open(a.ids).read().split())
        ids = [i for i in ids if i in keep]
    catalog = json.load(open(root / a.split / f"{a.split}_tools_catalog.json", encoding="utf-8"))
    fz = fuzzy_keys(catalog)
    kind = {t["name"]: t["kind"] for ap_ in catalog["apps"] for t in ap_["tools"]}
    gh = gold_hashes(a.split, root, [rows[i] for i in ids])

    cats = collections.defaultdict(list)
    lost = collections.Counter()
    total = 0.0
    tool_err = collections.Counter()
    for sid in ids:
        r, p = rows[sid], preds[sid]
        g, pc = r["label"]["tool_calls"], p["tool_calls"]
        s, info = sample_score(pc, g, p["state_hash"], gh[sid], fz)
        total += s
        if s == 1.0:
            continue
        gw = [c for c in g if kind.get(c["name"]) == "write"]
        pw = [c for c in pc if kind.get(c["name"]) == "write"]
        g_ask = any(c["name"] == "sys.ask_missing_info" for c in g)
        p_ask = any(c["name"] == "sys.ask_missing_info" for c in pc)
        if not g:
            c = "acted_on_out_of_scope"
        elif not pc:
            c = "no_call_but_gold_acts"
        elif p["state_hash"] != gh[sid]:
            mw = max_matching(pw, gw, fz)
            if len(pw) < len(gw) and mw == len(pw):
                c = "state:missing_write"
            elif len(pw) > len(gw) and mw == len(gw):
                c = "state:extra_write"
            else:
                c = "state:wrong_write_args"
                names_g = collections.Counter(x["name"] for x in gw)
                for x in pw:
                    if x["name"] in names_g:
                        tool_err[x["name"]] += 1
        elif g_ask != p_ask:
            c = "ask:missing" if g_ask else "ask:spurious"
        elif info["U"] > 0 and info["M"] < info["G"]:
            c = "f1:extra_and_missing_calls"
        elif info["U"] > 0:
            c = "f1:extra_calls"
        else:
            c = "f1:missing_calls"
        cats[c].append(sid)
        lost[c] += 1.0 - s
    n = len(ids)
    print(f"samples {n}  score {100 * total / n:.2f}   (points lost per category, out of 100)")
    for c, v in sorted(lost.items(), key=lambda kv: -kv[1]):
        print(f"  {c:28s} n={len(cats[c]):4d}  lost={100 * v / n:5.2f}")
    if tool_err:
        print("tools with wrong write args:", tool_err.most_common(10))
    for c, sids in cats.items():
        print(f"\n== {c}")
        for sid in sids[: a.show]:
            r = rows[sid]
            print(f"- {sid}: {r.get('audio_text', '')[:120]}")
            print(f"    gold: {json.dumps(r['label']['tool_calls'], ensure_ascii=False)[:300]}")
            print(f"    pred: {json.dumps(preds[sid]['tool_calls'], ensure_ascii=False)[:300]}")


if __name__ == "__main__":
    main()
