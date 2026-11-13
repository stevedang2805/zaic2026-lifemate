# ZAIC 2026 LifeMate — offline inference image.
# Build context must contain: lifemate/, models/llm/, models/asr/
#   docker build -f docker/Dockerfile -t zaic-lifemate .
# Run exactly as the organisers do:
#   docker run --rm --gpus all --network none -v /path/to/private_test:/data -v $PWD/result:/app/result zaic-lifemate
# Must match the vLLM that produced the Colab results (see results_*/versions.txt): v0.33.0.
# Check the tag exists first:  docker pull vllm/vllm-openai:v0.33.0
# If it does not, use the newest tag available and re-run the leaderboard check below.
FROM vllm/vllm-openai:v0.33.0

WORKDIR /app
# vllm/* images ship torch + vllm + CUDA; we only add what the agent needs.
# torchao that Colab/base images ship can be too old for peft; we do not use it.
RUN pip install --no-cache-dir soundfile librosa && (pip uninstall -y torchao || true)

# models first: editing the code then only rebuilds the last small layer
COPY models/llm /app/models/llm
COPY models/asr /app/models/asr
COPY lifemate /app/lifemate

# Fully offline + deterministic
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_DATASETS_OFFLINE=1 \
    VLLM_NO_USAGE_STATS=1 \
    DO_NOT_TRACK=1 \
    PYTHONHASHSEED=0 \
    TOKENIZERS_PARALLELISM=false \
    CUBLAS_WORKSPACE_CONFIG=:4096:8

# the base image has its own entrypoint (the API server) — clear it
ENTRYPOINT []
CMD ["python3", "-m", "lifemate.infer", \
     "--data", "/data", \
     "--asr", "/app/models/asr", \
     "--llm", "/app/models/llm", \
     "--out", "/app/result/submission.jsonl"]
