"""Minimal LoRA SFT (transformers + peft, no trl) on lifemate.sft_data examples.

Loss only on the assistant messages of the current turn (after the last user message), found by rendering the chat
template on message prefixes and mapping character spans to tokens. The rendered text is exactly what the agent
sends to vLLM at inference, so training and inference prompts match token for token.

python -m lifemate.train_lora --data sft_fit.jsonl --model Qwen/Qwen3-4B-Instruct-2507 --out ft/fit --epochs 1
  -> ft/fit/adapter (LoRA) and ft/fit/merged (full bf16 model for vLLM)
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

from .backends import _template_messages, set_seeds


def render(tok, messages, tools, gen_prompt):
    return tok.apply_chat_template(_template_messages(messages), tools=tools, tokenize=False, add_generation_prompt=gen_prompt)


def encode(tok, ex: dict, max_len: int):
    """-> (input_ids, labels) or None. Assistant messages from index n_prompt on are supervised."""
    msgs, tools, n0 = ex["messages"], ex["tools"], ex["n_prompt"]
    full = render(tok, msgs, tools, False)
    spans = []
    for j in range(n0, len(msgs)):
        if msgs[j]["role"] != "assistant":
            continue
        pre = render(tok, msgs[:j], tools, True)
        upto = render(tok, msgs[: j + 1], tools, False)
        if not (upto.startswith(pre) and full.startswith(upto)):
            return None  # template is not prefix-stable for this conversation
        spans.append((len(pre), len(upto)))
    enc = tok(full, return_offsets_mapping=True, add_special_tokens=False)
    ids = enc["input_ids"]
    if len(ids) > max_len:
        return None
    labels = [-100] * len(ids)
    for i, (a, b) in enumerate(enc["offset_mapping"]):
        if any(s <= a < e for s, e in spans):
            labels[i] = ids[i]
    if all(x == -100 for x in labels):
        return None
    return ids, labels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--rank", type=int, default=32)
    ap.add_argument("--alpha", type=int, default=64)
    ap.add_argument("--grad-accum", type=int, default=16)
    ap.add_argument("--max-len", type=int, default=12288)
    ap.add_argument("--no-merge", action="store_true")
    ap.add_argument("--detach-prefix", action="store_true",
                    help="run the prompt part without grad (KV cache), backprop only through the current turn: "
                         "~2-3x faster; LoRA still shapes the prompt's KV, but gets no gradient from it")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    set_seeds(a.seed)
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    log = open(out / "train_log.txt", "a")

    def say(s):
        print(s, flush=True)
        log.write(s + "\n")
        log.flush()

    tok = AutoTokenizer.from_pretrained(a.model)
    exs = [json.loads(l) for l in open(a.data, encoding="utf-8")]
    data, skipped = [], 0
    for ex in exs:
        e = encode(tok, ex, a.max_len)
        if e is None:
            skipped += 1
        else:
            data.append(e)
    n_tok = sum(len(x[0]) for x in data)
    n_lab = sum(sum(t != -100 for t in x[1]) for x in data)
    say(f"examples {len(data)} (skipped {skipped}) tokens {n_tok} supervised {n_lab}")
    assert len(data) > 0.9 * len(exs), "too many examples skipped: chat template not prefix-stable?"

    dev = "cuda" if torch.cuda.is_available() else "cpu"  # cpu only for the plumbing test with a tiny model
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, device_map={"": dev},
                                                 attn_implementation="sdpa")
    if a.detach_prefix:
        # no checkpointing: the suffix is short, and recomputation would append to the KV cache twice
        model.config.use_cache = True
    else:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.enable_input_require_grads()
        model.config.use_cache = False
    cfg = LoraConfig(r=a.rank, lora_alpha=a.alpha, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(model, cfg)
    model.print_trainable_parameters()

    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0, betas=(0.9, 0.999))
    steps_total = math.ceil(len(data) * a.epochs / a.grad_accum)
    warm = max(1, int(0.03 * steps_total))

    def lr_at(s):
        if s < warm:
            return a.lr * (s + 1) / warm
        return a.lr * 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, steps_total - warm)))

    rng = random.Random(a.seed)
    order = []
    while len(order) < len(data) * a.epochs:
        o = list(range(len(data)))
        rng.shuffle(o)
        order += o
    order = order[: int(len(data) * a.epochs)]
    model.train()
    t0, step, acc_loss, acc_n = time.time(), 0, 0.0, 0
    opt.zero_grad(set_to_none=True)
    for i, idx in enumerate(order):
        ids, labels = data[idx]
        x = torch.tensor([ids], device=dev)
        # supervised tokens sit at the end (current turn): compute logits only from just before the first one,
        # instead of a [12k x 151k] fp32 logit tensor
        first = next(k for k, t in enumerate(labels) if t != -100)
        keep = len(ids) - first + 1
        if a.detach_prefix:
            cut = first - 1
            with torch.no_grad():
                pkv = model(input_ids=x[:, :cut], use_cache=True, logits_to_keep=1).past_key_values
            logits = model(input_ids=x[:, cut:], past_key_values=pkv, use_cache=True).logits[0]
        else:
            try:
                logits = model(input_ids=x, logits_to_keep=keep).logits[0]
            except TypeError:  # older transformers: no logits_to_keep
                logits = model(input_ids=x).logits[0, -keep:]
        tgt = torch.tensor(labels[len(ids) - keep + 1:], device=dev)
        # mean loss over supervised tokens of this example; examples weighted equally
        loss = torch.nn.functional.cross_entropy(logits[:-1].float(), tgt, ignore_index=-100) / a.grad_accum
        loss.backward()
        acc_loss += loss.item() * a.grad_accum
        acc_n += 1
        if (i + 1) % a.grad_accum == 0 or i == len(order) - 1:
            for g in opt.param_groups:
                g["lr"] = lr_at(step)
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            opt.zero_grad(set_to_none=True)
            step += 1
            if step % 5 == 0 or step == steps_total:
                el = time.time() - t0
                say(f"step {step}/{steps_total} loss {acc_loss / acc_n:.4f} lr {lr_at(step):.2e} "
                    f"elapsed {el / 60:.1f}m eta {el / step * (steps_total - step) / 60:.1f}m")
                acc_loss, acc_n = 0.0, 0
    model.save_pretrained(out / "adapter")
    tok.save_pretrained(out / "adapter")
    say(f"saved adapter -> {out / 'adapter'}  ({(time.time() - t0) / 60:.1f} min)")
    if not a.no_merge:
        merged = model.merge_and_unload()
        merged.config.use_cache = True
        merged.save_pretrained(out / "merged", safe_serialization=True)
        tok.save_pretrained(out / "merged")
        say(f"saved merged model -> {out / 'merged'}")


if __name__ == "__main__":
    main()
