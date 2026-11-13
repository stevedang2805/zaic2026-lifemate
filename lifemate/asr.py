"""ASR for every user turn of a split (last request + history user turns) -> {audio_path: text}.

python -m lifemate.asr --root DATA --split train --ids splits/val_unseen.txt --model openai/whisper-large-v3-turbo --out asr.json
On train, also writes <out>.wer.txt: WER/CER against audio_text, and accuracy of spoken digit strings.

Greedy decoding (num_beams=1, no sampling) for reproducibility.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from pathlib import Path


def clips_of(item: dict) -> list[tuple[str, str | None]]:
    """(audio path relative to the split dir, gold text or None) for the last request and every history user turn."""
    out = [(item["audio"], item.get("audio_text"))]
    for h in item.get("history", []):
        if h.get("role") == "user" and h.get("audio"):
            out.append((h["audio"], h.get("audio_text")))
    return out


def norm_words(s: str) -> list[str]:
    s = unicodedata.normalize("NFC", s.lower())
    return re.findall(r"[^\W_]+", s)


def edit_distance(a: list, b: list) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, y in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y))
        prev = cur
    return prev[-1]


def load_wav(path: Path):
    import numpy as np
    import soundfile as sf
    wav, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    if sr != 16000:  # data is 16 kHz; resample defensively
        import librosa
        wav = librosa.resample(wav, orig_sr=sr, target_sr=16000)
    return np.ascontiguousarray(wav)


def build_pipe(model: str, dtype: str, batch: int):
    import torch
    from transformers import pipeline
    return pipeline("automatic-speech-recognition", model=model, dtype=getattr(torch, dtype),
                    device=0 if torch.cuda.is_available() else -1, chunk_length_s=30, batch_size=batch)


HALLUC_RE = re.compile(r"subscribe|ghiền mì gõ|theo dõi và hẹn gặp lại|hẹn gặp lại các bạn|đăng ký kênh|video hấp dẫn", re.I)


def looks_bad(text: str) -> bool:
    """Whisper failure modes seen on this data: YouTube-outro hallucinations, word loops and character loops
    ("...RONXXXXXXXXXX..." on one val clip)."""
    if HALLUC_RE.search(text):
        return True
    if re.search(r"(.)\1{14,}", text) or re.search(r"(.{2,12}?)\1{6,}", text):
        return True
    w = text.split()
    return len(w) >= 8 and max(w.count(x) for x in set(w)) / len(w) > 0.5


def transcribe_all(pipe, wavs: list, beams: int = 1) -> list[str]:
    kw = {"num_beams": beams, "do_sample": False}  # beam search vẫn tất định (không sampling)
    try:
        out = pipe([{"raw": w, "sampling_rate": 16000} for w in wavs],
                   generate_kwargs={**kw, "language": "vi", "task": "transcribe"})
    except (ValueError, TypeError) as e:  # some fine-tuned Whisper configs reject language/task
        print("language/task not accepted, retrying without:", e)
        out = pipe([{"raw": w, "sampling_rate": 16000} for w in wavs], generate_kwargs=kw)
    texts = [o["text"].strip() for o in out]
    # re-decode suspicious outputs with beam search + n-gram blocking (still deterministic); give up -> empty text
    for i, t in enumerate(texts):
        if looks_bad(t):
            try:
                t2 = pipe({"raw": wavs[i], "sampling_rate": 16000},
                          generate_kwargs={"num_beams": 4, "no_repeat_ngram_size": 3, "do_sample": False,
                                           "language": "vi", "task": "transcribe"})["text"].strip()
            except (ValueError, TypeError):
                t2 = ""
            texts[i] = "" if looks_bad(t2) else t2
    return texts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data")
    ap.add_argument("--split", default="train")
    ap.add_argument("--ids")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--dtype", default="float16")
    ap.add_argument("--beams", type=int, default=1, help="num_beams khi giải mã (1 = greedy như các bản trước)")
    a = ap.parse_args()
    root = Path(a.root)
    items = [json.loads(l) for l in open(root / a.split / f"{a.split}.jsonl", encoding="utf-8") if l.strip()]
    if a.ids:
        keep = set(open(a.ids).read().split())
        items = [it for it in items if it["id"] in keep]
    clips, gold = [], {}
    for it in items:
        for p, g in clips_of(it):
            if p not in gold:
                clips.append(p)
                gold[p] = g
    print(f"{len(items)} samples, {len(clips)} clips", flush=True)
    pipe = build_pipe(a.model, a.dtype, a.batch)
    res, t0, chunk = {}, time.time(), 256
    for i in range(0, len(clips), chunk):
        part = clips[i: i + chunk]
        texts = transcribe_all(pipe, [load_wav(root / a.split / p) for p in part], beams=a.beams)
        res.update(zip(part, texts))
        print(f"  {min(i + chunk, len(clips))}/{len(clips)}  {time.time() - t0:.0f}s", flush=True)
    sec = time.time() - t0
    json.dump(res, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    lines = [f"model={a.model} clips={len(clips)} seconds={sec:.0f} ({sec / max(1, len(clips)):.3f}s/clip, batch {a.batch})"]
    pairs = [(gold[p], res[p]) for p in clips if gold.get(p)]
    if pairs:
        we = sum(edit_distance(norm_words(g), norm_words(h)) for g, h in pairs)
        wn = sum(len(norm_words(g)) for g, _ in pairs)
        ce = sum(edit_distance(list("".join(norm_words(g))), list("".join(norm_words(h)))) for g, h in pairs)
        cn = sum(len("".join(norm_words(g))) for g, _ in pairs)
        from .textnorm import spoken_digit_runs
        dig_ok = dig_n = 0
        for g, h in pairs:
            for run in spoken_digit_runs(g):
                dig_n += 1
                hyp = re.sub(r"\D", "", h)
                dig_ok += run in hyp or run in spoken_digit_runs(h)
        lines.append(f"WER={100 * we / wn:.2f}% CER={100 * ce / cn:.2f}% (n={len(pairs)} clips, raw text, digits not normalised)")
        lines.append(f"spoken digit strings recovered exactly: {dig_ok}/{dig_n}")
        worst = sorted(pairs, key=lambda gh: -edit_distance(norm_words(gh[0]), norm_words(gh[1])) / max(1, len(norm_words(gh[0]))))[:15]
        lines.append("worst clips:")
        lines += [f"  GOLD: {g}\n  ASR : {h}" for g, h in worst]
    Path(a.out + ".wer.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:3]))


if __name__ == "__main__":
    main()
