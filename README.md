# ZAIC 2026 · LifeMate — đội DS@CocCocCoc

Agent nghe lệnh tiếng Việt (audio) → gọi chuỗi tool đúng trên môi trường mô phỏng. Hạng mục **SLM (< 6B)**.

> **Repo private, chỉ dành cho thành viên đội.** Luật cấm chia sẻ dữ liệu ra ngoài đội. Không commit dữ liệu BTC
> (`train/`, `public_test/`, audio, transcript public, file submission) — `.gitignore` đã chặn sẵn.

## Hệ thống tốt nhất — public **52.10** (13/11/2026)

```
audio ──► Whisper large-v3 fine-tune (1.55B) ──► transcript ──► Qwen3-4B-Instruct-2507 + LoRA (4.02B) ──► tool calls
          asr_v8_large_all                                       ft_v11_all_adapter
```
Tổng **5.57B** (< 6B; LLM < 5B). vLLM 0.33.0, greedy, tất định. Trọng số **không nằm trong git** (quá lớn) — lấy trên Drive của Thọ
(`MyDrive/ZAIC/`, xin quyền xem):

| Thư mục Drive | Là gì | Tái hiện bằng |
|---|---|---|
| `ft_v11_all_adapter/` | LoRA r32 của LLM cuối (~130MB) | `colab/zaic_final_llm_colab.ipynb` (A100, ~3.5 giờ) |
| `asr_v8_large_all/` | Whisper large-v3 fine-tune trên 5036 clip (~3GB) | `colab/zaic_final_asr_colab.ipynb` (A100, ~1 giờ) |
| `ft_v11_adapter/` | LLM cùng dữ liệu nhưng chỉ train trên `train_fit` (đo được val) | `colab/zaic_v11_colab.ipynb` |
| `asr_ft_v4/` | Whisper turbo fine-tune (bản cũ, nhẹ hơn) | — |

Notebook đọc code từ `MyDrive/ZAIC/lifemate_baseline.zip` = **zip của repo này** (`zip -r lifemate_baseline.zip . -x ".git/*"`).
Cell kiểm tra đầu notebook so file `VERSION` trong zip — đổi `VERSION` thì sửa chuỗi tương ứng trong notebook.

## Lịch sử điểm (public leaderboard)

| Bản | Thay đổi | val unseen / seen | Public |
|---|---|---|---|
| v4 | LoRA trên train_fit + Whisper turbo fine-tune | 35.06 / 54.11 | 44.46 (Docker 45.29) |
| v7 | + 440 spec synthetic sinh bằng code (`synth_specs/gen_*`) | 34.88 / 56.02 | 44.72 |
| v9 | + 320 spec viết tay (`synth_specs/llm_*`) | 39.52 / 58.31 | 47.17 |
| v10 | **BỊ LOẠI** — spec viết dựa trên transcript public (vi phạm luật) | — | (46.62, không dùng) |
| v11 | + 285 spec viết từ catalog (`synth_specs_claude/`) | 40.90 / 55.68 | 49.53 |
| v12 | + 131 spec vá lỗi cụ thể (đã xoá, xem commit `2a288e6`) | 39.43 / 60.31 | 48.05 ✗ |
| v8 | v11 + ASR **Whisper large-v3** (WER 11.47% → 10.08%), toàn bộ clip | 44.53 / 59.10 (holdout) | 51.01 |
| **cuối** | v8 + LLM train trên **toàn bộ** train (SFT 5455) | — | **52.10** |

Chi tiết mọi thí nghiệm, lý do thắng/thua, số liệu: **`HANDOFF.md`** (đọc mục 1–3 trước, rồi 10–15).

## Bài học quan trọng

- **Dữ liệu synthetic phủ rộng từng app/tool giúp nhiều nhất**: +2.45 (v9), +2.36 (v11), chưa bão hoà. Dữ liệu "vá lỗi cụ thể" (v12) thì **hại** (−1.5). Mẫu có đáp án `[]` rập khuôn làm model lười (v6).
- **ASR vẫn mất 8–11 điểm** so với transcript chuẩn (đo trên val). large-v3 > turbo.
- **Không bao giờ đọc input/transcript của public_test để làm dữ liệu train hay phân tích lỗi** (bài học v10). Phân tích lỗi trên `val_unseen`/`val_seen` (là dữ liệu train) thì hợp lệ.
- Val nhỏ (193/135 mẫu) và dao động ±1 giữa các lần chạy → chênh < 1 điểm coi như hoà; public là trọng tài.
- Docker: tắt torch.compile để tất định (xem `HANDOFF.md` mục 7).

## Hướng làm tiếp (xếp theo kỳ vọng)

1. **Thêm ~300 spec phủ rộng** cho các app/tool đang ít mẫu, cùng kiểu `synth_specs_claude/` (generator: `tools/synth_v9/`). Kiểm tra bằng simulator: `python -m lifemate.synth_build --root DATA --tools-from public_test --specs "<glob>" --split synth_x` (phải 0 reject). Train bằng `colab/zaic_final_llm_colab.ipynb` sau khi thêm glob.
2. **Audio TTS** cho từ vựng app mới (tên hàng, ga tàu, mã cổ phiếu) để fine-tune ASR.
3. **Cho LLM lập kế hoạch/suy nghĩ ngắn trước khi gọi tool** (phải giữ ≤ 30 s/mẫu trên A30).

## Cấu trúc

```
lifemate/            code agent: prompt, agent loop + guards, backends (vLLM/HF/oracle), ASR, SFT, LoRA, synth_build, infer (Docker)
scripts/score.py     scorer local (khớp luật chấm, 1545/1545 khi replay gold); scripts/detcheck.py so 2 lần chạy
tests/               test guards (không cần GPU)
synth_specs/         gen_*.jsonl (440, sinh bằng code) + llm_*.jsonl (320, viết tay)
synth_specs_claude/  285 spec viết từ catalog
tools/synth_v9/      generator của synth_specs_claude (mỗi kịch bản là code: lời nói, state, gold) — dùng để viết thêm spec
splits/              val_unseen (193, 6 app giữ lại) / val_seen (135) / train_fit (957)
colab/               zaic_final_llm_colab (LLM cuối), zaic_final_asr_colab (ASR cuối), zaic_v11_colab (LLM trên train_fit, đo được val)
docker/              Dockerfile (vllm/vllm-openai:v0.33.0), build_and_test.sh (3 PASS: đủ dòng, schema, tất định)
VAST_GUIDE.md        dựng + test + nộp Docker trên Vast.ai từng bước (Bước 5b cho large-v3)
HANDOFF.md           toàn bộ lịch sử, quyết định, số liệu
docs/BASELINE_DEV.md hướng dẫn chạy dev (oracle test, baseline, guards) và ghi chép v1–v7
```

Lịch sử (notebook v2–v12, log `results1–7`, dữ liệu v12 `synth_specs_c12`, các hướng dẫn cũ) đã xoá khỏi nhánh chính cho gọn,
vẫn lấy lại được từ commit đầu: `git checkout 2a288e6 -- <đường dẫn>`.

## Kiểm tra nhanh không cần GPU

```bash
python -m lifemate.run --root DATA --split train --backend oracle --oracle-mistakes --out runs/oracle --batch 16
python scripts/score.py --root DATA --split train --pred runs/oracle/submission.jsonl --by-tag   # phải 100.00
python tests/test_guards.py --root DATA                                                       # ALL PASS
```
`DATA` = thư mục chứa `train/` và `public_test/` của gói dữ liệu BTC (tải theo link trong `HANDOFF.md`, không commit).
