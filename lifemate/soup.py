"""Model soup cho các adapter LoRA cùng gốc: W = W_base + sum_i w_i * (alpha_i / r_i) * B_i @ A_i.

Trung bình CHÍNH XÁC trên delta (không trung bình A và B riêng — sai về toán), xử lý từng module một để vừa GPU 24GB.
Kết quả là một model đã merge, dùng y như output của lifemate.merge (vLLM / Docker không đổi gì).

python -m lifemate.soup --base Qwen/Qwen3-4B-Instruct-2507 \
    --adapters /content/drive/MyDrive/ZAIC/ft_v11_all_adapter /content/drive/MyDrive/ZAIC/ft_v11_adapter \
    --weights 0.5 0.5 --out /content/soup/merged
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LORA_RE = re.compile(r"^(?:base_model\.model\.)?(.+)\.lora_([AB])(?:\.default)?\.weight$")


def load_adapter(path: str):
    """-> (scale, {module_name: (A, B)}) ; module_name khớp tên tham số của model gốc, bỏ hậu tố '.weight'."""
    from safetensors.torch import load_file
    p = Path(path)
    cfg = json.load(open(p / "adapter_config.json"))
    r, alpha = cfg["r"], cfg["lora_alpha"]
    if cfg.get("use_rslora"):
        scale = alpha / (r ** 0.5)
    else:
        scale = alpha / r
    sd = load_file(str(p / "adapter_model.safetensors"))
    pairs: dict[str, dict[str, object]] = {}
    other = []
    for k, v in sd.items():
        m = LORA_RE.match(k)
        if not m:
            other.append(k)
            continue
        pairs.setdefault(m.group(1), {})[m.group(2)] = v
    if other:
        raise SystemExit(f"{path}: adapter có tham số ngoài LoRA (modules_to_save?) — soup không hỗ trợ: {other[:5]}")
    bad = [k for k, d in pairs.items() if set(d) != {"A", "B"}]
    if bad:
        raise SystemExit(f"{path}: thiếu cặp A/B ở {bad[:5]}")
    return scale, {k: (d["A"], d["B"]) for k, d in pairs.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapters", nargs="+", required=True)
    ap.add_argument("--weights", nargs="+", type=float, help="mặc định chia đều; được chuẩn hoá để tổng = 1")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default=None)
    a = ap.parse_args()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    w = a.weights or [1.0] * len(a.adapters)
    if len(w) != len(a.adapters):
        raise SystemExit("--weights phải cùng số lượng với --adapters")
    s = sum(w)
    w = [x / s for x in w]
    dev = a.device or ("cuda" if torch.cuda.is_available() else "cpu")
    base = AutoModelForCausalLM.from_pretrained(a.base, dtype=torch.bfloat16, device_map={"": dev})
    params = dict(base.named_parameters())

    ads = [load_adapter(p) for p in a.adapters]
    keys = set(ads[0][1])
    for p, (_, mods) in zip(a.adapters, ads):
        if set(mods) != keys:
            raise SystemExit(f"{p}: tập module khác adapter đầu tiên — không trộn được")
    n = 0
    with torch.no_grad():
        for name in sorted(keys):
            pname = name + ".weight"
            if pname not in params:
                raise SystemExit(f"không tìm thấy {pname} trong model gốc")
            W = params[pname]
            delta = torch.zeros(W.shape, dtype=torch.float32, device=dev)
            for wi, (scale, mods) in zip(w, ads):
                A, B = mods[name]
                delta += (wi * scale) * (B.to(dev, torch.float32) @ A.to(dev, torch.float32))
            W.copy_((W.to(torch.float32) + delta).to(W.dtype))
            n += 1
    base.save_pretrained(a.out, safe_serialization=True)
    AutoTokenizer.from_pretrained(a.base).save_pretrained(a.out)
    json.dump({"base": a.base, "adapters": a.adapters, "weights": w, "modules": n},
              open(Path(a.out) / "soup.json", "w"), ensure_ascii=False, indent=1)
    print(f"soup {len(ads)} adapter, weights {[round(x, 3) for x in w]}, {n} module -> {a.out}")


if __name__ == "__main__":
    main()
