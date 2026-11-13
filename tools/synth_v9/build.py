"""Dump every app's scenarios to synth_specs_claude/llm_<app>.jsonl and verify them with lifemate.synth_build."""
from __future__ import annotations

import importlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import dump  # noqa: E402

APPS = sys.argv[1:] or ["ecommerce", "grocery", "pantry", "recipes", "habit_tracker", "stocks", "event_tickets",
                        "train_bus_tickets", "public_transit", "parking", "translator"]
OUT = os.path.join(os.path.dirname(__file__), "synth_specs_claude")
os.makedirs(OUT, exist_ok=True)
total = 0
for app in APPS:
    mod = importlib.import_module(f"app_{app}")
    n = dump(mod.build(), os.path.join(OUT, f"claude_{app}.jsonl"))
    print(f"{app}: {n} specs")
    total += n
print("total", total)
