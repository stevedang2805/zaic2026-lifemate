# HANDOFF — Zalo AI Challenge 2026 · LifeMate (đội DS@CocCocCoc)

Tài liệu bàn giao để tiếp tục trong một đoạn chat mới. Cập nhật: **13/11/2026, 12:00 (GMT+7)** — **CẤU HÌNH CUỐI = 52.10** (mục 15). Việc còn lại: Docker.

**Cách dùng:** mở chat mới, đính kèm `HANDOFF.md` và `lifemate_baseline.zip`, rồi gửi câu mở đầu:
> "Đây là tài liệu bàn giao và code của cuộc thi ZAIC 2026 LifeMate mình đang làm. Đọc HANDOFF.md trước, giải nén zip
> để xem code. Mình muốn tiếp tục từ mục 9 (việc còn lại)."

Người làm: Đặng Nguyên Thọ (UIT, KHDL). Làm một mình dù đội có 3 người. Giao tiếp bằng tiếng Việt; muốn nhận xét
thẳng, có số liệu, không trấn an; sửa đúng phạm vi được yêu cầu; nhận file ở định dạng gốc. Máy cá nhân dùng GPU AMD
(RX 6600) nên không chạy được Docker GPU ở nhà; train trên Colab Pro, dựng Docker trên máy ảo thuê ở Vast.ai.

---

## 1. Đề bài

Xây agent nhận **yêu cầu nói tiếng Việt** (audio, có thể lẫn từ tiếng Anh) cùng ngữ cảnh người dùng, danh sách app đã
cài (mỗi app có các tool mô tả bằng JSON Schema), lịch sử hội thoại, và một môi trường mô phỏng chứa dữ liệu app.
Agent phải gọi **chuỗi tool đúng, với đối số đúng**, để các app về đúng trạng thái người dùng muốn. Agent được chấm
qua hành động, không qua lời nói. Có 3 tình huống:
- **Làm được:** gọi các tool cần thiết theo thứ tự.
- **Thiếu thông tin:** gọi `sys.ask_missing_info` (nêu tool định dùng và tham số còn thiếu). Có thể gọi sau khi đã chạy
  vài tool khác.
- **Ngoài phạm vi** (không app nào làm được): trả `[]`.

**Đầu vào mỗi mẫu** (`<split>.jsonl`): `id`; `audio` (lượt cuối, `audio/<id>/<id>.wav`); `context`
(`current_time`, `timezone`, `location`, `user_profile` gồm nhà, nơi làm, thành phố; `installed_apps`
`{app: {"tools": [...]}}`); `history` (lượt user có audio `<id>_u1.wav`…; lượt assistant có `text`, có thể kèm
`tool_calls`/`tool_results`, đã được áp sẵn vào state). Chỉ train có thêm `audio_text` (transcript) và `label`
(`tool_calls`, `tool_results`, `final_state`).

**Catalog** (`<split>_tools_catalog.json`): mỗi tool có `name` `<app>.<tool>`, `kind` (`read`/`write`/`meta`),
`description`, `parameters` (JSON Schema + mở rộng `x-one-of`, `x-ref` = id lấy từ app khác, `x-match: fuzzy` = văn bản
tự do chấm gần đúng), `returns`.

**Thư viện `zaic_tools`** (chỉ dùng thư viện chuẩn, đi kèm từng split):
```python
env = ToolEnv("public_test", "public_0001", root=".")  # một phiên cho một mẫu
env.call(name, args)       # chạy -> {"ok": true, ...} | {"ok": false, "error": ...}; call bị từ chối vẫn được ghi lại
env.validate(name, args)   # chỉ kiểm schema, KHÔNG ghi log
env.get_tool_calls(); env.get_state_hash()
```
CLI kiểm tra file nộp: `cd public_test && python -m zaic_tools --split public_test --root .. --validate submission.jsonl`

**File nộp** `submission.jsonl` (UTF-8, mỗi mẫu đúng 1 dòng):
`{"id": ..., "tool_calls": env.get_tool_calls(), "state_hash": env.get_state_hash()}`

