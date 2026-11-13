# LifeMate baseline agent (ZAIC 2026)

> Tài liệu dev từ giai đoạn v1–v7. Các notebook `notebooks/zaic_v*_colab.ipynb` nhắc tới bên dưới đã xoá khỏi nhánh chính;
> lấy lại bằng `git checkout 2a288e6 -- notebooks/`. Hệ thống hiện tại: xem `README.md` ở thư mục gốc.

Bước 1: agent loop dùng **transcript gold** (bỏ qua ASR) để đo trần của phần LLM. Không chứa dữ liệu của BTC.

```
lifemate/
  prompt.py    system prompt (quy ước của gold), bảng lịch tương đối, schema rút gọn, history -> chat turns, shrink()
  agent.py     vòng lặp 1 mẫu (generator, batch được) + guards
  backends.py  vllm / hf (greedy, seed cố định) / oracle (replay gold, test không cần GPU)
  run.py       chạy cả split -> submission.jsonl + traces.jsonl
  splits.py    tách val theo app giữ lại (đo zero-shot trên schema lạ)
  report.py    phân loại điểm bị mất theo nhóm lỗi
  priors.py    học từ gold mức dùng tham số tùy chọn / filter của read; quy tắc chung cho app lạ
  textnorm.py  số đọc bằng chữ -> chuỗi số (gợi ý cho model)
  sft_data.py  dữ liệu SFT đúng định dạng prompt lúc chạy + augment đổi tên app
  train_lora.py LoRA SFT tối giản (transformers + peft), loss chỉ trên lượt hiện tại, merge cho vLLM
  tokstats.py  đếm token thật bằng tokenizer của model
  asr.py       ASR mọi lượt user (Whisper/PhoWhisper, greedy) -> {audio_path: text}, kèm WER trên train
  merge.py     merge adapter LoRA vào model gốc
  asr_finetune.py fine-tune Whisper trên audio + transcript của train
scripts/score.py   scorer local (công thức của BTC)
tests/test_guards.py
splits/            val_unseen (193) / val_seen (135) / train_fit (957)
```

`--root` là thư mục chứa `train/` và `public_test/` (đúng cấu trúc gói dữ liệu của BTC).

## 0. Kiểm tra không cần GPU (phải ra 100.00 và ALL PASS)

```bash
python -m lifemate.run --root DATA --split train --backend oracle --oracle-mistakes --out runs/oracle --batch 16
python scripts/score.py --root DATA --split train --pred runs/oracle/submission.jsonl --by-tag
python tests/test_guards.py --root DATA
```

## 1. Baseline LLM trên train, transcript gold

```bash
pip install -r requirements.txt
M=Qwen/Qwen3-4B-Instruct-2507        # ứng viên; tự kiểm tra ngày release (< 26/10/2026) và license

# smoke test 5 mẫu, đọc traces để chắc chắn chat template + parser khớp
python -m lifemate.run --root DATA --split train --limit 5 --backend vllm --model $M --out runs/smoke
python -c "import json;[print(json.loads(l)['events'][:3]) for l in open('runs/smoke/traces.jsonl')]"

# số chính: zero-shot trên app giữ lại, và trên app đã thấy
for S in val_unseen val_seen; do
  python -m lifemate.run --root DATA --split train --ids splits/$S.txt --backend vllm --model $M --batch 32 --out runs/base_$S
  python -m lifemate.report --root DATA --split train --pred runs/base_$S/submission.jsonl --show 3 > runs/base_$S/report.txt
  head -15 runs/base_$S/report.txt
done
```

`--batch` chỉ để dev cho nhanh. Bản chạy cuối trong Docker để `--batch 1`, vì kernel batch có thể đổi output greedy, trong khi luật yêu cầu chạy lại phải cho kết quả giống nhau.

## Guards (không bao giờ ghi call thừa vào log)

| Guard | Lý do (số liệu train) |
|---|---|
| `env.validate` trước `env.call`; lỗi schema được báo lại cho model | `validate` không ghi log, call bị reject vẫn tính vào U |
| Bỏ key không có trong schema, ép `"500000"` -> int | key thừa làm call không khớp gold |
| Read giống hệt đã gọi trong turn -> trả lại kết quả cũ | gold: 0 mẫu đọc trùng |
| Read đã có kết quả trong history và còn "mới" -> trả kết quả history | gold không đọc lại read còn mới (0/1522); chỉ đọc lại read đã cũ, tức sau đó có write vào cùng app (4/838) |
| Write giống hệt được phép lặp | gold đổi 2 voucher = 2 call `redeem` giống nhau |
| ID chưa từng xuất hiện -> cảnh báo 1 lần, model gọi lại y hệt thì cho chạy | 1308/1309 ID trong gold đã xuất hiện trước đó |
| `ask_missing_info` phải nêu tool đã cài và đúng tên tham số; gọi xong thì dừng | 217/217 |
| Tự rút gọn prompt khi gần 16K (bỏ mô tả tham số, cắt history cũ) | prompt dài nhất khoảng 11K token trước các bước tool |

