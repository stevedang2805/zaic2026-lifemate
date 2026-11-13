"""Local scorer for ZAIC 2026 LifeMate — reimplements the organisers' formula.

Usage (from the folder that holds train/ or public_test/):
    python score.py --split train --pred submission.jsonl [--root .] [--no-hash] [--by-tag]

Gold:
  * tool_calls  = label.tool_calls from <split>.jsonl
  * state_hash  = replay label.tool_calls with the split's zaic_tools on <split>_environment/<id>/state.json
                  (needs the environment folder; pass --no-hash to score F1 only = the organisers' tie-break metric)

Per sample (from the rules):
  gold == []            -> 1 if pred == [] else 0
  hash_pred != hash_gold or M == 0 -> 0
  else F1 with P = M / (M + U), R = M / |G|   (U = unmatched submitted calls, rejected calls included)
A submitted call matches a gold call when: same name, every non-fuzzy argument identical, every fuzzy argument
(x-match: fuzzy in the catalog) has token-F1 > 0.6 after lowercase + Unicode NFC. Each call matches at most one call,
order ignored -> maximum bipartite matching.

Assumptions (not fully specified by the organisers, check against the leaderboard):
  * "identical" non-fuzzy args = exact JSON equality, and the argument KEY SETS must be equal
    (an extra optional argument -> no match). Toggle with --lenient-keys.
  * fuzzy tokens = whitespace split after lower + NFC (punctuation kept attached to tokens).
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import unicodedata
from pathlib import Path


def norm_tokens(s) -> list[str]:
    return unicodedata.normalize("NFC", str(s).lower()).split()


def token_f1(a, b) -> float:
    ta, tb = norm_tokens(a), norm_tokens(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    common = sum((collections.Counter(ta) & collections.Counter(tb)).values())
    if common == 0:
        return 0.0
    p, r = common / len(ta), common / len(tb)
    return 2 * p * r / (p + r)


def fuzzy_keys(catalog: dict) -> dict[str, set[str]]:
    out = {}
    for app in catalog["apps"]:
        for t in app["tools"]:
            props = (t.get("parameters") or {}).get("properties") or {}
            out[t["name"]] = {k for k, p in props.items() if p.get("x-match") == "fuzzy"}
    return out


def call_match(pred: dict, gold: dict, fz: dict[str, set[str]], lenient_keys=False) -> bool:
    if pred.get("name") != gold.get("name"):
        return False
    pa, ga = pred.get("arguments") or {}, gold.get("arguments") or {}
    fk = fz.get(gold["name"], set())
    keys = set(ga) | (set() if lenient_keys else set(pa))
    for k in keys:
        if k not in pa or k not in ga:
            return False
        if k in fk:
            if token_f1(pa[k], ga[k]) <= 0.6:
                return False
        elif pa[k] != ga[k] or type(pa[k]) is not type(ga[k]):
            return False
    return True


def max_matching(pred: list, gold: list, fz, lenient_keys=False) -> int:
    """Maximum bipartite matching (Kuhn), so the count does not depend on order."""
    adj = [[j for j, g in enumerate(gold) if call_match(p, g, fz, lenient_keys)] for p in pred]
    match_g = [-1] * len(gold)

    def try_(i, seen):
        for j in adj[i]:
            if j in seen:
                continue
            seen.add(j)
            if match_g[j] == -1 or try_(match_g[j], seen):
                match_g[j] = i
                return True
        return False

    return sum(try_(i, set()) for i in range(len(pred)))


def sample_score(pred_calls, gold_calls, pred_hash, gold_hash, fz, check_hash=True, lenient_keys=False):
    if not gold_calls:
        return (1.0 if not pred_calls else 0.0), {"M": 0, "U": len(pred_calls), "G": 0}
    m = max_matching(pred_calls, gold_calls, fz, lenient_keys)
    u = len(pred_calls) - m
    info = {"M": m, "U": u, "G": len(gold_calls), "hash_ok": (pred_hash == gold_hash) if check_hash else None}
    if m == 0 or (check_hash and pred_hash != gold_hash):
        return 0.0, info
    p, r = m / (m + u), m / len(gold_calls)
    return 2 * p * r / (p + r), info


def gold_hashes(split: str, root: Path, rows: list[dict]) -> dict[str, str]:
    sys.path.insert(0, str(root / split))
    from zaic_tools import ToolEnv  # noqa: E402
    out = {}
    for r in rows:
        env = ToolEnv(split, r["id"], root=root)
        for c in r["label"]["tool_calls"]:
            env.call(c["name"], c.get("arguments") or {})
        out[r["id"]] = env.get_state_hash()
    return out


def tag(r: dict) -> str:
    calls = r["label"]["tool_calls"]
    if not calls:
        return "out_of_scope"
    if any(c["name"] == "sys.ask_missing_info" for c in calls):
        return "ask_missing"
    return "act"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="train")
    ap.add_argument("--root", default=".")
    ap.add_argument("--pred", required=True)
    ap.add_argument("--no-hash", action="store_true", help="skip state check (F1 only, the tie-break metric)")
    ap.add_argument("--lenient-keys", action="store_true", help="ignore extra optional args in the prediction")
    ap.add_argument("--by-tag", action="store_true")
    ap.add_argument("--dump", help="write per-sample scores to this jsonl")
    a = ap.parse_args()
    root = Path(a.root)
    rows = {json.loads(l)["id"]: json.loads(l) for l in open(root / a.split / f"{a.split}.jsonl", encoding="utf-8") if l.strip()}
    preds = {json.loads(l)["id"]: json.loads(l) for l in open(a.pred, encoding="utf-8") if l.strip()}
    rows = {k: v for k, v in rows.items() if k in preds}  # score only predicted ids (handy for subsets)
    fz = fuzzy_keys(json.load(open(root / a.split / f"{a.split}_tools_catalog.json", encoding="utf-8")))
    gh = {} if a.no_hash else gold_hashes(a.split, root, list(rows.values()))
    tot, by = [], collections.defaultdict(list)
    dump = open(a.dump, "w", encoding="utf-8") if a.dump else None
    for sid, r in rows.items():
        p = preds[sid]
        s, info = sample_score(p.get("tool_calls") or [], r["label"]["tool_calls"], p.get("state_hash"), gh.get(sid),
                               fz, check_hash=not a.no_hash, lenient_keys=a.lenient_keys)
        tot.append(s)
        by[tag(r)].append(s)
        if dump:
            dump.write(json.dumps({"id": sid, "score": s, "tag": tag(r), **info}, ensure_ascii=False) + "\n")
    n = len(tot)
    print(f"samples {n}  score {100 * sum(tot) / max(n, 1):.2f}")
    if a.by_tag:
        for t, v in sorted(by.items()):
            print(f"  {t:13s} n={len(v):4d}  mean={100 * sum(v) / len(v):.2f}")


if __name__ == "__main__":
    main()