**Dữ liệu:** gói v3.2.0 (build 24/10/2026): train 1545 mẫu (5036 clip audio), public_test 634 mẫu.
Link: `https://dl-challenge.zalo.ai/2026/lifemate_argfzdgert/train+public_test.zip`.
Private test chỉ phát hành sau khi đã nộp Docker. Không được chia sẻ dữ liệu ra ngoài đội.

## 2. Cách chấm

Theo luật, đã cài lại trong `scripts/score.py`. Bản cài lại khớp 1545/1545 khi replay đáp án của train.
- Gold `[]`: được 1 điểm nếu dự đoán cũng `[]`, ngược lại 0.
- `state_hash` dự đoán khác gold, hoặc không call nào khớp: 0.
- Còn lại: F1 với P = M/(M+U), R = M/|G|. M = số call khớp (ghép cặp tối đa, không xét thứ tự), U = số call thừa,
  **tính cả call bị từ chối**.
- Một call khớp khi: cùng tên, mọi đối số không-fuzzy giống hệt nhau, mọi đối số fuzzy có token-F1 > 0.6 (sau khi
  lowercase và chuẩn hoá NFC). Giả định của mình: tập key phải bằng nhau, tức truyền thừa một tham số tuỳ chọn thì không khớp.
- Tie-break: F1 không tính hash.
- Độ nhạy (thử trên đáp án train): thêm 1 read thừa mỗi mẫu → 75.9; bỏ hết read → 71.5; bỏ write cuối → 24.5.
  Write sai thì về 0; read thừa chỉ trừ ít.

## 3. Luật và ràng buộc

Kiểm tra lại với trang cuộc thi trước khi nộp.
- **Hạng mục nộp: "Based on small models (<6B)".** Tổng tham số toàn hệ thống < 6B; LLM < 5B; context ≤ 16K token.
- Lúc suy luận chạy **offline** (Docker chạy `--network none`). **≤ 30 giây/mẫu trên 1×A30 (24GB).**
- **Tất định:** greedy decoding, seed cố định, chạy lại phải ra đúng file cũ.
- Agent **không được đọc, copy hay parse bất kỳ file nào trong `<split>_environment/`** (kể cả `state.json`).
  **Mỗi mẫu đúng 1 `ToolEnv`, chỉ tạo một lần** (không được tạo lại để thử rồi làm lại).
  Lúc suy luận chỉ được dùng `validate`, `call`, `get_tool_calls`, `get_state_hash`.
  `get_state` chỉ được dùng trên train/dev.
- **Không được gán nhãn public_test hay private_test để train hoặc tune.** Dữ liệu synthetic của mình chỉ sinh từ
  catalog và code `zaic_tools`, không đọc `public_test.jsonl` hay `public_test_environment/`.
- Được dùng model khác để sinh dữ liệu synthetic trong lúc phát triển (không được dùng lúc suy luận).
- Model phải phát hành trước 26/10/2026 và có giấy phép mở.
- **Hạn nộp Docker: 16/11/2026, 23:59 GMT+7.** Tối đa 2 lần nộp, lần cuối được tính. Nộp bằng link Google Drive
  công khai + checksum (form "Solution Submission" trên portal). Private test chấm từ 20 đến 23/11 bằng chính Docker đã nộp.
- Leaderboard public mỗi lần nộp cần chọn loại model, chọn **SLM**.

## 4. Trạng thái hiện tại

| | Public | Ghi chú |
|---|---|---|
| **Docker v4** (bản dự phòng chắc chắn) | **45.29** | đúng 634 dòng, 0 lỗi schema, 2 lần chạy giống hệt, trung bình 1.8 s/mẫu, chậm nhất 12.4 s (RTX 4090) |
| v4 (Colab) | 44.46 | |
| v7 (Colab) | 44.72 | hoà với v4 |
| Top leaderboard | khoảng 96 | |