## v2 (sau baseline 27.1 / 34.0)

- Sửa bug: với `--batch > 1`, `time_budget` cắt 21 mẫu (thời gian chờ cả batch bị tính cho từng mẫu). Giờ chỉ áp khi `--batch 1`.
- `--priors`: bỏ tham số tùy chọn mà gold gần như không truyền (`repeat:"once"`, `priority:"normal"`, `note`, `label`...),
  bỏ filter của read dạng liệt kê. Gold mất ~1 điểm F1 do quy tắc này; áp lên output baseline: +1.8 / +4.2.
- Nhắc 1 lần khi model trả lời "Đã ..." mà chưa gọi tool ghi nào (baseline: đúng 24/30 lần).
- Gợi ý chuỗi số khi người dùng đọc số điện thoại bằng chữ (đúng 13/13 trên train).
- Fine-tune: `notebooks/zaic_v2_colab.ipynb`. Kết quả (L4, 5.5 giờ train): val_unseen 48.6 (49.2 không priors), val_seen 66.9.

## v3: ASR + file nộp public đầu tiên — `notebooks/zaic_v3_colab.ipynb`

## Thứ tự cải tiến gợi ý

1. Đọc `report.txt`: nhóm nào mất nhiều điểm nhất thì sửa prompt hoặc guard cho nhóm đó.
2. Fine-tune (LoRA) trên `train_fit` + dữ liệu synthetic có app/schema giả, chấm trên `val_unseen`.
3. ASR (bước 2): sinh `asr.json` `{audio_path: text}` rồi chạy `--transcripts asr.json`; so với kết quả dùng transcript gold để biết ASR làm mất bao nhiêu điểm.

## v3 → v4

- v3 (public LB 28.53): ASR làm mất một nửa điểm. val_unseen: transcript gold 49.0 / Whisper-turbo 25.3 / PhoWhisper 23.5;
  val_seen: 67.7 / 35.6 / 32.8. WER turbo 34.6%, khoảng 2% clip bị bịa câu ("Hãy subscribe cho kênh ...").
- v4 (`notebooks/zaic_v4_colab.ipynb`): fine-tune Whisper trên 5036 clip train (giữ lại clip của val), lọc câu bịa rồi giải mã lại.
- Chuẩn bị cho lần train LLM cuối: `sft_data --asr` (thêm bản transcript ASR có nhiễu), `train_lora --detach-prefix` (nhanh ~2.5-3x).

## v4 → v5

- v4 (public **44.46**): Whisper fine-tune 3 epoch trên 3936 clip train. WER 34.6% → **11.52%**, CER 8.74%.
  val_unseen 25.3 → **35.06**, val_seen 35.6 → **54.11**. Trần transcript gold: 49.0 / 67.7 → ASR vẫn lấy mất ~14 điểm.
- Lỗi còn lại chủ yếu là suy luận của LLM, không phải ASR: chọn sai tool ở app lạ (`reschedule_delivery` thay cho
  `schedule_pickup`), sai mã chu trình ("giặt nhanh" → `eco` thay vì `quick`), gọi thừa write.
- v5 (`notebooks/zaic_v5_colab.ipynb`): 2 Whisper fold cho transcript nhiễu thật (out-of-fold) → train LLM trên
  gold + đổi tên app + transcript nhiễu, cộng dữ liệu synthetic nếu có trong `MyDrive/ZAIC/synth_specs/`.
- Bộ lọc ASR bắt thêm lỗi lặp ký tự ("RONXXXXX..."); 0 câu gold bị bắt nhầm trên 5036 clip.

## v5 — thất bại, đã quay lại (public 44.46 → 40.49)

v5 đổi hai thứ cùng lúc so với v4; cả hai đều đáng ngờ, nên **không dùng adapter v5**:
- `--detach-prefix`: LoRA không nhận gradient từ phần prompt, nên học đọc schema kém đi. Loss giống hệt nhưng
  khả năng tổng quát hoá sang app lạ kém hơn. Cờ này vẫn còn trong code nhưng chỉ nên dùng để chạy thử nhanh.
