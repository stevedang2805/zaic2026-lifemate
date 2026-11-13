"""Run the agent on a split and write submission.jsonl (+ traces for debugging).

  # GPU dev run on train with gold transcripts (upper bound of the LLM part), held-out-app validation subset:
  python -m lifemate.run --root data --split train --ids splits/val_unseen.txt --backend vllm \
         --model Qwen/Qwen3-4B-Instruct-2507 --transcripts gold --out runs/qwen4b_val_unseen --batch 32
  python scripts/score.py --root data --split train --pred runs/qwen4b_val_unseen/submission.jsonl --by-tag

  # sanity check without GPU (must print score 100.00):
  python -m lifemate.run --root data --split train --backend oracle --transcripts gold --out runs/oracle

  # public test with ASR transcripts produced earlier ({"audio/public_0001/public_0001.wav": "text", ...}):
  python -m lifemate.run --root data --split public_test --backend vllm --model ... --transcripts asr.json --out runs/pub

--batch > 1 batches LLM calls across samples (fast dev loop). The final Docker run should use --batch 1:
batched kernels can change greedy outputs slightly, and the rules ask for reproducible results.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .agent import run_agent
from .backends import make_backend, set_seeds


def load_catalog_tools(root: Path, split: str) -> dict:
    cat = json.load(open(root / split / f"{split}_tools_catalog.json", encoding="utf-8"))
    return {t["name"]: t for a in cat["apps"] for t in a["tools"]}


def make_transcriber(mode: str, item_lookup: dict):
    """gold: audio_text from train labels. Otherwise a JSON file {audio_path: text}."""
    if mode == "gold":
        def tr(path, hist_turn, _items=item_lookup):
            if hist_turn is not None:
                return hist_turn.get("audio_text", "")
            return _items[path].get("audio_text", "")
        return tr
    table = json.load(open(mode, encoding="utf-8"))

    def tr(path, hist_turn):
        return table.get(path, "")
    return tr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--split", default="train")
    ap.add_argument("--ids", help="file with one sample id per line (subset)")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--backend", default="oracle", choices=["oracle", "vllm", "hf"])
    ap.add_argument("--model")
    ap.add_argument("--transcripts", default="gold")
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--max-new-tokens", type=int, default=384)
    ap.add_argument("--dtype", default="bfloat16", help="float16 on T4/V100 (no bf16)")
    ap.add_argument("--gpu-mem", type=float, default=0.85)
    ap.add_argument("--max-model-len", type=int, default=16384)
    ap.add_argument("--priors", help="json from lifemate.priors (per-tool argument priors)")
    ap.add_argument("--no-nudge", action="store_true")
    ap.add_argument("--time-budget", type=float, default=24.0, help="per-sample seconds; only enforced with --batch 1")
    ap.add_argument("--oracle-mistakes", action="store_true", help="oracle injects bad first calls (tests guards)")
    a = ap.parse_args()

    set_seeds(0)
    root = Path(a.root).resolve()
    sys.path.insert(0, str(root / a.split))
    from zaic_tools import ToolEnv  # noqa: E402  (the split's own package)

    items = [json.loads(l) for l in open(root / a.split / f"{a.split}.jsonl", encoding="utf-8") if l.strip()]
    if a.ids:
        keep = {l.strip() for l in open(a.ids) if l.strip()}
        items = [it for it in items if it["id"] in keep]
    if a.limit:
        items = items[: a.limit]
    catalog_tools = load_catalog_tools(root, a.split)
    priors = json.load(open(a.priors, encoding="utf-8")) if a.priors else None
    transcribe = make_transcriber(a.transcripts, {it["audio"]: it for it in items})

    kw = {}
    if a.backend in ("vllm", "hf"):
        kw.update(max_new_tokens=a.max_new_tokens, dtype=a.dtype, max_model_len=a.max_model_len)
    if a.backend == "vllm":
        kw["gpu_mem"] = a.gpu_mem
    if a.backend == "oracle":
        kw["mistakes"] = a.oracle_mistakes
    backend = make_backend(a.backend, a.model, rows={it["id"]: it for it in items}, **kw)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fsub = open(out / "submission.jsonl", "w", encoding="utf-8")
    ftr = open(out / "traces.jsonl", "w", encoding="utf-8")
    t_all = time.time()
    n_done = 0
    for b in range(0, len(items), a.batch):
        chunk = items[b: b + a.batch]
        envs = {it["id"]: ToolEnv(a.split, it["id"], root=root) for it in chunk}  # exactly one env per sample
        gens, pending, traces = {}, {}, {}
        for it in chunk:
            # with --batch > 1 a sample also waits for the others of its batch, so its wall time means nothing
            g = run_agent(it, envs[it["id"]], catalog_tools, transcribe,
                          time_budget=a.time_budget if a.batch == 1 else float("inf"),
                          priors=priors, nudge=not a.no_nudge)
            gens[it["id"]] = g
            try:
                pending[it["id"]] = next(g)
            except StopIteration as e:
                traces[it["id"]] = e.value
        while pending:
            sids = list(pending)
            outs = backend.generate_batch([pending[s] for s in sids], sids)
            for sid, text in zip(sids, outs):
                try:
                    pending[sid] = gens[sid].send(text)
                except StopIteration as e:
                    traces[sid] = e.value
                    del pending[sid]
        for it in chunk:  # keep input order
            env = envs[it["id"]]
            fsub.write(json.dumps({"id": it["id"], "tool_calls": env.get_tool_calls(), "state_hash": env.get_state_hash()},
                                  ensure_ascii=False) + "\n")
            ftr.write(json.dumps(traces.get(it["id"], {}), ensure_ascii=False) + "\n")
        n_done += len(chunk)
        fsub.flush(); ftr.flush()
        print(f"{n_done}/{len(items)}  {time.time() - t_all:.1f}s", file=sys.stderr, flush=True)
    print(f"wrote {out / 'submission.jsonl'} ({n_done} lines) in {time.time() - t_all:.1f}s")


if __name__ == "__main__":
    main()
