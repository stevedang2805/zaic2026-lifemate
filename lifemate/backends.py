"""LLM backends. Each exposes generate_batch(list[(messages, tools)], sids) -> list[str], greedy decoding only.

  vllm   : fastest; prefix caching makes the multi-step loop cheap (system prompt + schema are reused)
  hf     : plain transformers, no extra dependency
  oracle : replays label.tool_calls of train samples — tests the loop / guards / scorer without a GPU
"""
from __future__ import annotations

import json
import os
import random


def set_seeds(seed: int = 0):
    random.seed(seed)
    os.environ.setdefault("PYTHONHASHSEED", str(seed))
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def _template_messages(messages: list[dict]) -> list[dict]:
    """Chat templates (Qwen, Llama) expect tool_call arguments as dicts and tool messages as strings."""
    out = []
    for m in messages:
        m = dict(m)
        if m.get("tool_calls"):
            m["tool_calls"] = [{"type": "function", "function": {"name": c["function"]["name"],
                                                                 "arguments": c["function"]["arguments"]}} for c in m["tool_calls"]]
        out.append(m)
    return out


class _TemplateMixin:
    tokenizer = None
    chat_kwargs: dict = {}

    def render(self, messages, tools) -> str:
        return self.tokenizer.apply_chat_template(_template_messages(messages), tools=tools, tokenize=False,
                                                  add_generation_prompt=True, **self.chat_kwargs)

    def n_tokens(self, messages, tools) -> int:
        return len(self.tokenizer(self.render(messages, tools))["input_ids"])

    def render_fit(self, messages, tools, limit: int) -> str:
        """Render, shrinking the prompt (see prompt.shrink) until it leaves room for the answer."""
        from .prompt import shrink
        text = self.render(messages, tools)
        level = 0
        while len(self.tokenizer(text)["input_ids"]) > limit and level < 3:
            level += 1
            text = self.render(*shrink(messages, tools, level))
        return text


class VLLMBackend(_TemplateMixin):
    def __init__(self, model: str, max_model_len: int = 16384, max_new_tokens: int = 384, gpu_mem: float = 0.85,
                 dtype: str = "bfloat16", enable_thinking: bool = False, seed: int = 0, prefix_caching: bool = True,
                 **kw):
        from vllm import LLM, SamplingParams
        self.llm = LLM(model=model, max_model_len=max_model_len, gpu_memory_utilization=gpu_mem, dtype=dtype,
                       enable_prefix_caching=prefix_caching, seed=seed, **kw)
        self.tokenizer = self.llm.get_tokenizer()
        self.params = SamplingParams(temperature=0.0, top_p=1.0, max_tokens=max_new_tokens, seed=seed)
        self.chat_kwargs = {"enable_thinking": enable_thinking}
        self.max_model_len = max_model_len

    def generate_batch(self, prompts, sids=None):
        limit = self.max_model_len - self.params.max_tokens
        texts = [self.render_fit(m, t, limit) for m, t in prompts]
        outs = self.llm.generate(texts, self.params, use_tqdm=False)
        return [o.outputs[0].text for o in outs]


class HFBackend(_TemplateMixin):
    def __init__(self, model: str, max_new_tokens: int = 384, dtype: str = "bfloat16", enable_thinking: bool = False,
                 max_model_len: int = 16384, **kw):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.tokenizer.padding_side = "left"
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(model, dtype=getattr(torch, dtype), device_map="auto", **kw).eval()
        self.max_new_tokens = max_new_tokens
        self.max_model_len = max_model_len
        self.chat_kwargs = {"enable_thinking": enable_thinking}

    def generate_batch(self, prompts, sids=None):
        texts = [self.render_fit(m, t, self.max_model_len - self.max_new_tokens) for m, t in prompts]
        enc = self.tokenizer(texts, return_tensors="pt", padding=True, add_special_tokens=False).to(self.model.device)
        with self.torch.no_grad():
            out = self.model.generate(**enc, max_new_tokens=self.max_new_tokens, do_sample=False,
                                      pad_token_id=self.tokenizer.pad_token_id)
        gen = out[:, enc["input_ids"].shape[1]:]
        return [self.tokenizer.decode(g, skip_special_tokens=True) for g in gen]


class OracleBackend:
    """Emits the gold calls of a train sample one per step (optionally with injected mistakes, to exercise guards)."""

    def __init__(self, rows: dict, mistakes: bool = False):
        self.rows = rows
        self.mistakes = mistakes
        self.pos: dict[str, int] = {}

    def generate_batch(self, prompts, sids):
        return [self._one(sid, m) for (m, _), sid in zip(prompts, sids)]

    def _one(self, sid, messages):
        gold = self.rows[sid]["label"]["tool_calls"]
        i = self.pos.get(sid, 0)
        last = messages[-1]
        # after a guard feedback, the oracle simply re-emits the correct call
        if last["role"] == "tool" and last["content"].startswith(("LỖI", "CẢNH BÁO")):
            i -= 1
        if i >= len(gold):
            return "Đã xong."
        c = gold[i]
        self.pos[sid] = i + 1
        if self.mistakes and i == 0 and "LỖI" not in last.get("content", ""):
            # first emission: a wrong-typed / extra-key version of the gold call (must be fixed or cleaned by guards)
            bad = dict(c["arguments"], _junk="x")
            return f"<tool_call>{json.dumps({'name': c['name'], 'arguments': bad}, ensure_ascii=False)}</tool_call>"
        return f"<tool_call>{json.dumps({'name': c['name'], 'arguments': c['arguments']}, ensure_ascii=False)}</tool_call>"


def make_backend(name: str, model: str | None = None, rows: dict | None = None, **kw):
    if name == "vllm":
        return VLLMBackend(model, **kw)
    if name == "hf":
        return HFBackend(model, **kw)
    if name == "oracle":
        return OracleBackend(rows, **kw)
    raise ValueError(name)
