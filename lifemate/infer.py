"""Final inference entry point (Docker): ASR + agent, one sample at a time, fully offline.

  python -m lifemate.infer --data /data --asr /models/asr --llm /models/llm --out result/submission.jsonl

--data is either the split folder itself (/data/private_test.jsonl, /data/private_test_environment/, /data/zaic_tools/...)
or a folder containing it (/data/private_test/...). The split name is taken from the *_tools_catalog.json file.

Rules respected: one ToolEnv per sample, only validate/call/get_tool_calls/get_state_hash, no state.json access,
greedy decoding + fixed seeds, batch 1 (reproducible), per-sample time budget. A sample that crashes still gets a line
(the calls already made and the hash), so the file always has exactly one line per sample.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path


def find_split(data: Path) -> tuple[Path, str]:
    """-> (root, split) such that root/split/split.jsonl exists (symlinking when /data is the split folder)."""
    for cat in list(data.glob("*_tools_catalog.json")) + list(data.glob("*/*_tools_catalog.json")):
        split = cat.name[: -len("_tools_catalog.json")]
        folder = cat.parent
        if (folder / f"{split}.jsonl").exists():
            if folder.name == split:
                return folder.parent, split
            tmp = Path(tempfile.mkdtemp(prefix="zaic_root_"))
            (tmp / split).symlink_to(folder.resolve(), target_is_directory=True)
            return tmp, split
    raise FileNotFoundError(f"no <split>_tools_catalog.json + <split>.jsonl under {data}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/data")
    ap.add_argument("--asr", required=True)
    ap.add_argument("--llm", required=True)
    ap.add_argument("--out", default="result/submission.jsonl")
    ap.add_argument("--backend", default="vllm", choices=["vllm", "hf"])
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--asr-dtype", default="float16")
    ap.add_argument("--asr-beams", type=int, default=1, help="num_beams của Whisper (1 = greedy)")
    ap.add_argument("--gpu-mem", type=float, default=0.70, help="vLLM share of GPU memory; the rest holds Whisper")
    ap.add_argument("--time-budget", type=float, default=24.0, help="seconds per sample for the agent loop")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--eager", action="store_true", help="vLLM enforce_eager: no torch.compile / CUDA graphs")
    ap.add_argument("--no-prefix-cache", action="store_true")
    # No torch.compile: Inductor picks some kernels by timing them at start-up, so 1 run in 4 took a different numeric
    # path and 49/634 outputs changed (vLLM 0.33, RTX 4090). Without compilation there is nothing to pick; full CUDA
    # graphs keep decoding fast (200 public samples: mean 2.40s, max 13.0s vs 1.98s / 12.2s compiled).
    ap.add_argument("--vllm-kw", default='{"compilation_config": {"mode": 0, "cudagraph_mode": "FULL"}}',
                    help="extra vllm.LLM kwargs as JSON; '{}' = vLLM defaults (torch.compile on)")
    ap.add_argument("--det-torch", action="store_true", help="torch.use_deterministic_algorithms for Whisper")
    ap.add_argument("--trace", help="jsonl: per sample the ASR texts and every LLM (prompt hash, output) — "
                                    "for finding where two runs diverge")
    a = ap.parse_args()

    from .backends import make_backend, set_seeds
    set_seeds(0)
    if a.det_torch:
        import torch
        torch.use_deterministic_algorithms(True, warn_only=True)
    root, split = find_split(Path(a.data))
    sys.path.insert(0, str(root / split))
    from zaic_tools import ToolEnv  # noqa: E402  (the split's own package)

    from .agent import run_agent
    from .asr import build_pipe, clips_of, load_wav, transcribe_all
    from .run import load_catalog_tools

    items = [json.loads(l) for l in open(root / split / f"{split}.jsonl", encoding="utf-8") if l.strip()]
    if a.limit:
        items = items[: a.limit]
    catalog_tools = load_catalog_tools(root, split)
    t_load = time.time()
    pipe = build_pipe(a.asr, a.asr_dtype, batch=8)
    kw = {"max_new_tokens": 384, "dtype": a.dtype, "max_model_len": 16384}
    if a.backend == "vllm":
        kw["gpu_mem"] = a.gpu_mem
        kw["prefix_caching"] = not a.no_prefix_cache
        if a.eager:
            kw["enforce_eager"] = True
        kw.update(json.loads(a.vllm_kw))
    llm = make_backend(a.backend, a.llm, **kw)
    print(f"[infer] split={split} samples={len(items)} models loaded in {time.time() - t_load:.0f}s", flush=True)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    times = []
    ftrace = open(a.trace, "w", encoding="utf-8") if a.trace else None
    with open(out, "w", encoding="utf-8") as fout:
        for k, it in enumerate(items):
            t0 = time.time()
            tr = {"id": it["id"], "asr": [], "llm": []}
            env = ToolEnv(split, it["id"], root=root)  # exactly one env per sample
            try:
                clips = clips_of(it)
                texts = transcribe_all(pipe, [load_wav(root / split / p) for p, _ in clips], beams=a.asr_beams)
                table = {p: t for (p, _), t in zip(clips, texts)}
                tr["asr"] = texts

                def transcribe(path, _h, _t=table):
                    return _t.get(path, "")

                remaining = a.time_budget - (time.time() - t0)
                g = run_agent(it, env, catalog_tools, transcribe, time_budget=max(1.0, remaining))
                try:
                    prompt = next(g)
                    while True:
                        reply = llm.generate_batch([prompt], [it["id"]])[0]
                        if ftrace:
                            h = hashlib.sha1(json.dumps(prompt, ensure_ascii=False, sort_keys=True, default=str)
                                             .encode()).hexdigest()[:12]
                            tr["llm"].append([h, reply])
                        prompt = g.send(reply)
                except StopIteration:
                    pass
            except Exception:  # never lose the line of a sample
                traceback.print_exc()
            fout.write(json.dumps({"id": it["id"], "tool_calls": env.get_tool_calls(), "state_hash": env.get_state_hash()},
                                  ensure_ascii=False) + "\n")
            fout.flush()
            times.append(time.time() - t0)
            if ftrace:
                tr["sec"] = round(times[-1], 2)
                ftrace.write(json.dumps(tr, ensure_ascii=False) + "\n")
                ftrace.flush()
            if (k + 1) % 20 == 0 or k + 1 == len(items):
                print(f"[infer] {k + 1}/{len(items)} mean {sum(times) / len(times):.2f}s max {max(times):.2f}s", flush=True)
    if ftrace:
        ftrace.close()
    print(f"[infer] wrote {out} ({len(items)} lines)")


if __name__ == "__main__":
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    main()