**Hệ thống tốt nhất:** ASR `asr_ft_v4` (Whisper large-v3-turbo fine-tune, 809M) → LLM Qwen3-4B-Instruct-2507 (4.02B)
+ LoRA `ft_fit_adapter`, chạy bằng vLLM 0.33.0 với greedy decoding. Tổng khoảng 4.83B.

**Tài sản trên Drive (`MyDrive/ZAIC/`):**
- `ft_fit_adapter`: **LLM tốt nhất** (train ở v2 trên train_fit, đang chạy trong Docker v4)
- `asr_ft_v4`: **ASR tốt nhất** (train trên 3936 clip, giữ lại clip của val)
- `ft_v6_adapter`, `ft_v7_adapter`: các adapter thử nghiệm. `ft_v5_adapter`: **không dùng**.
- `asr_train_oof.json`: transcript ASR out-of-fold của train (dùng ở v5)
- `synth_specs/gen_*.jsonl`: 11 file, 440 spec synthetic sinh bằng code (v6/v7)
- `synth_specs/llm_*.jsonl`: 11 file, **320 spec viết tay — bộ đã dùng cho v9 (47.17)**
- `synth_specs_claude/claude_*.jsonl`: 285 spec Claude viết từ catalog (v11, mục 12)
- `ft_v10_adapter`: **BỊ LOẠI, không dùng** (mục 11)
- `synth_specs_c12/c12_*.jsonl`: 131 spec nhắm lỗi val (v12, mục 13)
- `ft_v9_adapter`: adapter v9 (public 47.17)
- `ft_v11_adapter`: **đang là tốt nhất** (public 49.53); ASR gap đo được 11.8 / 14.3 điểm
- `lifemate_baseline.zip`: code. **Phải luôn là bản mới nhất**, notebook kiểm tra bằng sự có mặt của `scripts/detcheck.py`.
- `results_v*.zip`, `submission_public_v*.jsonl`

**Docker image cuối chưa được upload.** Máy Vast đã dùng xong và phải Destroy. Bản Docker v4 chỉ tồn tại dưới dạng công
thức (code + 2 thư mục model trên Drive), cần dựng lại khi nộp.

## 5. Kiến trúc và code (`lifemate_baseline.zip`)

```
lifemate/
  prompt.py      system prompt (10 quy tắc lấy từ gold), bảng ngày tương đối, schema rút gọn ([đọc]/[ghi]),
                 history -> chat turns, shrink() khi prompt > 16K
  agent.py       vòng lặp 1 mẫu (generator) + guards
  backends.py    vllm (prefix caching, greedy) / hf / oracle (replay gold)
  run.py         chạy cả split (dev, có --batch)
  infer.py       ĐIỂM VÀO CỦA DOCKER: ASR từng mẫu + agent batch 1, mỗi mẫu bọc try/except để luôn ghi đủ dòng,
                 --trace, --vllm-kw (mặc định: không torch.compile, giữ CUDA graph)
  asr.py         Whisper pipeline; looks_bad() bắt câu bịa ("subscribe…"), lặp từ, lặp ký tự -> giải mã lại bằng beam
  asr_finetune.py fine-tune Whisper (fp32 + autocast bf16, SpecAugment, gain aug, --exclude để giữ lại val)
  sft_data.py    dữ liệu SFT đúng định dạng prompt lúc chạy; augment (đổi tên app, thêm app gây nhiễu, xáo thứ tự);
                 --drop-empty, --asr/--asr-max-wer
  train_lora.py  LoRA r32/α64, mọi lớp linear, loss chỉ trên lượt hiện tại; lưu adapter + merged
  priors.py      học từ gold: tham số tuỳ chọn hiếm khi truyền, filter của read; quy tắc chung cho app lạ
  textnorm.py    số đọc bằng chữ -> gợi ý chuỗi số (13/13 đúng trên train)
  synth_gen.py   sinh synthetic bằng code cho 11 app chỉ có ở public (40/app, đáp án tính từ state)
  synth_build.py dựng split synth và kiểm tra bằng simulator của BTC; synth_prompt.py: prompt cho LLM ngoài
  merge.py, splits.py, report.py (phân loại lỗi), tokstats.py
scripts/score.py      scorer local
scripts/detcheck.py   so 2 lần chạy (submission + trace), chỉ ra lệch do ASR hay do LLM
docker/Dockerfile     FROM vllm/vllm-openai:v0.33.0; copy models trước, code sau; CMD python3 -m lifemate.infer
docker/build_and_test.sh  build, chạy offline 2 lần, kiểm số dòng, validate, so 2 lần chạy
docker/det_test.sh, det_try.sh  thử độ tất định (mount code, không cần build lại)
notebooks/            v2…v7, v8_asr, final_llm (bản sao trong colab/)
splits/               val_unseen 193 (6 app giữ lại: learning, door_lock, loyalty, package_tracking, library,
                      appliances), val_seen 135, train_fit 957
VAST_GUIDE.md         dựng, test và nộp Docker trên Vast.ai từng bước (đã cập nhật các lỗi gặp phải)
```

