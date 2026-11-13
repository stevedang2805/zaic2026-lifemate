"""Dump every app's scenarios to synth_specs_c12/llm_<app>.jsonl and verify them with lifemate.synth_build."""
from __future__ import annotations

import importlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import dump  # noqa: E402

APPS = sys.argv[1:] or ["time", "enum", "cond", "hist"]
OUT = os.path.join(os.path.dirname(__file__), "synth_specs_c12")
os.makedirs(OUT, exist_ok=True)
total = 0
for app in APPS:
    mod = importlib.import_module(f"app_{app}")
    n = dump(mod.build(), os.path.join(OUT, f"c12_{app}.jsonl"))
    print(f"{app}: {n} specs")
    total += n
print("total", total)

# loại các spec trùng câu chữ với transcript public (Jaccard >= 0.5) — danh sách cố định, xem HANDOFF mục 13
DROP = {"c12_enum_0001", "c12_enum_0003", "c12_enum_0005", "c12_enum_0022", "c12_enum_0024", "c12_enum_0025", "c12_enum_0026",
        "c12_enum_0031", "c12_enum_0032", "c12_enum_0033", "c12_enum_0034", "c12_enum_0042", "c12_hist_0003", "c12_time_0024",
        "c12_time_0025", "c12_time_0027"}
import glob, json
kept = 0
for p in glob.glob(os.path.join(OUT, "*.jsonl")):
    rows = [l for l in open(p, encoding="utf-8") if json.loads(l)["id"] not in DROP]
    open(p, "w", encoding="utf-8").writelines(rows); kept += len(rows)
print("after drop:", kept)
