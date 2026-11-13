# Dựng, test và nộp Docker trên Vast.ai — từng bước

Tổng chi phí ước tính: **3–5 USD** (GPU khoảng 0.3–0.6 USD/giờ × 4–6 giờ, cộng phí lưu trữ và băng thông).
Nạp **10 USD** là dư, và phần còn lại dùng được cho lần build model cuối.

**Hai điều phải nhớ:**
1. Chọn đúng template **"Ubuntu 22.04 VM"**. Máy loại container (mặc định) **không chạy được Docker bên trong**.
2. Xong việc phải bấm **Destroy**. Bấm **Stop** thì Vast vẫn tính phí lưu trữ.

---

## Bước 0 — Chuẩn bị (chưa tốn tiền)

**0a. Chia sẻ file trên Google Drive.** Trong `MyDrive/ZAIC/`, chuột phải → Share → General access →
**Anyone with the link**, cho 3 thứ sau, rồi copy 3 link lại:
- thư mục adapter LLM **đã chốt: `ft_v11_all_adapter`** (public 52.10)
- thư mục ASR **đã chốt: `asr_v8_large_all`** (Whisper large-v3) — **bắt buộc làm Bước 5b**
- file `lifemate_baseline.zip` (bản mới nhất)

**0b. Tạo SSH key trên Windows.** Mở PowerShell:
```powershell
ssh-keygen -t ed25519            # Enter liên tục để chấp nhận mặc định, không cần đặt mật khẩu
type $HOME\.ssh\id_ed25519.pub   # copy TOÀN BỘ dòng in ra (bắt đầu bằng ssh-ed25519 ...)
```
Đã có key từ lần thử Lambda thì chỉ cần chạy lệnh `type`.

---

## Bước 1 — Tài khoản và nạp tiền

1. Đăng ký tại **cloud.vast.ai**.
2. Vào **Billing** → nạp **10 USD**. Vast nhận thẻ (qua Stripe) và crypto (qua BitPay hoặc Crypto.com).
   Thẻ bị từ chối thì bật "thanh toán trực tuyến quốc tế" trong app ngân hàng rồi thử lại.
3. Vào **Account** → **Keys** (SSH keys) → thêm key đã copy ở bước 0b.
   **Phải thêm key TRƯỚC khi tạo máy.** Máy đã chạy rồi thì không thêm key được, và sẽ không vào được máy.

---

## Bước 2 — Tạo máy ảo

1. Vào tab **Templates**, tìm **"Ubuntu 22.04 VM"**, bấm chọn. Template này đã có CUDA và Docker, và tự lọc
   những máy hỗ trợ VM.
2. Sang tab **Search**. Chỉnh trước khi thuê:
   - **Disk space: 150 GB.** Kéo thanh disk ở bên trái. Đặt đủ ngay từ đầu, vì sau khi tạo máy thì khó đổi.
     (Image vLLM khoảng 10GB, model gốc 8GB, model ghép 8GB, image mới 14GB, file nén 12GB, dữ liệu, cộng dư.)
   - **GPU:** chọn một trong **RTX 3090, RTX 4090, A5000, A10, L4, A6000**; tất cả đều 24GB trở lên.
     RTX 3090 thường rẻ nhất.
3. Cách chọn máy trong danh sách:
   - **Reliability** từ 98% trở lên.
   - **Internet** ↓ và ↑ từ 500 Mbps trở lên (cần tải khoảng 25GB và upload 12GB).
   - Xem giá **băng thông** (đơn vị $/TB) của máy đó. Tránh máy tính phí băng thông quá cao.
   - Giá GPU khoảng 0.2–0.6 USD/giờ là hợp lý.
4. Bấm **RENT**.
5. Sang tab **Instances** và đợi. Máy VM khởi động lâu hơn container, có thể mất 5–15 phút.
   Khi nút xanh đổi thành **>_CONNECT** là xong.

---

## Bước 3 — Kết nối và kiểm tra GPU