**Guards trong agent** (đều dựa trên số liệu gold của train):
- `validate` trước `call`; lỗi schema được báo lại cho model.
- Bỏ key không có trong schema (kể cả với tool không có tham số); ép kiểu `"500000"` → int.
- Read giống hệt đã gọi trong turn: trả lại kết quả cũ, không gọi lại.
- Read đã có kết quả trong history và còn "mới": trả kết quả history. Gold không đọc lại read còn mới (0/1522);
  chỉ đọc lại read đã cũ, tức sau đó có write vào cùng app (4/838).
- Write giống hệt được phép lặp (gold đổi 2 voucher = 2 call `redeem` giống nhau).
- ID chưa từng xuất hiện: cảnh báo 1 lần, nếu model gọi lại y hệt thì cho chạy (1308/1309 ID trong gold đã xuất hiện trước).
- `ask_missing_info` phải nêu tool đã cài và đúng tên tham số, gọi xong thì dừng (217/217).
- Nhắc 1 lần khi model trả lời "Đã …" mà chưa gọi write nào.
- Tối đa 10 lần thực thi và 16 lần sinh mỗi mẫu; ngân sách 24 giây (chỉ áp khi batch 1).
- Priors: các quy tắc chung luôn bật (kể cả khi `priors=None`); làm mất F1 ở 11 mẫu train nhưng giữ nguyên để tái hiện v4.

**Quy ước của gold** (đã đưa vào prompt):
- Đọc để lấy ID trước khi dùng ID. Read dạng liệt kê gọi với `{}`.
- Thiếu giá trị: vẫn tra ID trước (vd. `contacts.search`), rồi mới `ask_missing_info`. `ask_missing_info` luôn là call
  cuối, đúng 1 tham số.
- `[]` cho: nói chuyện phiếm; huỷ ("à thôi khỏi"); không app nào làm được; điều kiện đã biết là sai từ history;
  đã trả lời trong history.
- Tham số tuỳ chọn hầu như không truyền (alarm label 1/78, note của chuyển khoản 1/82, không truyền repeat).
  `calendar.create_event` thường truyền `end` = `start` + 1 giờ (24/32).
- Ngày tương đối: "thứ X" = lần tới gần nhất; "thứ X này" = trong tuần Thứ 2–CN hiện tại; "thứ X tuần sau" = tuần sau.

## 6. Lịch sử thử nghiệm

