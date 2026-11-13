"""Argument priors learned from gold calls, plus generic rules for tools never seen in train.

Gold habits (train): optional args are rarely passed (alarm.create.label 1/78, banking.transfer.note 1/82, no
reminders/alarm `repeat` at all), but some are almost always passed (notes.create.title 30/32). List-type reads are
called with {} (smart_home.get_status 93/107, bill_payment.list_bills 112/112), others always filter
(gold_price.get_price.type 33/33). So: per-tool priors where train has evidence, generic rules elsewhere.

python -m lifemate.priors --root data --ids splits/train_fit.txt --out priors_fit.json   # for dev eval
python -m lifemate.priors --root data --out priors_all.json                              # for test
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import unicodedata
from pathlib import Path

MIN_N = 8            # evidence needed to trust a per-tool prior
DROP_OPT_BELOW = 0.10
STRIP_READ_ABOVE = 0.85
# optional enum values that mean "default" — gold never states them (once, normal, vacuum, cash, economy, general)
DEFAULT_VALUES = {"once", "normal", "vacuum", "cash", "economy", "general", "default", "standard", "auto", "none",
                  "medium", "any", "all"}
# optional free-text args that gold almost never fills (note 1/82, label 1/78, 2/33, 1/8, 0/6)
RARE_TEXT_ARGS = {"note", "label"}


def build(rows: list[dict], catalog_tools: dict) -> dict:
    opt_n, opt_used = collections.Counter(), collections.Counter()
    read_n, read_empty = collections.Counter(), collections.Counter()
    for r in rows:
        for c in r["label"]["tool_calls"]:
            t = catalog_tools.get(c["name"])
            if not t:
                continue
            p = t.get("parameters") or {}
            req = set(p.get("required") or []) | {k for g in (p.get("x-one-of") or []) for k in g}
            for k in (p.get("properties") or {}):
                if k not in req:
                    opt_n[f"{c['name']}|{k}"] += 1
                    opt_used[f"{c['name']}|{k}"] += k in c["arguments"]
            if t.get("kind") == "read" and not req:
                read_n[c["name"]] += 1
                read_empty[c["name"]] += not c["arguments"]
    return {"opt": {k: [opt_used[k], n] for k, n in opt_n.items()},
            "read_empty": {k: [read_empty[k], n] for k, n in read_n.items()}}


def _toks(s) -> set[str]:
    return set(re.findall(r"[^\W_]+", unicodedata.normalize("NFC", str(s).lower())))


def apply(name: str, args: dict, spec: dict, priors: dict | None, context: str) -> tuple[dict, list[str]]:
    """Returns (args, dropped_keys). context = text the user said (current + history) and tool results seen."""
    p = spec.get("parameters") or {}
    props = p.get("properties") or {}
    req = set(p.get("required") or []) | {k for g in (p.get("x-one-of") or []) for k in g}  # one-of members are required
    priors = priors or {}
    out, dropped = {}, []
    # list-type read: strip filters when gold almost always calls it bare
    re_ = priors.get("read_empty", {}).get(name)
    if spec.get("kind") == "read" and not req and re_ and re_[1] >= MIN_N and re_[0] / re_[1] >= STRIP_READ_ABOVE:
        return {}, list(args)
    ctx = _toks(context)
    for k, v in args.items():
        pr = props.get(k) or {}
        if k in req:
            out[k] = v
            continue
        fuzzy = pr.get("x-match") == "fuzzy"
        ev = priors.get("opt", {}).get(f"{name}|{k}")
        if ev and ev[1] >= MIN_N:
            # a rare optional arg is dropped by the prior only if it is free text (not in the state hash);
            # a state-changing arg (payment, seat_class...) is dropped only when it holds a default value
            if ev[0] / ev[1] < DROP_OPT_BELOW and (fuzzy or (isinstance(v, str) and v.lower() in DEFAULT_VALUES)):
                dropped.append(k)
                continue
            out[k] = v
            continue
        # generic rules (tool or arg unseen in train)
        if pr.get("enum") and isinstance(v, str) and v.lower() in DEFAULT_VALUES:
            dropped.append(k)
            continue
        if pr.get("x-match") == "fuzzy" and isinstance(v, str):
            vt = _toks(v)
            overlap = len(vt & ctx) / max(1, len(vt))
            if overlap < 0.5 or (k in RARE_TEXT_ARGS and overlap < 0.8):  # gold optional free text: overlap >= 0.5 always
                dropped.append(k)
                continue
        out[k] = v
    return out, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data")
    ap.add_argument("--ids")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    root = Path(a.root)
    rows = [json.loads(l) for l in open(root / "train/train.jsonl", encoding="utf-8")]
    if a.ids:
        keep = set(open(a.ids).read().split())
        rows = [r for r in rows if r["id"] in keep]
    cat = json.load(open(root / "train/train_tools_catalog.json", encoding="utf-8"))
    tools = {t["name"]: t for ap_ in cat["apps"] for t in ap_["tools"]}
    pri = build(rows, tools)
    json.dump(pri, open(a.out, "w"), ensure_ascii=False, indent=0)
    print(f"{a.out}: {len(pri['opt'])} optional-arg priors, {len(pri['read_empty'])} read priors from {len(rows)} samples")


if __name__ == "__main__":
    main()
