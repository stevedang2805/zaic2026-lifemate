# Việc B — Đóng gói Docker cho bài nộp cuối (hạn 16/11 23:59)

## Cần có
- Một máy Linux có GPU NVIDIA (từ 16GB), Docker và `nvidia-container-toolkit`. **Colab không chạy được Docker.** Nếu không có máy như vậy, báo ngay để tính phương án khác (máy lab trường, hoặc thuê VM có GPU vài giờ).
- **Tài liệu hướng dẫn Docker của BTC** trên portal: đọc kỹ đường dẫn mount (`/data`), chỗ ghi kết quả (`result/submission.jsonl`), lệnh chạy, và giới hạn kích thước image. Chỗ nào khác với file này thì làm theo BTC.

## Thành phần
- Code: thư mục `lifemate/` (entry point `python -m lifemate.infer`, đã test).
- Model, đặt sẵn trong image vì phải chạy **offline**:
  - LLM đã merge (khoảng 8GB), lấy từ Drive sau khi train xong vòng cuối.
  - ASR Whisper đã fine-tune (khoảng 1.6GB), lấy từ `MyDrive/ZAIC/asr_ft_v4` hoặc bản cuối.
  Trong lúc chờ bản cuối, dùng bản hiện có để dựng và test image.
- Phiên bản thư viện khớp với Colab: `vllm==0.33.0`, `torch==2.14.0`, `transformers==5.20.2`, `peft==0.21.2`, thêm `soundfile`.

## Dockerfile nháp
```dockerfile
FROM vllm/vllm-openai:v0.33.0          # có sẵn torch + vllm + CUDA; kiểm tra tag có tồn tại
WORKDIR /app
RUN pip install --no-cache-dir soundfile peft==0.21.2 && pip uninstall -y torchao || true
COPY lifemate /app/lifemate
COPY models/llm /app/models/llm
COPY models/asr /app/models/asr
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 VLLM_NO_USAGE_STATS=1 PYTHONHASHSEED=0
ENTRYPOINT []
CMD ["python", "-m", "lifemate.infer", "--data", "/data", "--asr", "/app/models/asr", "--llm", "/app/models/llm", "--out", "/app/result/submission.jsonl"]
```

## Kiểm tra trước khi nộp
1. **Chạy offline trên public_test** với lệnh giống BTC:
   ```bash
   docker run --rm --gpus all --network none -v /path/public_test:/data -v $PWD/result:/app/result <image>
   ```
   Phải ra `result/submission.jsonl` có **634 dòng**.
2. **Kiểm tra file:** `cd public_test && python -m zaic_tools --split public_test --root .. --validate ../result/submission.jsonl` phải báo 0 lỗi schema. Nộp file này lên leaderboard; điểm phải gần với điểm của bản nộp từ Colab.
3. **Tính tái lập:** chạy 2 lần, rồi `diff` hai file submission. Phải giống hệt nhau.
4. **Thời gian:** log in ra `mean`/`max` giây mỗi mẫu. Luật yêu cầu dưới 30 giây/mẫu trên A30, nên trên máy test cần `max` dưới khoảng 20 giây.
5. **Bộ nhớ GPU:** nếu vLLM báo thiếu bộ nhớ, giảm `--gpu-mem` (mặc định 0.70).
6. **Nộp:** `docker save <image> | gzip > zaic.tar.gz`, tính `sha256sum`, upload lên Google Drive (public link), rồi điền form "Solution Submission" kèm checksum. Được nộp tối đa 2 lần, BTC chỉ chấm lần cuối.
