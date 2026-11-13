#!/usr/bin/env bash
# Find which setting makes two runs identical, without rebuilding the image (the current code is mounted over /app/lifemate).
#
#   bash docker/det_test.sh "$PUB" [N]        # N = number of samples per run (default 200)
#
# Each config runs twice on the first N public samples; scripts/detcheck.py reports how many outputs differ and
# whether the first divergence comes from Whisper (ASR) or from vLLM (LLM).
set -uo pipefail
SPLIT_DIR="$(cd "${1:?usage: det_test.sh /path/to/public_test [N]}" && pwd)"
N="${2:-200}"
IMAGE="${IMAGE:-zaic-lifemate}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

run () {  # $1 = out dir, $2.. = extra infer flags (and -e VAR=... before them is not supported: use EXTRA_ENV)
  local out="$1"; shift
  rm -rf "$out"; mkdir -p "$out"
  docker run --rm --gpus all --network none ${EXTRA_ENV:-} \
    -v "$SPLIT_DIR:/data:ro" -v "$HERE/$out:/app/result" -v "$HERE/lifemate:/app/lifemate:ro" "$IMAGE" \
    python3 -m lifemate.infer --data /data --asr /app/models/asr --llm /app/models/llm \
      --out /app/result/submission.jsonl --trace /app/result/trace.jsonl --limit "$N" "$@" 2>&1 \
    | grep -E "^\[infer\]|Error|error" | tail -3
}

config () {  # $1 = name, $2.. = flags
  local name="$1"; shift
  echo "== $name: $*"
  run "det/${name}_1" "$@"
  run "det/${name}_2" "$@"
  python3 scripts/detcheck.py "det/${name}_1" "det/${name}_2"
}

config base
config eager_nocache --eager --no-prefix-cache --det-torch
echo "done"
