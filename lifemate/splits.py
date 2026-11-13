"""Dev splits of train that mimic the test situation: public test has 11 apps never seen in train (65% of samples
install one), and private test will likely bring others. So the main validation set uses apps held out from training.

  val_unseen : samples whose gold uses a held-out app (zero-shot on a new schema) — the number to watch
  val_seen   : random ~10% of the other samples (also used for out-of-scope / ask balance)
  train_fit  : everything else, minus any sample that merely has a held-out app installed (its schema would leak)

python -m lifemate.splits --root data --out splits
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

# train-only apps (absent from public test, so holding them out costs nothing there), spread over app groups
HELD_OUT = ["learning", "door_lock", "loyalty", "package_tracking", "library", "appliances"]


def gold_apps(r: dict) -> set[str]:
    out = set()
    for c in r["label"]["tool_calls"]:
        if c["name"] == "sys.ask_missing_info":
            out.add(str(c["arguments"].get("tool_name", "")).split(".", 1)[0])
        else:
            out.add(c["name"].split(".", 1)[0])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data")
    ap.add_argument("--out", default="splits")
    ap.add_argument("--seen-frac", type=float, default=0.10)
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(Path(a.root) / "train/train.jsonl", encoding="utf-8")]
    held = set(HELD_OUT)
    unseen = [r["id"] for r in rows if gold_apps(r) & held]
    rest = [r for r in rows if r["id"] not in set(unseen)]
    rng = random.Random(0)
    seen = sorted(rng.sample([r["id"] for r in rest], int(a.seen_frac * len(rest))))
    fit = [r["id"] for r in rest if r["id"] not in set(seen) and not (set(r["context"]["installed_apps"]) & held)]
    leak = len(rest) - len(seen) - len(fit)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, ids in [("val_unseen", unseen), ("val_seen", seen), ("train_fit", fit)]:
        (out / f"{name}.txt").write_text("\n".join(ids) + "\n")
        print(f"{name:10s} {len(ids):5d}")
    print(f"dropped (held-out app installed but unused): {leak}")


if __name__ == "__main__":
    main()
