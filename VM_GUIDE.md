# Dựng và test Docker trên máy ảo GPU — từng bước

Máy của bạn dùng AMD Radeon RX 6600 nên không test được image (vLLM chỉ chạy trên NVIDIA). Cách làm: thuê một
máy ảo Linux có GPU NVIDIA, làm **mọi thứ** trên đó (tải dữ liệu, ghép model, build, test, upload), rồi tắt máy.
Tổng khoảng 4–6 giờ máy, tức 3–5 USD.

**Mẹo tiết kiệm:** chuẩn bị xong bước 0 trước khi bật máy. Máy tính tiền theo giờ kể cả lúc bạn đang đọc hướng dẫn.

---

## Bước 0 — Chuẩn bị trên Google Drive (chưa tốn tiền)

Chia sẻ 3 thứ trong `MyDrive/ZAIC/` ở chế độ **"Anyone with the link"** (chuột phải → Share → General access):
- thư mục `ft_fit_adapter` (LLM v4, khoảng 150MB)
- thư mục `asr_ft_v4` (Whisper, khoảng 1.6GB)
- file `lifemate_baseline.zip`

Copy 3 link lại. Mỗi link có dạng `https://drive.google.com/drive/folders/<ID>` hoặc `.../file/d/<ID>/view`.

---

## Bước 1 — Tạo máy

1. Đăng ký **lambda.ai** (Lambda Cloud), thêm thẻ thanh toán.
2. Vào **SSH keys**. Trên Windows, mở PowerShell:
   ```powershell
   ssh-keygen -t ed25519          # Enter liên tục để chấp nhận mặc định
   type $HOME\.ssh\id_ed25519.pub # copy toàn bộ dòng in ra
   ```
   Dán dòng đó vào Lambda, đặt tên bất kỳ.
3. **Launch instance:** chọn **1x A10 (24 GB)**; hết thì chọn A6000 hoặc A100. Region nào cũng được. Không cần gắn filesystem.
4. Đợi trạng thái **Running**, copy **IP**.

Kết nối từ PowerShell:
```powershell
ssh ubuntu@<IP>
```

Kiểm tra GPU trong Docker (phải ra bảng có tên GPU):
```bash
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```
Báo lỗi `permission denied` thì chạy `sudo usermod -aG docker $USER`, thoát (`exit`), rồi `ssh` lại.

---

## Bước 2 — Lấy code, dữ liệu và model

```bash
cd ~ && python3 -m pip install -q gdown
gdown --fuzzy "<link lifemate_baseline.zip>" -O lifemate_baseline.zip
mkdir zaic && cd zaic && unzip -q ../lifemate_baseline.zip

# dữ liệu public test, tải thẳng từ BTC (mạng datacenter nên nhanh)
wget -q "https://dl-challenge.zalo.ai/2026/lifemate_argfzdgert/train+public_test.zip" -O ../data.zip
unzip -q ../data.zip -d ../data
PUB=$(dirname $(find ../data -name public_test.jsonl)); echo $PUB

# model
gdown --folder "<link ft_fit_adapter>" -O adapter
gdown --folder "<link asr_ft_v4>" -O models/asr
python3 -m pip install -q -U transformers peft accelerate torch
python3 -m lifemate.merge --base Qwen/Qwen3-4B-Instruct-2507 --adapter adapter --out models/llm

ls models/llm/config.json models/asr/config.json && du -sh models/*
```

`gdown --folder` báo lỗi quá giới hạn tải thì đợi vài phút rồi chạy lại. Nếu vẫn lỗi, mở link trên trình duyệt
xem đã thật sự để "Anyone with the link" chưa.

---

## Bước 3 — Build và test

```bash
docker pull vllm/vllm-openai:v0.33.0      # không có tag này thì xem ghi chú đầu docker/Dockerfile
bash docker/build_and_test.sh "$PUB"
```

Mất khoảng 30–60 phút. Phải thấy đủ ba dòng:
- `lines: 634 (expected 634)`
- `634 lines checked, 0 schema errors`
- `PASS: identical across runs`

Lỗi gì thì copy nguyên phần cuối log gửi mình.

---

## Bước 4 — Đối chiếu điểm

Tải file kết quả về máy bạn. Chạy trong **PowerShell trên máy bạn**, không phải trong ssh:
```powershell
scp ubuntu@<IP>:~/zaic/result1/submission.jsonl .\submission_docker.jsonl
```
Nộp file này lên leaderboard. Điểm phải gần **44.46**. Lệch nhiều thì báo mình **trước khi** đóng gói.

---

## Bước 5 — Đóng gói và upload lên Drive

```bash
cd ~/zaic
docker save zaic-lifemate | gzip -1 > zaic.tar.gz
sha256sum zaic.tar.gz | tee zaic.sha256      # lưu chuỗi này để điền form
ls -lh zaic.tar.gz
```

Upload thẳng từ máy ảo lên Drive bằng `rclone`, nhanh hơn nhiều so với tải về nhà rồi upload lại:
```bash
sudo -v ; curl https://rclone.org/install.sh | sudo bash
rclone config
#   n (new remote) → name: gdrive → storage: drive → client_id/secret: Enter → scope: 1 (full)
#   → root_folder / service_account: Enter → Edit advanced: n
#   → Use auto config? n   ← máy ảo không có trình duyệt
#   Nó in ra một lệnh "rclone authorize ..." — làm theo dòng hướng dẫn dưới đây
```
Cài rclone trên Windows (rclone.org/downloads, giải nén), chạy đúng lệnh `rclone authorize "drive" ...` nó in ra
trong PowerShell. Trình duyệt sẽ mở để bạn đăng nhập Google. Copy đoạn token in ra, dán ngược vào máy ảo.
Sau đó:
```bash
rclone copy zaic.tar.gz gdrive:ZAIC/ --progress
```

Trên Drive, đặt `zaic.tar.gz` ở chế độ "Anyone with the link", rồi điền form **Solution Submission** trên portal:
link Drive + checksum trong `zaic.sha256`.

---

## Bước 6 — TẮT MÁY

Vào Lambda → Instances → **Terminate**. Quên tắt là máy tính tiền cả đêm.

Khi có model cuối (v6), thuê lại máy, làm lại bước 2 (chỉ đổi adapter) đến bước 6. Lần sau nhanh hơn vì bạn đã quen các bước.
