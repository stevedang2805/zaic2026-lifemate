# Dựng Docker — hướng dẫn từng bước

Làm ngay bây giờ với model **v4** (đã có trong Drive). Khi v5 xong thì chỉ việc thay thư mục model rồi build lại,
mọi thứ khác giữ nguyên. Dựng khung sớm là để nếu có trục trặc thì còn nhiều ngày để sửa.

**Đọc hướng dẫn Docker của BTC trên portal trước.** Chỗ nào khác tài liệu này thì làm theo BTC
(nhất là đường dẫn mount và tên file kết quả).

---

## Bước 1 — Chọn máy

Build image không cần GPU, nhưng **test thì cần**. Và phải test, vì nộp image chưa chạy thử là quá rủi ro.

### Phương án A — Windows có GPU NVIDIA (≥16GB VRAM)
```powershell
wsl --install                      # PowerShell với quyền Administrator, xong thì khởi động lại
```
Cài **Docker Desktop**, vào Settings → Resources → WSL Integration, bật cho distro Ubuntu.
Driver NVIDIA trên Windows đã đủ, không cần cài gì thêm trong WSL. Kiểm tra:
```bash
wsl
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```
Thấy bảng `nvidia-smi` là xong. Cần khoảng 60GB trống trên ổ C (image + file nén).

### Phương án B — Linux có GPU (máy cá nhân hoặc máy lab)
```bash
# cài NVIDIA Container Toolkit nếu chưa có
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update && sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```
Máy lab: cần được thêm vào group `docker`, hoặc có quyền sudo. Hỏi quản trị sớm.

### Phương án C — Thuê máy ảo GPU (bắt buộc nếu máy không có GPU NVIDIA ≥16GB)
Cần một **máy ảo (VM) thật** chạy được Docker. **Không dùng RunPod pod**: pod của RunPod bản thân là một container,
không chạy Docker bên trong được.

Lựa chọn hợp lý: **Lambda Cloud** (lambda.ai) loại **1x A10 (24GB)**, khoảng 0.75 USD/giờ. VM của Lambda cài sẵn
Docker và NVIDIA Container Toolkit. A10 cùng thế hệ với A30 của BTC, nên số đo thời gian mỗi mẫu sát với lúc chấm.
Hết A10 thì chọn A6000 hoặc A100. Dùng khoảng 4–6 giờ, tức 3–5 USD. Xem `VM_GUIDE.md` để làm từng bước.

---

## Bước 2 — Chuẩn bị thư mục

```bash
mkdir -p ~/zaic && cd ~/zaic
unzip /duong/dan/lifemate_baseline.zip        # ra lifemate/, docker/, scripts/, ...
mkdir -p models
```

Cần thêm **dữ liệu public_test** để test (giải nén `train+public_test.zip`, lấy thư mục `public_test/`).

---

## Bước 3 — Lấy model

LLM không cần tải 8GB từ Drive: tải model gốc từ HuggingFace rồi ghép adapter tại chỗ. Adapter chỉ khoảng 150MB.

```bash
pip install -U transformers peft torch accelerate

# 3a. adapter: tải MyDrive/ZAIC/ft_fit_adapter (v4) hoặc ft_v5_adapter (v5) về ~/zaic/adapter/
#     (tải bằng trình duyệt rồi copy lên máy, hoặc dùng gdown nếu đã đặt link chia sẻ)

# 3b. ghép (chạy CPU được, cần ~16GB RAM, khoảng 5-10 phút)
python -m lifemate.merge --base Qwen/Qwen3-4B-Instruct-2507 --adapter ./adapter --out models/llm

# 3c. ASR: tải cả thư mục MyDrive/ZAIC/asr_ft_v4 (khoảng 1.6GB) vào models/asr
```

Kiểm tra trước khi build:
```bash
ls models/llm/config.json models/asr/config.json models/asr/preprocessor_config.json
du -sh models/*          # llm khoảng 8GB, asr khoảng 1.6GB
```

---

## Bước 4 — Build và test

```bash
docker pull vllm/vllm-openai:v0.33.0     # phải khớp phiên bản vLLM của Colab; không có tag này thì xem ghi chú trong Dockerfile
bash docker/build_and_test.sh /duong/dan/toi/public_test
```

Script tự làm: build image, chạy **không mạng** (`--network none`), kiểm tra đủ 634 dòng, chạy
`zaic_tools --validate`, rồi chạy lần hai và so sánh hai file phải giống hệt nhau. Mất khoảng 30–60 phút.

### Lỗi hay gặp

| Lỗi | Cách xử lý |
|---|---|
| `manifest unknown` khi pull | Tag vLLM không tồn tại. Xem các tag có sẵn trên Docker Hub, chọn bản gần nhất, rồi bắt buộc làm bước 5 (đối chiếu điểm) |
| `CUDA out of memory` | Thêm `--gpu-mem 0.60` vào dòng `CMD` trong Dockerfile. Whisper và vLLM dùng chung GPU |
| `could not select device driver` | Chưa cài NVIDIA Container Toolkit, xem lại bước 1 |
| Hai lần chạy khác nhau | Báo mình kèm `diff`. Thường do decode không greedy hoặc do batching |
| Chậm hơn 30 giây/mẫu | Báo mình. Có thể giảm `MAX_GEN` trong `lifemate/agent.py` hoặc `--max-new-tokens` |
| Hết đĩa | `docker system prune -a` để xoá image cũ |

---

## Bước 5 — Đối chiếu điểm (bắt buộc)

Nộp `result1/submission.jsonl` do Docker sinh ra lên leaderboard. Điểm phải **gần bằng** bản chạy từ Colab
(v4: 44.46). Lệch quá 1–2 điểm nghĩa là môi trường Docker khác Colab, phải tìm ra nguyên nhân trước khi nộp.

Bạn được 5 lần nộp mỗi ngày, nên dùng một lần cho việc kiểm tra này là hoàn toàn xứng đáng.

---

## Bước 6 — Đóng gói và nộp

```bash
docker save zaic-lifemate | gzip -1 > zaic.tar.gz    # gzip -1 nhanh hơn nhiều, dung lượng chỉ hơn một chút
sha256sum zaic.tar.gz                                # lưu lại chuỗi này
ls -lh zaic.tar.gz                                   # khoảng 10-14GB
```

Upload lên Google Drive, đặt quyền **"Anyone with the link"**, rồi điền form "Solution Submission" trên portal:
link Drive, checksum, mô tả giải pháp. Được nộp 2 lần, BTC chỉ chấm lần cuối.

Upload từ nhà có thể mất vài giờ. Từ VM thuê thì dùng `rclone` (cấu hình `rclone config` với Google Drive)
và chỉ mất vài phút.

---

## Khi model v5 xong

Chỉ cần làm lại bước 3b với adapter mới, rồi chạy lại bước 4:
```bash
python -m lifemate.merge --base Qwen/Qwen3-4B-Instruct-2507 --adapter ./adapter_v5 --out models/llm
bash docker/build_and_test.sh /duong/dan/toi/public_test
```
Docker sẽ dùng lại các layer cũ, nên build lần sau nhanh hơn nhiều.