| Bản | Thay đổi | val_unseen / val_seen | Public |
|---|---|---|---|
| v1 | baseline zero-shot, transcript gold | 27.1 / 34.0 | — |
| v2 | guards + priors + LoRA trên train_fit (L4, 5.5 h) | 48.6 / 66.9 (transcript gold) | — |
| v3 | thêm ASR: Whisper turbo gốc (WER 34.6%) | gold 49.0 / 67.7; turbo 25.3 / 35.6; PhoWhisper 23.5 / 32.8 | 28.53 |
| **v4** | **fine-tune Whisper turbo** (3 epoch, 3936 clip): WER 11.52%, CER 8.74% | **35.06 / 54.11** | **44.46** |
| v5 | 2 fold ASR OOF + SFT trên transcript nhiễu + `--detach-prefix` | 37.67 / 52.96 | 40.49 ✗ |
| v6 | v4 + 440 mẫu synthetic | 35.96 / 51.54 | 43.31 ✗ |
| v7 | v6 + `--drop-empty` (bỏ 42 mẫu synthetic có đáp án `[]`) | 34.88 / 56.02 | 44.72 ≈ |
| Docker v4 | v4 trong Docker, không torch.compile | — | **45.29** |
| v9 | v4 + 440 gen (aug 1) + 320 spec viết tay (aug 2), drop-empty, L4 7.3 h | 39.52 / 58.31 | 47.17 |
| v10 | **BỊ LOẠI** (spec viết từ transcript public) | 39.70 / 55.87 | 46.62 |
| **v11** | v9 + 285 `claude_*` (từ catalog), A100 2 h | **40.90 / 55.68**; transcript chuẩn 52.66 / 69.93 | **49.53** |

**Bài học:**
- **v5 thất bại vì hai lý do.** (1) Transcript ASR nghe sai một con số mà đáp án vẫn giữ số đúng, nên model học cách
  **đoán thay vì hỏi**: trên public, `ask_missing_info` tụt từ 92 xuống 62. (2) `--detach-prefix` làm loss y hệt nhưng
  model đọc schema kém đi. **Không dùng cả hai.**
- **v6 thất bại vì các mẫu synthetic có đáp án `[]` quá rập khuôn** ("à thôi không mua nữa", "nếu … không thì thôi"),
  nên model học phản xạ trả `[]`. Số mẫu trả rỗng trên public tăng 64 → 106; "không gọi tool dù gold có hành động"
  tăng 17 → 27 (unseen) và 5 → 19 (seen). Phần synthetic có hành động thì giúp: sai đối số trên val_unseen giảm 49 → 39.
- **v7 hoà v4.** Trên public, v7 đổi output của 223/410 mẫu có app mới mà điểm gần như không đổi. Synthetic sinh bằng
  code không tăng điểm thật.
- **Val nhỏ (193/135 mẫu), không tin một mình được.** Từ v5 trở đi, điểm public là trọng tài. Dao động giữa 2 lần chạy
  khác kernel khoảng ±1 điểm, nên chênh dưới 1 điểm coi như hoà.
- **Trần hiện tại:** với transcript chuẩn, LLM đạt 49 (app lạ) / 68 (app quen). ASR làm mất khoảng 14 điểm.
  65% mẫu public (410/634) dùng 11 app không có trong train: ecommerce, event_tickets, grocery, habit_tracker, pantry,
  parking, public_transit, recipes, stocks, train_bus_tickets, translator. 6 app giữ lại làm val **không** xuất hiện
  trong public.

**Lỗi còn lại** (v4, val_unseen, số điểm mất trên 100):
- sai đối số write: 25.4 (top: `appliances.start_cycle`, `reminders.create`, `calendar.create_event`)
- thiếu write: 13.0
- không gọi tool dù gold có hành động: 8.8
- write thừa: 8.8
- call đọc thừa hoặc thiếu (F1): 8.2

Các lỗi chủ yếu đến từ suy luận của LLM, ví dụ chọn sai tool (`reschedule_delivery` thay cho `schedule_pickup`),
sai mã chế độ ("giặt nhanh" → `eco` thay vì `quick`).

## 7. Docker: những gì đã kiểm chứng (11/11)

