#!/usr/bin/env bash
# One run per candidate setting on the first N public samples, each compared with det/base_1 (from det_test.sh):
# does it start, how fast is it, how many outputs change. Code is mounted, no rebuild.
#
#   bash docker/det_try.sh "$PUB" [N]
set -uo pipefail
SPLIT_DIR="$(cd "${1:?usage: det_try.sh /path/to/public_test [N]}" && pwd)"
N="${2:-200}"
IMAGE="${IMAGE:-zaic-lifemate}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

try () {  # $1 = name, $2 = docker env flags ("" for none), $3 = --vllm-kw JSON
  local name="$1" envs="$2" kw="$3" out="det/$1"
  echo "== $name  env[$envs]  vllm-kw $kw"
  rm -rf "$out"; mkdir -p "$out"
  docker run --rm --gpus all --network none $envs \
    -v "$SPLIT_DIR:/data:ro" -v "$HERE/$out:/app/result" -v "$HERE/lifemate:/app/lifemate:ro" "$IMAGE" \
    python3 -m lifemate.infer --data /data --asr /app/models/asr --llm /app/models/llm \
      --out /app/result/submission.jsonl --trace /app/result/trace.jsonl --limit "$N" --vllm-kw "$kw" \
    > "$out/log.txt" 2>&1
  grep -E "^\[infer\] (200|wrote|split)" "$out/log.txt" | tail -2
  if [ "$(wc -l < "$out/submission.jsonl" 2>/dev/null || echo 0)" = "$N" ] && [ -s "$out/trace.jsonl" ]; then
    python3 scripts/detcheck.py "$out" det/base_1 | head -1
  else
    echo "FAILED — last lines of $out/log.txt:"; grep -iE "error|exception" "$out/log.txt" | tail -5
  fi
}

DET='{"compilation_config": {"inductor_compile_config": {"deterministic": true}}}'
try inductor_det "" "$DET"
try nocompile_graph "" '{"compilation_config": {"mode": 0, "cudagraph_mode": "FULL"}}'
try batch_inv "-e VLLM_BATCH_INVARIANT=1" '{}'
try batch_inv_det "-e VLLM_BATCH_INVARIANT=1" "$DET"
echo done
