"""Compare two inference runs (submission + trace written by lifemate.infer --trace) and say where they diverge.

  python3 scripts/detcheck.py runA runB

For each sample whose output differs, the cause is the first divergence:
  ASR   the Whisper transcripts differ
  LLM   same prompt (same hash), different model output -> nondeterminism inside vLLM
  PROMPT the prompts differ before any output differs (would mean the agent code itself is not deterministic)
Stdlib only, runs on the host.
"""
import json
import sys
from collections import Counter


def load(path):
    return {r["id"]: r for r in map(json.loads, open(path, encoding="utf-8"))}


def main(a, b):
    sa, sb = load(f"{a}/submission.jsonl"), load(f"{b}/submission.jsonl")
    ta, tb = load(f"{a}/trace.jsonl"), load(f"{b}/trace.jsonl")
    ids = [i for i in sa if i in sb]
    diff = [i for i in ids if sa[i] != sb[i]]
    asr_diff = [i for i in ids if ta[i]["asr"] != tb[i]["asr"]]
    llm_diff = [i for i in ids if ta[i]["llm"] != tb[i]["llm"]]
    cause = Counter()
    first = {}
    for i in llm_diff + [x for x in asr_diff if x not in llm_diff]:
        if ta[i]["asr"] != tb[i]["asr"]:
            cause["ASR"] += 1
            continue
        for k, ((ha, oa), (hb, ob)) in enumerate(zip(ta[i]["llm"], tb[i]["llm"])):
            if ha != hb:
                cause["PROMPT"] += 1
                break
            if oa != ob:
                cause["LLM"] += 1
                first.setdefault(i, (k, oa, ob))
                break
        else:
            cause["LENGTH"] += 1
    secs = [t["sec"] for t in ta.values()]
    print(f"{a} vs {b}: {len(ids)} samples | output differs {len(diff)} | ASR differs {len(asr_diff)} | "
          f"LLM steps differ {len(llm_diff)} | causes {dict(cause)} | run A mean {sum(secs) / len(secs):.2f}s "
          f"max {max(secs):.2f}s")
    for i, (k, oa, ob) in list(first.items())[:3]:
        print(f"  {i} step {k}:\n    A: {oa[:160]!r}\n    B: {ob[:160]!r}")
    return len(diff)


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1], sys.argv[2]) else 0)
