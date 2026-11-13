"""Merge a LoRA adapter into its base model (for vLLM).

python -m lifemate.merge --base Qwen/Qwen3-4B-Instruct-2507 --adapter /content/drive/MyDrive/ZAIC/ft_fit_adapter --out /content/ft_fit/merged
"""
from __future__ import annotations

import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    base = AutoModelForCausalLM.from_pretrained(a.base, dtype=torch.bfloat16, device_map={"": dev})
    m = PeftModel.from_pretrained(base, a.adapter).merge_and_unload()
    m.save_pretrained(a.out, safe_serialization=True)
    AutoTokenizer.from_pretrained(a.base).save_pretrained(a.out)
    print("merged ->", a.out)


if __name__ == "__main__":
    main()
