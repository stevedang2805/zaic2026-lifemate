# Kế hoạch làm một mình — 7/11 → 16/11

Hiện tại: public **44.46**. Trần của LLM khi transcript đúng: 49 (app lạ) / 68 (app quen).
Hạn cứng: **16/11 23:59** nộp Docker. Private test chạy 20–23/11 bằng đúng Docker đã nộp.

Thứ tự dưới đây xếp theo rủi ro: việc có hạn cứng làm trước, việc tăng điểm làm sau. Mục tiêu là làm **đủ cả 11 app**
synthetic; chúng chạy xen kẽ được với thời gian chờ Colab và chờ Docker build.

## Việc 0 (làm ngay hôm nay) — quyết định máy chạy Docker

**Đây là việc chặn mọi thứ.** Colab không chạy được Docker. Chọn một trong ba:

| Phương án | Chi phí | Ghi chú |
|---|---|---|
| Máy cá nhân có GPU NVIDIA ≥16GB | 0 | Windows dùng được qua WSL2 + Docker Desktop + NVIDIA Container Toolkit |
| Máy lab ở trường | 0 | Cần xin quyền chạy Docker, hỏi sớm vì thủ tục mất thời gian |
| Thuê VM GPU (vast.ai, runpod) | khoảng 2–5 USD cho vài giờ | Nhanh nhất, không phụ thuộc ai; cần thẻ thanh toán quốc tế |

Image khoảng 12–14GB (LLM 8GB + Whisper 1.6GB + base), nên cần khoảng 40GB đĩa trống và mạng đủ nhanh để upload lên Drive.

Nếu không phương án nào khả thi, báo mình ngay. Khi đó phải đổi hướng: dùng LLM nhỏ hơn nhiều (Qwen3-1.7B) để image
còn khoảng 5GB, đánh đổi bằng điểm.

## Lịch

| Ngày | Việc | Thời gian |
|---|---|---|
| 7/11 | Chạy notebook v5 trên Colab (A100). Trong lúc chờ: chốt máy Docker | 2h chờ |
| 7–8/11 | Tạo dữ liệu synthetic, đủ 11 app (xem Việc 2) | 4h |
| 9/11 | Chạy v5 lần nữa, lần này có synthetic → model cuối | 2–3h chờ |
| 7/11 (song song) | Dựng Docker với model v4, chạy thử offline — xem `DOCKER_GUIDE.md` | 3h |
| 11–13/11 | Thay model cuối vào Docker, chạy lại, nộp file từ Docker lên leaderboard để đối chiếu | 2h |
| 14/11 | **Nộp Docker** (sớm 2 ngày để còn sửa nếu hỏng) | 1h |
| 15–16/11 | Dự phòng | |

## Việc 1 — chạy v5 (làm ngay)

1. Upload `lifemate_baseline.zip` mới vào `MyDrive/ZAIC/` (ghi đè).
2. Mở `notebooks/zaic_v5_colab.ipynb`, chọn **A100**, Run all. Khoảng 2 giờ.
3. Nộp `submission_public_v5.jsonl`, hạng mục **small models (<6B)**.
4. Gửi mình `results_v5.zip` + điểm.

Chạy lần này **chưa có** synthetic. Sau khi làm xong Việc 2 thì chạy lại chính notebook này, nó sẽ tự gộp synthetic.
Lần chạy lại sẽ bỏ qua bước train 2 Whisper fold (đã lưu trong Drive), nên nhanh hơn.

## Việc 2 — dữ liệu synthetic (đòn bẩy điểm lớn nhất)

Đây là cách duy nhất nâng trần 49 điểm trên app lạ. Mỗi app mất khoảng 20 phút.

**Thứ tự ưu tiên** (theo số mẫu public có cài app đó):

| Ưu tiên | App | Số mẫu public |
|---|---|---|
| 1 | grocery | 107 |
| 2 | recipes | 88 |
| 3 | parking | 87 |
| 4 | public_transit | 82 |
| 5 | pantry | 74 |
| 6 | train_bus_tickets | 74 |
| 7 | ecommerce | 67 |
| 8 | event_tickets | 64 |
| 9 | stocks | 59 |
| 10 | translator | 50 |
| 11 | habit_tracker | 35 |