- Bản transcript ASR: khi ASR nghe sai một con số mà đáp án vẫn là con số đúng, model học cách đoán thay vì hỏi.
  Trên public, `sys.ask_missing_info` tụt 92 → 62 và lỗi sai đối số tăng. `sft_data --asr-max-wer` (mặc định 0.25)
  nay bỏ các bản ASR nghe sai quá nhiều, nhưng cần A/B trước khi tin.
- Local: val_unseen 35.06 → 37.67 (tăng) nhưng val_seen 54.11 → 52.96 và public giảm 4 điểm. val 193/135 mẫu
  quá nhỏ để tin tưởng một mình; từ giờ lấy điểm public làm trọng tài.

## v6 — `notebooks/zaic_v6_colab.ipynb`

Quay lại đúng công thức v4, chỉ thêm **một** thay đổi: dữ liệu synthetic cho các app lạ. `TRAIN_ALL=True`
chỉ bật cho lần train cuối, sau khi v6 đã chứng minh vượt 44.46 trên public.

## Dữ liệu synthetic cho 11 app chỉ có ở public — `lifemate/synth_gen.py`

`python -m lifemate.synth_gen --out synth_specs --n 40` sinh 440 spec (40/app): state ngẫu nhiên, câu nói kiểu người thật
(số đọc bằng chữ, giờ "kém mười lăm", "thứ bảy tuần sau", từ địa phương, tự sửa lời), đáp án tính từ state theo quy ước
gold đo trên train. Tỉ lệ: làm ngay/đọc 80%, hỏi lại 11%, out-of-scope 9%; 57% có history; 36% nhiều app.
Kiểm tra: 440/440 qua simulator của BTC; oracle qua agent loop đạt 100; ràng buộc chống mơ hồ (giờ khởi hành
không trùng, đơn hàng được nhắc tới là duy nhất) được kiểm bằng máy. Chỉ dùng catalog + code `zaic_tools`, không đọc
`public_test.jsonl` hay `public_test_environment/`.

Rủi ro còn lại: quy ước của gold cho app mới là suy luận từ train (ví dụ chuỗi `query` của tool tìm kiếm, có truyền
`end` hay không). Phần ghi (ID, số lượng, giờ) tính chính xác từ state nên không bị ảnh hưởng; phần đọc chỉ ảnh hưởng F1.

## v6 — public 43.31 (thấp hơn v4 44.46) → v7

v6 = công thức v4 + 440 mẫu synthetic. Trên public: `ask_missing_info` 92 → 43, trả rỗng 64 → 106 (trên mẫu có app mới:
40 → 72). Trên val: "không gọi tool trong khi gold có hành động" 17 → 27 (unseen) và 5 → 19 (seen); ví dụ model trả `[]`
cho "Chạy máy rửa bát chế độ thường giúp em nha". Nguyên nhân: các mẫu synthetic đáp án `[]` quá rập khuôn ("à thôi không
mua nữa", "nếu … không thì thôi"), model học thành phản xạ. Phần synthetic có hành động thì giúp: sai đối số trên
val_unseen 49 → 39, dù các app của val_unseen không có trong synthetic.

v7 (`notebooks/zaic_v7_colab.ipynb`): như v6, thêm `sft_data --drop-empty` cho synthetic (398/440 mẫu).

## v7 — public 44.72 (v4 44.46): hoà

val 34.88 / 56.02 (v4 35.06 / 54.11). Trên public, v7 đổi output của 223/410 mẫu có app mới nhưng điểm gần như không
đổi; chênh lệch nằm trong mức dao động giữa các lần chạy (Docker v4 ra 45.29 so với 44.46 trên Colab).

## Docker — tất định (11/11)

torch.compile của vLLM đo tốc độ để chọn kernel lúc khởi động; 1/4 lần chạy chọn khác và 49/634 output đổi theo.
`infer.py` nay mặc định `compilation_config={"mode": 0, "cudagraph_mode": "FULL"}` (không compile, giữ CUDA graph).
Docker v4: public **45.29**, 2 lần chạy giống hệt, trung bình 1.8 s/mẫu, chậm nhất 12.4 s (RTX 4090).
Công cụ: `docker/det_test.sh`, `docker/det_try.sh`, `scripts/detcheck.py`, `infer.py --trace`.

## Cuối cùng

- `zaic_v8_asr_colab.ipynb`: Whisper large-v3 (1.55B; tổng 5.57B < 6B) thay cho turbo, LLM giữ adapter v4 → so ASR sạch.
- `zaic_final_llm_colab.ipynb`: TRAIN_ALL + synthetic (công thức v7) → `ft_final_adapter`.
