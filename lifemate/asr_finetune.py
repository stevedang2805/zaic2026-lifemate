"""Fine-tune Whisper on the train split's audio (every user turn has a gold transcript: 5036 clips).

Base whisper-large-v3-turbo on val clips: WER 34.6%, ~2% hallucinated sentences ("Hãy subscribe cho kênh ..."),
names and Central/Southern speech often wrong -> end-to-end score halves (val_unseen 49.0 gold text -> 25.3 ASR).

python -m lifemate.asr_finetune --root DATA --exclude splits/val_all.txt --model openai/whisper-large-v3-turbo \
       --out /content/asr_ft --epochs 3
Clips of samples listed in --exclude are held out (for WER / end-to-end evaluation).
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

from .asr import clips_of, load_wav


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data")
    ap.add_argument("--model", default="openai/whisper-large-v3-turbo")
    ap.add_argument("--exclude", help="ids whose clips are held out")
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--grad-accum", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    import numpy as np
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor

    random.seed(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)
    root = Path(a.root)
    items = [json.loads(l) for l in open(root / "train/train.jsonl", encoding="utf-8")]
    excl = set(open(a.exclude).read().split()) if a.exclude else set()
    pairs, seen = [], set()
    for it in items:
        if it["id"] in excl:
            continue
        for p, g in clips_of(it):
            if g and p not in seen:
                seen.add(p)
                pairs.append((root / "train" / p, g.strip()))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    log = open(out / "asr_train_log.txt", "a")

    def say(s):
        print(s, flush=True)
        log.write(s + "\n")
        log.flush()

    say(f"train clips {len(pairs)} (held-out samples {len(excl)})")

    proc = WhisperProcessor.from_pretrained(a.model)
    proc.tokenizer.set_prefix_tokens(language="vietnamese", task="transcribe", predict_timestamps=False)
    dev = "cuda" if torch.cuda.is_available() else "cpu"  # cpu only for the plumbing test
    model = WhisperForConditionalGeneration.from_pretrained(a.model, dtype=torch.float32).to(dev)
    model.config.apply_spec_augment = True     # SpecAugment (time/feature masking) as regulariser
    model.config.mask_time_prob = 0.05
    model.config.mask_feature_prob = 0.05
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    sot = model.config.decoder_start_token_id

    wav_cache = {}

    def feats_labels(batch):
        wavs = []
        for p, _ in batch:
            if p not in wav_cache:
                wav_cache[p] = load_wav(p)
            w = wav_cache[p]
            g = 10 ** (random.uniform(-6, 6) / 20)  # random gain +-6 dB
            wavs.append(np.clip(w * g, -1, 1))
        x = proc.feature_extractor(wavs, sampling_rate=16000, return_tensors="pt").input_features
        lab = [proc.tokenizer(t).input_ids for _, t in batch]
        lab = [l[1:] if l and l[0] == sot else l for l in lab]  # model prepends decoder_start itself
        n = max(len(l) for l in lab)
        y = torch.full((len(lab), n), -100, dtype=torch.long)
        for i, l in enumerate(lab):
            y[i, : len(l)] = torch.tensor(l)
        return x, y

    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    steps_per_epoch = math.ceil(len(pairs) / (a.batch * a.grad_accum))
    total = int(steps_per_epoch * a.epochs)
    warm = max(1, int(0.05 * total))

    def lr_at(s):  # linear warmup, then linear decay to 0
        if s < warm:
            return a.lr * (s + 1) / warm
        return a.lr * max(0.0, (total - s) / max(1, total - warm))

    model.train()
    t0, step, micro, run = time.time(), 0, 0, []
    order = []
    while len(order) < total * a.batch * a.grad_accum:
        o = list(range(len(pairs)))
        random.shuffle(o)
        order += o
    for b in range(0, total * a.batch * a.grad_accum, a.batch):
        batch = [pairs[i] for i in order[b: b + a.batch]]
        x, y = feats_labels(batch)
        with torch.autocast(dev, dtype=torch.bfloat16):
            loss = model(input_features=x.to(dev), labels=y.to(dev)).loss / a.grad_accum
        loss.backward()
        run.append(loss.item() * a.grad_accum)
        micro += 1
        if micro % a.grad_accum == 0:
            for g in opt.param_groups:
                g["lr"] = lr_at(step)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            opt.zero_grad(set_to_none=True)
            step += 1
            if step % 25 == 0 or step == total:
                el = time.time() - t0
                say(f"step {step}/{total} loss {sum(run) / len(run):.4f} elapsed {el / 60:.1f}m eta {el / step * (total - step) / 60:.1f}m")
                run = []
            if step >= total:
                break
    model.config.use_cache = True
    model.config.apply_spec_augment = False
    model.generation_config.language = "vi"
    model.generation_config.task = "transcribe"
    model.half().save_pretrained(out, safe_serialization=True)  # fp16 weights: 1.6 GB instead of 3.2 GB
    proc.save_pretrained(out)
    say(f"saved -> {out} ({(time.time() - t0) / 60:.1f} min)")


if __name__ == "__main__":
    main()