Làm được 6 app đầu đã là tốt. Hết thời gian thì dừng, phần còn lại vẫn dùng được.

**Quy trình cho mỗi app** (ví dụ `grocery`):

```bash
# 1. sinh prompt (DATA = thư mục chứa train/ và public_test/)
python -m lifemate.synth_prompt --root DATA --app grocery --n 20 > prompt_grocery.txt

# 2. dán toàn bộ prompt_grocery.txt vào ChatGPT / Claude / Gemini
#    lưu nguyên phần trả lời vào synth_specs/grocery.jsonl (chỉ các dòng JSON, bỏ ```json nếu có)

# 3. kiểm tra bằng simulator của BTC
python -m lifemate.synth_build --root DATA --tools-from public_test --specs "synth_specs/*.jsonl"
```

Bước 3 in ra `REJECT <id>: <lý do>` cho mẫu sai. Cách xử lý: dán danh sách lỗi ngược lại cho LLM
("các mẫu sau bị từ chối vì lý do này, sửa lại giúp"), rồi thay các dòng đó. Lặp 2–3 lần là phần lớn qua được.
Mẫu nào vẫn hỏng thì xoá, không cố sửa.

**Cần tự kiểm tra:** bộ lint chỉ bắt mẫu không hợp lệ. Nó không biết tool call có đúng ý câu nói không.
Hãy đọc lướt khoảng 5 mẫu mỗi app, xem `audio_text` và `gold` có khớp nhau không. Mẫu sai ý sẽ dạy model sai.

**Luật:** tuyệt đối không mở, chép hay "lấy cảm hứng" từ `public_test.jsonl` và `public_test_environment/`.
Chỉ dùng catalog và code trong `public_test/zaic_tools/`. Dùng LLM ngoài để sinh dữ liệu là hợp lệ, vì chỉ dùng
trong giai đoạn phát triển, không dùng lúc inference.

Xong hết thì tải cả thư mục `synth_specs/` lên `MyDrive/ZAIC/synth_specs/` rồi chạy lại notebook v5.

## Việc 3 — Docker

Hướng dẫn chi tiết từng bước nằm trong **`DOCKER_GUIDE.md`**. Tóm tắt:

```bash
# cấu trúc thư mục trước khi build
zaic/
├── lifemate/              (từ lifemate_baseline.zip)
├── docker/Dockerfile
├── docker/build_and_test.sh
├── models/llm/            (tải từ MyDrive/ZAIC, model đã merge của lần train cuối)
└── models/asr/            (tải từ MyDrive/ZAIC/asr_ft_v4)

bash docker/build_and_test.sh /duong/dan/toi/public_test
```

Script sẽ: build image, chạy **offline** (`--network none`) trên public test, kiểm tra đủ 634 dòng,
chạy `zaic_tools --validate`, rồi chạy lần hai và so sánh hai file phải giống hệt nhau.

Bốn điều phải đạt trước khi nộp:
1. Đủ 634 dòng, 0 lỗi schema.
2. Hai lần chạy cho kết quả giống hệt nhau (luật về tính tái lập).
3. Thời gian mỗi mẫu dưới 30 giây trên A30. Log in ra `mean`/`max`; trên máy test nên để `max` dưới 20 giây.
4. **Nộp file do Docker sinh ra lên leaderboard**, điểm phải gần bằng điểm của bản chạy từ Colab. Lệch nhiều
   nghĩa là môi trường Docker khác Colab ở đâu đó.

Nộp: `docker save zaic-lifemate | gzip > zaic.tar.gz`, tính `sha256sum zaic.tar.gz`, upload lên Google Drive
(đặt link công khai), rồi điền form "Solution Submission" kèm checksum. Được nộp 2 lần, BTC chỉ chấm lần cuối.

## Dự phòng

Nếu đến 13/11 mà Docker vẫn chưa chạy được, dừng mọi việc khác và dồn hết vào Docker.
Không nộp Docker là mất toàn bộ, dù điểm public có cao đến đâu.