- Base `vllm/vllm-openai:v0.33.0` (torch 2.14.0+cu130, triton 3.8.0). Image chỉ có `python3`, không có `python`.
- **Tất định:** khi bật torch.compile, Inductor đo tốc độ để chọn kernel lúc khởi động. Khoảng 1/4 lần chạy chọn khác
  và 49/634 output đổi theo. Đã kiểm: Whisper không gây lệch (ASR giống hệt), lệch nằm trong vLLM với cùng một prompt.
  Cách sửa đang dùng (mặc định trong `infer.py`): `compilation_config={"mode": 0, "cudagraph_mode": "FULL"}`.
  Chậm hơn khoảng 0.4 s/mẫu, nhưng không còn bước nào phải chọn kernel, trên bất kỳ GPU nào.
  Các phương án đã thử trên 200 mẫu: `inductor_det` 1.98 s (chạy được, nhưng không chắc chặn hết);
  `eager + no prefix cache` 5.06 s, chậm nhất 26 s (quá sát giới hạn).
- Image khoảng 14GB. Vast VM (template "Ubuntu 22.04 VM", đĩa 150GB). Phải cài NVIDIA Container Toolkit, và tắt
  `unattended-upgrades` ngay từ đầu, vì nó tự nâng driver giữa chừng gây lỗi "driver/library version mismatch"
  (phải reboot).
- `scp` chạy trên **PowerShell của Windows** (`-P` viết hoa), không chạy trong SSH. Đóng gói:
  `docker save zaic-lifemate | gzip -1 > zaic.tar.gz`, rồi `sha256sum`, rồi `rclone` lên Drive.
- Chi tiết từng bước: `VAST_GUIDE.md`.

## 8. Đánh giá thẳng về khả năng tăng điểm

Mục tiêu 60–70 **gần như không khả thi** trước 16/11 với hướng hiện tại. Kể cả khi ASR hoàn hảo, public chỉ khoảng
55–58. Trần nằm ở khả năng suy luận của LLM 4B trên app lạ. Thực tế đạt được khoảng 45–49.
Hướng có thể tăng lớn hơn, nhưng cần 1–2 tuần, nên **không** làm kịp:
- cho model suy nghĩ từng bước, hoặc lập kế hoạch ngắn trước khi gọi tool (phải giữ ≤ 30 s trên A30);
- dữ liệu SFT chất lượng cao do model lớn sinh cho 11 app mới, đa dạng hơn synthetic sinh bằng code;
- TTS để có audio cho từ vựng của app mới (tên sản phẩm, mã cổ phiếu, ga tàu), giúp ASR.

## 9. Việc còn lại (theo thứ tự)

0. **`zaic_v9_colab.ipynb`** (A100, 2–3 giờ) — xem mục 10. Chạy trước v8 vì cùng dùng `asr_ft_v4` nên so sánh thẳng với v4/v7.

1. **`zaic_v8_asr_colab.ipynb`** (A100, khoảng 2 giờ): Whisper large-v3 (1.55B; tổng 5.57B < 6B) thay cho turbo.
   LLM giữ adapter v4. Mốc so sánh: WER 11.52%, val 35.06 / 54.11, public 44.46.
   Thắng khi WER dưới khoảng 10.5% **và** public cao hơn ít nhất 1 điểm.
   Sau đó chạy lại notebook với `HOLD_OUT=False` (và `ASR_BASE` của bản thắng) để train ASR trên toàn bộ 5036 clip.
2. **`zaic_final_llm_colab.ipynb`** (tuỳ chọn, A100 khoảng 4 giờ; L4 khoảng 9 giờ): `TRAIN_ALL=True`,
   `USE_SYNTH=True` → `ft_final_adapter`. Kỳ vọng +0 đến +1 (gần như tung đồng xu). Nếu không chạy, dùng `ft_fit_adapter`.
   Nếu ASR mới thắng, đặt `ASR_PROD` trỏ tới thư mục ASR mới.
3. **13–14/11, Docker cuối:** thuê Vast mới, làm theo `VAST_GUIDE.md`, thay link adapter và ASR đã chọn.
   - Nếu dùng large-v3: kiểm thời gian mỗi mẫu (phải còn dư nhiều so với 30 s trên A30) và bộ nhớ (`--gpu-mem 0.70`
     dành phần còn lại cho Whisper).
   - Chạy `build_and_test.sh` phải ra đủ 3 dòng PASS. Nộp `result1` lên public để đối chiếu.
   - `docker save | gzip`, sha256, upload Drive, đặt link "Anyone with the link", điền form.
