"""Real token counts of the first prompt of every sample, rendered with the model's chat template.

python -m lifemate.tokstats --root DATA --model Qwen/Qwen3-4B-Instruct-2507
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backends import _template_messages
from .prompt import build_messages, tools_for_sample
from .run import load_catalog_tools


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data")
    ap.add_argument("--model", required=True)
    a = ap.parse_args()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)
    root = Path(a.root)
    for split in ["train", "public_test"]:
        cat = load_catalog_tools(root, split)
        items = [json.loads(l) for l in open(root / split / f"{split}.jsonl", encoding="utf-8")]
        lens = []
        for it in items:
            # train: real transcripts; public: 80-char placeholder per user turn (ASR text is about that long)
            tr = (lambda p, h, it=it: (h or it).get("audio_text") or "x" * 80)
            text = tok.apply_chat_template(_template_messages(build_messages(it, tr)), tools=tools_for_sample(it, cat),
                                           tokenize=False, add_generation_prompt=True)
            lens.append(len(tok(text)["input_ids"]))
        lens.sort()
        n = len(lens)
        print(f"{split:12s} n={n} mean={sum(lens) // n} p50={lens[n // 2]} p95={lens[int(.95 * n)]} max={lens[-1]} "
              f">12k={sum(x > 12000 for x in lens)} >15k={sum(x > 15000 for x in lens)}")
    print("--- sample render (head) ---")
    print(text[:1500])


if __name__ == "__main__":
    main()