Bấm **>_CONNECT**, copy lệnh SSH (dạng `ssh -p <port> <user>@<IP>`), dán vào **PowerShell** trên máy bạn.
Lần đầu nó hỏi `Are you sure you want to continue connecting` thì gõ `yes`.

Vào được máy thì chạy:
```bash
# chặn máy tự cập nhật driver giữa chừng (lần trước gây lỗi "driver/library version mismatch", phải reboot)
systemctl disable --now unattended-upgrades
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```
Cả hai đều phải ra bảng có tên GPU.

- `docker: permission denied` → `sudo usermod -aG docker $USER`, gõ `exit`, rồi SSH lại.
- `could not select device driver` → cài NVIDIA Container Toolkit:
  ```bash
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  sudo apt update && sudo apt install -y nvidia-container-toolkit
  sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker
  ```
- Đăng nhập bằng `root` thì bỏ chữ `sudo` ở mọi lệnh.

**Mẹo:** gõ `tmux` ngay sau khi vào máy. Nếu mất mạng giữa chừng, các lệnh vẫn chạy tiếp; SSH lại rồi
gõ `tmux attach` để xem tiếp.

---

## Bước 4 — Lấy code, dữ liệu và model

```bash
cd ~ && python3 -m pip install -q gdown
gdown <ID file lifemate_baseline.zip> -O lifemate_baseline.zip   # ID = đoạn giữa /d/ và /view trong link; gdown mới không còn --fuzzy
mkdir -p zaic && cd zaic && unzip -q ../lifemate_baseline.zip

# dữ liệu, tải thẳng từ BTC
wget -q --show-progress "https://dl-challenge.zalo.ai/2026/lifemate_argfzdgert/train+public_test.zip" -O ../data.zip
unzip -q ../data.zip -d ../data
PUB=$(dirname $(find ../data -name public_test.jsonl)); echo "$PUB"

# model
gdown --folder "<link ft_v11_all_adapter>" -O adapter
gdown --folder "<link asr_v8_large_all>" -O models/asr
python3 -m pip install -q -U transformers peft accelerate torch
python3 -m lifemate.merge --base Qwen/Qwen3-4B-Instruct-2507 --adapter adapter --out models/llm

ls models/llm/config.json models/asr/config.json && du -sh models/*
```
Kết quả đúng: `models/llm` khoảng 8GB, `models/asr` khoảng 1.6GB (turbo) hoặc **khoảng 3.1GB (large-v3)**.

- `gdown` báo quá giới hạn tải → đợi vài phút rồi chạy lại. Vẫn lỗi thì kiểm tra link đã đặt "Anyone with the link" chưa.
- `pip` báo `externally-managed-environment` → thêm `--break-system-packages` vào lệnh pip.

---

## Bước 5 — Build và test

```bash
docker pull vllm/vllm-openai:v0.33.0
bash docker/build_and_test.sh "$PUB"
```
Mất khoảng 30–60 phút. Phải thấy đủ ba dòng:
- `lines: 634 (expected 634)`
- `634 lines checked, 0 schema errors`
- `PASS: identical across runs`

Gặp lỗi thì copy **nguyên phần cuối log** gửi mình. Lỗi hay gặp:
- `manifest unknown` khi pull → tag v0.33.0 không có trên Docker Hub. Báo mình để chọn tag khác.
- `CUDA out of memory` → sửa dòng `CMD` trong `docker/Dockerfile`, thêm `"--gpu-mem", "0.60",` rồi chạy lại.

---

## Bước 5b — Chỉ khi ASR là Whisper large-v3 (1.55B)

large-v3 nặng gấp đôi turbo (3.1GB fp16 so với 1.6GB) và giải mã chậm hơn khoảng 3 lần (32 lớp decoder thay vì 4).
Làm **trước** khi chạy `build_and_test.sh`:

1. **Bộ nhớ:** mở `docker/Dockerfile`, trong `CMD` thêm `"--gpu-mem", "0.62",` ngay trước `"--out"`. Whisper được nạp trước,
   vLLM chỉ được lấy 62% GPU (≈14.9GB trên 24GB: 8GB trọng số + đủ KV cache cho 16K token). Giữ 0.70 sẽ dễ OOM lúc beam search dự phòng của Whisper.
2. **Kiểm tổng tham số:** 4.02B + 1.55B = 5.57B < 6B, LLM 4.02B < 5B. Ghi đúng số này vào form nộp.
3. **Thời gian mỗi mẫu:** sau khi `build_and_test.sh` chạy xong, xem dòng cuối log `[infer] 634/634 mean X s max Y s`.
   Yêu cầu: **max dưới 20 giây trên máy test** (A30 chấm thật chậm hơn RTX 4090/3090 khoảng 1.2–1.5 lần ở phần ASR; phần LLM
   decode gần bằng nhau vì phụ thuộc băng thông bộ nhớ). Mốc v4 turbo trên 4090: mean 1.8s, max 12.4s.
   Nếu max 20–25s: giảm `--time-budget` xuống `20.0` (thêm `"--time-budget", "20.0",` vào `CMD`) và chạy lại 2 lần để chắc vẫn tất định.
   Nếu max trên 25s: **quay về turbo** (`asr_ft_v4`), không đáng mạo hiểm mất cả mẫu vì quá giờ.
4. Nếu được, thuê **A10 hoặc L4** thay vì 3090/4090 để đo thời gian: hai loại này chậm ngang hoặc hơn A30, số đo sẽ thiên về an toàn.

---

## Bước 6 — Đối chiếu điểm (bắt buộc)

Tải file kết quả về máy bạn. Chạy trong **PowerShell trên máy bạn**, không phải trong SSH. Dùng đúng port,
user và IP của lệnh SSH (lưu ý `scp` dùng **chữ P hoa**):
```powershell
scp -P <port> <user>@<IP>:~/zaic/result1/submission.jsonl .\submission_docker.jsonl
```
Nộp file lên leaderboard. Điểm phải gần **44.46**. Lệch nhiều thì báo mình **trước khi** làm bước 7.

---

## Bước 7 — Đóng gói và upload lên Drive

```bash
cd ~/zaic
docker save zaic-lifemate | gzip -1 > zaic.tar.gz
sha256sum zaic.tar.gz | tee zaic.sha256
ls -lh zaic.tar.gz
```

Upload từ máy ảo lên Drive bằng `rclone`:
```bash
curl https://rclone.org/install.sh | sudo bash
rclone config
```
Trả lời lần lượt: `n` (new remote) → name: `gdrive` → storage: `drive` → client_id, client_secret: Enter →
scope: `1` → các câu sau: Enter → Edit advanced config: `n` → **Use web browser to automatically authenticate: `n`**.

Nó in ra một lệnh `rclone authorize "drive" "..."`. Trên **Windows**, tải rclone tại rclone.org/downloads,
giải nén, mở PowerShell trong thư mục đó, chạy **đúng** lệnh vừa in (thêm `.\` đằng trước: `.\rclone authorize ...`).
Trình duyệt mở ra, đăng nhập Google, cho phép. PowerShell in ra một đoạn token; copy và dán ngược vào máy ảo.
Các câu còn lại: Enter / `n` / `y`.

```bash
rclone copy zaic.tar.gz gdrive:ZAIC/ --progress
rclone copy zaic.sha256 gdrive:ZAIC/
```

Trên Drive, đặt `zaic.tar.gz` ở chế độ "Anyone with the link". Điền form **Solution Submission** trên portal:
link Drive và chuỗi checksum trong `zaic.sha256`.

---

## Bước 8 — DESTROY máy

Vào tab **Instances** → biểu tượng thùng rác (**Destroy**). Không phải Stop.

Khi có model cuối (v6), thuê máy mới và làm lại từ bước 2. Ở bước 4 chỉ đổi link adapter.
