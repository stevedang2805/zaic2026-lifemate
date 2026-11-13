#!/usr/bin/env bash
# Build the submission image and run the organisers' checks on public_test.
#
#   bash docker/build_and_test.sh /path/to/data/public_test
#
# Expects, next to this repo:  models/llm/  (merged LLM)   models/asr/  (fine-tuned Whisper)
set -euo pipefail

SPLIT_DIR="${1:?usage: build_and_test.sh /path/to/public_test}"
IMAGE="${IMAGE:-zaic-lifemate}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

for d in models/llm models/asr lifemate; do
  [ -d "$d" ] || { echo "MISSING $HERE/$d"; exit 1; }
done
SPLIT_DIR="$(cd "$SPLIT_DIR" && pwd)"
SPLIT="$(basename "$SPLIT_DIR")"
N_EXPECTED=$(wc -l < "$SPLIT_DIR/$SPLIT.jsonl")

echo "== build"
docker build -f docker/Dockerfile -t "$IMAGE" .

run_once () {  # $1 = output dir
  rm -rf "$1"; mkdir -p "$1"
  docker run --rm --gpus all --network none \
    -v "$SPLIT_DIR:/data:ro" -v "$HERE/$1:/app/result" "$IMAGE" 2>&1 | tail -20
}

echo "== run 1 (offline, no network)"
time run_once result1
N=$(wc -l < result1/submission.jsonl)
echo "lines: $N (expected $N_EXPECTED)"
[ "$N" = "$N_EXPECTED" ] || { echo "FAIL: wrong number of lines"; exit 1; }

echo "== schema check with the organisers' tool"
( cd "$SPLIT_DIR" && python3 -m zaic_tools --split "$SPLIT" --root .. --validate "$HERE/result1/submission.jsonl" )

echo "== run 2 (reproducibility)"
run_once result2
if diff -q result1/submission.jsonl result2/submission.jsonl >/dev/null; then
  echo "PASS: identical across runs"
else
  echo "FAIL: runs differ — check greedy decoding / seeds / batching"
  diff <(head -5 result1/submission.jsonl) <(head -5 result2/submission.jsonl) | head
  exit 1
fi

echo
echo "Submit result1/submission.jsonl to the leaderboard; the score must match the Colab run."
echo "Then: docker save $IMAGE | gzip > zaic.tar.gz && sha256sum zaic.tar.gz"
