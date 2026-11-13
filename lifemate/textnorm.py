"""Spoken digit sequences -> digit strings ("không chín không một, hai ba bốn" -> "09012..."), appended to the user
message as a hint. A small LLM often drops or doubles digits when converting long spoken numbers itself."""
from __future__ import annotations

import re
import unicodedata

DIGITS = {"không": "0", "một": "1", "hai": "2", "ba": "3", "bốn": "4", "tư": "4", "năm": "5", "lăm": "5",
          "sáu": "6", "bảy": "7", "bẩy": "7", "tám": "8", "chín": "9", "khồng": "0"}
_WORD = re.compile(r"[^\W\d_]+|\d+|[,.;:!?…-]")


def spoken_digit_runs(text: str, min_len: int = 7) -> list[str]:
    """Runs of single-digit words (commas/pauses allowed inside, literal digits too) with >= min_len digits."""
    toks = _WORD.findall(unicodedata.normalize("NFC", text.lower()))
    runs, cur, n_words = [], "", 0
    for t in toks + ["<end>"]:
        if t in DIGITS:
            cur += DIGITS[t]
            n_words += 1
        elif t.isdigit() and cur:
            cur += t
        elif t in ",-" and cur:
            continue
        else:
            if len(cur) >= min_len and n_words >= 3:
                runs.append(cur)
            cur, n_words = "", 0
    return runs


def with_number_hint(text: str) -> str:
    runs = spoken_digit_runs(text)
    if not runs:
        return text
    return f"{text}\n[chuỗi số người dùng đọc: {', '.join(runs)}]"