4. **15–16/11: dự phòng.** Nếu bản cuối có vấn đề, nộp lại **Docker v4** (`ft_fit_adapter` + `asr_ft_v4`, đã chứng minh 45.29).
5. Sau khi ban tổ chức tải xong, đặt các link Drive về chế độ Restricted.

## 10. v9 (11/11 tối) — public 47.17

v9 thực tế đã chạy dùng `synth_specs/llm_*.jsonl` (**320 spec viết tay**, từ một phiên làm việc song song) + 440 `gen_*`;
GEN_AUG=1, LLM_AUG=2 (`--seed 1`), drop-empty, train_fit, L4 7.3 giờ. Kết quả: val 39.52 / 58.31, public **47.17** (+2.45 so với v7).
Lưu ý: 285 spec do Claude viết cùng tối (`synth_specs_v9_claude/`, generator `tools/synth_v9/`) **chưa từng được train**;
chúng trùng id với 320 spec trên (cùng cách đặt tên `llm_<app>_NNNN`) nên muốn dùng phải đổi tiền tố id.

## 11. v10 — BỊ LOẠI (vi phạm luật), 12/11

v10 thêm 146 spec do Claude viết **dựa trên transcript ASR của các mẫu public bị sai** (45/146 câu trùng Jaccard ≥ 0.5 với
transcript public, vài câu trùng 100%). Đó là gán nhãn public_test để train → vi phạm mục 3. Kết quả: val 39.70 / 55.87,
public 46.62 (hoà v9). **Không dùng `ft_v10_adapter` hay bất kỳ dữ liệu v10 nào**; đã xoá khỏi zip. Từ đây public chỉ dùng để
lấy điểm, không đọc input/transcript public để phân tích lỗi.
Kiểm tra nhiễm (Jaccard ≥ 0.5 với transcript public): `gen_*` 3/440, `llm_*` (v9) 8/320, `claude_*` 7/285 — mức ngẫu nhiên (câu ngắn chung chung).

## 12. v11 (12/11): v9 + 285 spec Claude viết từ catalog

`synth_specs_claude/claude_*.jsonl` (285 spec, id tiền tố `claude_`, generator `tools/synth_v9/`), viết 11/11 tối chỉ từ catalog
+ code `zaic_tools`. Notebook `colab/zaic_v11_colab.ipynb`: dữ liệu v9 + 285 spec này; synth_llm phải = 605, SFT = 4279.
Mốc: public 47.17. Thắng khi ≥ 48. Cùng notebook dùng cho bản cuối: `TRAIN_ALL=True`, `USE_CLAUDE` = True nếu v11 thắng, False nếu không.

## 13. v12 (12/11): v11 + 131 spec nhắm lỗi trên val

`synth_specs_c12/c12_*.jsonl` (131 spec, generator `tools/synth_v12/`), chỉ dựa trên report **val** của v9 + catalog:
`c12_time` (tính giờ: 'X giờ kém Y', 'N phút/tiếng nữa', buổi -> 24h, thứ X), `c12_enum` (climate mode, xe, payment, maps mode,
loại hoá đơn, vàng/xăng, priority, repeat, music/tv action, email delete/archive, hạng ghế, lý do trả hàng, mã ngôn ngữ),
`c12_cond` (15 cặp điều kiện đúng/sai, luôn đọc trước), `c12_hist` (giá trị đã có trong history -> làm luôn, không hỏi lại).
Đã loại 16 spec trùng câu chữ (Jaccard ≥ 0.5) với transcript public (danh sách `DROP` trong `tools/synth_v12/build.py`); còn 0 trùng.
Notebook `colab/zaic_v12_colab.ipynb`: synth_llm = 736, SFT = 4672; cell 5b đo val với transcript chuẩn (ASR gap).
Bản cuối: notebook v12, `TRAIN_ALL=True`, bật/tắt `USE_CLAUDE`, `USE_C12` theo kết quả v11/v12.

## 14. Lịch chốt (từ 12/11 chiều)

Đo trên v11: transcript chuẩn 52.66 / 69.93 so với ASR 40.90 / 55.68 → **ASR vẫn làm mất 12–14 điểm**, nên v8 (large-v3) được ưu tiên ngang v12.
Unit Colab: đã mua thêm 100 (A100 ≈ 6.7 unit/giờ).

| Khi | Việc | Thắng khi |
|---|---|---|
| 12/11 14:30 | v8 ASR large-v3 `HOLD_OUT=True`, **`ADAPTER = ft_v11_adapter`** (so trên nền v11) | WER < ~10.5% **và** public > 49.53 + 1 |
| 12/11 14:30 (song song) | v12 (`zaic_v12_colab.ipynb`) | public > 49.53 + 1 |
| ~18:30 | bản cuối: notebook v12 `TRAIN_ALL=True`, `USE_CLAUDE=True`, `USE_C12` = v12 thắng; nếu large-v3 thắng: v8 `HOLD_OUT=False` song song | — |
| 13/11 | Docker trên Vast theo `VAST_GUIDE.md` (Bước 5b nếu large-v3). Dựng **2 image**: (a) `ft_v11_adapter` + `asr_ft_v4` = bảo hiểm 49.53, (b) bản cuối. Nộp (a) trước, (b) sau — lần cuối được tính | `build_and_test.sh` đủ 3 PASS, `result1` nộp public khớp điểm Colab ±1 |
| 14–16/11 | buffer; 16/11 23:59 hạn nộp | |

Không dùng gì từ v10. Không đọc input/transcript public để phân tích lỗi.

## 15. KẾT QUẢ 12–13/11 VÀ CẤU HÌNH CUỐI

| Bản | LLM | ASR | val (unseen / seen) | Public |
|---|---|---|---|---|
| v11 | `ft_v11_adapter` (train_fit) | turbo `asr_ft_v4` | 40.90 / 55.68 | 49.53 |
| v12 | v11 + 131 spec c12 | turbo | 39.43 / 60.31 | 48.05 ✗ (bỏ c12) |
| v8 holdout | `ft_v11_adapter` | large-v3 holdout (WER 10.08%) | 44.53 / 59.10 | 49.86 |
| v8 all | `ft_v11_adapter` | **large-v3 all** `asr_v8_large_all` | — | 51.01 |
| **CUỐI** | **`ft_v11_all_adapter`** (TRAIN_ALL, SFT 5455, A100 153 phút) | **`asr_v8_large_all`** | (val trong train, không ý nghĩa) | **52.10** |

Tổng tham số: Qwen3-4B 4.02B + Whisper large-v3 1.55B = **5.57B < 6B**; LLM < 5B.
Docker: làm theo `VAST_GUIDE.md`, **bắt buộc Bước 5b** (`--gpu-mem 0.62`, đo max giây/mẫu).
Dự phòng nếu large-v3 không đạt thời gian/bộ nhớ trong Docker: `ft_v11_all_adapter` + `asr_ft_v4` (chưa đo public; ước 50–51),
cuối cùng là `ft_v11_adapter` + `asr_ft_v4` (49.53, đã chứng minh trên Colab).

## 16. Beam search cho ASR (13/11 tối, không cần train, chạy được trên L4)

Bản cuối giải mã Whisper **greedy**. Đã thêm `--beams` (`lifemate/asr.py`) và `--asr-beams` (`lifemate/infer.py`, Docker); mặc định 1 =
greedy nên mọi bản cũ tái hiện y nguyên. Notebook `colab/zaic_beam_colab.ipynb` (L4): đo WER val với `asr_v8_large_holdout`
ở beam 1/3/5 (greedy = 10.08%), nếu beam tốt nhất giảm ≥ 0.3 điểm WER thì chạy public với hệ thống cuối + beam đó.
Nếu public > 52.10: Docker thêm `"--asr-beams", "<B>"` vào `CMD`, và đo lại max giây/mẫu (beam chậm hơn greedy).
