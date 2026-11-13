"""Agent loop for one sample, written as a generator so a runner can batch LLM calls across samples.

    gen = run_agent(item, env, tools_catalog, transcribe)
    prompt = next(gen)                # (messages, tools) the LLM must complete
    prompt = gen.send(llm_text)       # ... repeat until StopIteration; StopIteration.value = trace dict

Guards (each costs a re-prompt, never a logged call — env.validate() does not log, env.call() does):
  * malformed output              -> feedback, retry
  * schema error (env.validate)   -> feedback with the error, retry
  * unknown argument keys         -> dropped (an extra key breaks the exact-match scorer); int strings cast to int
  * identical call already made this turn, or identical READ already in history with results -> not executed,
    the earlier result is returned to the model
  * ID argument that never appeared in anything the agent has seen -> feedback once; executed if the model insists
  * sys.ask_missing_info executed -> stop
  * step / generation / time limits
"""
from __future__ import annotations

import json
import re
import time

from . import priors as P
from .prompt import build_messages, tools_for_sample, visible_text

TOOL_CALL_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.S)
MAX_EXEC = 10          # gold max is 6 calls
MAX_GEN = 16
MAX_RETRY_PER_STEP = 2
TIME_BUDGET_S = 24.0   # 30 s per sample incl. ASR; keep margin
# final answer that claims an action ("Đã khoá cửa...") while no write ran this turn: 24/30 such cases in the
# first baseline really were missing writes -> one nudge
CLAIM_RE = re.compile(r"(^|[\s,.])(đã|Đã)\s")


def _dump(x) -> str:
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


def call_key(name: str, args: dict) -> str:
    return name + _dump(dict(sorted((args or {}).items())))


def parse_calls(text: str) -> tuple[list[dict], str | None]:
    """Qwen/Hermes style <tool_call>{"name":..,"arguments":{..}}</tool_call>; several blocks allowed.
    Returns (calls, error). No block at all -> ([], None): the model is done."""
    blocks = TOOL_CALL_RE.findall(text)
    if not blocks and "<tool_call>" in text:  # unterminated block (hit max_tokens)
        blocks = [text.split("<tool_call>", 1)[1]]
    calls = []
    for b in blocks:
        try:
            obj = json.loads(b)
        except json.JSONDecodeError:
            # tolerate trailing junk after the JSON object
            try:
                obj, _ = json.JSONDecoder().raw_decode(b)
            except json.JSONDecodeError as e:
                return [], f"JSON không hợp lệ trong <tool_call>: {e}"
        if not isinstance(obj, dict) or "name" not in obj:
            return [], "mỗi <tool_call> phải là {\"name\": ..., \"arguments\": {...}}"
        args = obj.get("arguments", obj.get("parameters", {}))
        if isinstance(args, str):
            try:
                args = json.loads(args) if args.strip() else {}
            except json.JSONDecodeError:
                return [], "arguments phải là object JSON"
        if not isinstance(args, dict):
            return [], "arguments phải là object JSON"
        calls.append({"name": str(obj["name"]), "arguments": args})
    return calls, None


def clean_args(name: str, args: dict, catalog_tools: dict) -> dict:
    known = name in catalog_tools
    spec = (catalog_tools.get(name) or {}).get("parameters") or {}
    props = spec.get("properties") or {}
    out = {}
    for k, v in args.items():
        if known and k not in props:
            continue  # unknown key: schema ignores it but the scorer would count the call as unmatched
        if v is None or v == "" or v == [] or v == {}:
            continue  # empty optional value = not given
        t = (props.get(k) or {}).get("type")
        if t == "integer" and isinstance(v, str) and re.fullmatch(r"-?\d+", v.replace(".", "").replace(",", "")):
            v = int(v.replace(".", "").replace(",", ""))
        elif t == "integer" and isinstance(v, float) and v.is_integer():
            v = int(v)
        elif t == "string" and isinstance(v, (int, float)) and not isinstance(v, bool):
            v = str(v)
        elif t == "array" and isinstance(v, str):
            v = [v]
        out[k] = v
    return out


def id_args(name: str, args: dict, catalog_tools: dict) -> list[tuple[str, str]]:
    props = ((catalog_tools.get(name) or {}).get("parameters") or {}).get("properties") or {}
    out = []
    for k, v in args.items():
        p = props.get(k) or {}
        if p.get("x-ref") or k.endswith("_id"):
            for x in (v if isinstance(v, list) else [v]):
                if isinstance(x, str):
                    out.append((k, x))
    return out


def history_reads(item: dict, catalog_tools: dict) -> dict[str, dict]:
    """key -> result of FRESH read calls made in history (with stored results). A read is stale once a later history
    call wrote to the same app; gold re-reads only stale reads (train: 4/838 stale re-read, 0/1522 fresh re-read)."""
    out = {}
    for h in item.get("history", []):
        res = h.get("tool_results") or []
        for i, c in enumerate(h.get("tool_calls") or []):
            kind = (catalog_tools.get(c["name"]) or {}).get("kind")
            app = c["name"].split(".", 1)[0]
            if kind == "write":
                for k in [k for k in out if k.split(".", 1)[0] == app]:
                    del out[k]
            elif kind == "read" and i < len(res):
                out[call_key(c["name"], c.get("arguments") or {})] = res[i]
    return out


def run_agent(item: dict, env, catalog_tools: dict, transcribe, time_budget: float = TIME_BUDGET_S,
              priors: dict | None = None, nudge: bool = True):
    t0 = time.time()
    tools = tools_for_sample(item, catalog_tools)
    messages = build_messages(item, transcribe)
    seen = visible_text(item) + _dump(messages[-1]["content"])
    hist_reads = history_reads(item, catalog_tools)
    installed = {n for a in item["context"]["installed_apps"].values() for n in a.get("tools", [])}
    done_calls: dict[str, dict] = {}
    warned_ids: set = set()
    trace = {"id": item["id"], "events": []}
    n_exec = n_gen = retries = 0
    n_write = 0
    nudged = False
    user_text = " ".join(m["content"] for m in messages if m["role"] == "user")

    def feedback(text: str):
        messages.append({"role": "tool", "content": text})

    while n_gen < MAX_GEN and n_exec < MAX_EXEC:
        if time.time() - t0 > time_budget:
            trace["events"].append({"stop": "time_budget"})
            break
        out = yield messages, tools
        n_gen += 1
        trace["events"].append({"gen": out})
        calls, err = parse_calls(out)
        if err:
            if retries >= MAX_RETRY_PER_STEP:
                trace["events"].append({"stop": "parse_error"})
                break
            retries += 1
            messages.append({"role": "assistant", "content": out})
            feedback(f"LỖI: {err}. Hãy gọi lại đúng định dạng.")
            continue
        if not calls:
            messages.append({"role": "assistant", "content": out})
            if nudge and not nudged and n_write == 0 and CLAIM_RE.search(out):
                nudged = True
                messages.append({"role": "user", "content": "[hệ thống] Bạn vừa trả lời là đã làm, nhưng trong lượt này chưa có "
                                 "tool ghi nào được gọi nên chưa có gì thay đổi. Nếu yêu cầu cần thay đổi dữ liệu, hãy gọi tool ngay. "
                                 "Nếu yêu cầu chỉ cần đọc, cần hỏi lại hoặc không cần làm gì, trả lời đúng một từ: XONG."})
                trace["events"].append({"nudge": True})
                continue
            break  # final answer, no more tools

        messages.append({"role": "assistant", "content": "", "tool_calls": [
            {"type": "function", "function": {"name": c["name"], "arguments": c["arguments"]}} for c in calls]})
        stop = False
        had_error = False
        for c in calls:
            name = c["name"]
            args = clean_args(name, c["arguments"], catalog_tools)
            if name in catalog_tools and name != "sys.ask_missing_info":
                args, dropped = P.apply(name, args, catalog_tools[name], priors, user_text + seen)
                if dropped:
                    trace["events"].append({"drop_args": [name, dropped]})
            key = call_key(name, args)
            # duplicate guards
            is_read = (catalog_tools.get(name) or {}).get("kind") == "read"
            if is_read and key in done_calls:  # identical writes are legitimate (gold redeems 2 vouchers = 2 calls)
                feedback(_dump({"note": "tool này đã được gọi với cùng tham số, dùng lại kết quả", **done_calls[key]}))
                trace["events"].append({"skip_dup": key})
                continue
            if is_read and key in hist_reads:
                feedback(_dump({"note": "đã có kết quả này ở lượt trước, dùng lại", **hist_reads[key]}))
                trace["events"].append({"skip_hist": key})
                continue
            # schema guard
            v = env.validate(name, args)
            if not v["ok"]:
                had_error = True
                feedback(f"LỖI (chưa thực hiện): {v['error']}. Sửa tham số rồi gọi lại, hoặc gọi sys.ask_missing_info nếu thiếu thông tin.")
                trace["events"].append({"reject": key, "error": v["error"]})
                continue
            # ask_missing must name an installed tool and real parameter names of it (train: 217/217)
            if name == "sys.ask_missing_info":
                tn, ps = args.get("tool_name"), args.get("params") or []
                tprops = ((catalog_tools.get(tn) or {}).get("parameters") or {}).get("properties") or {}
                if tn not in installed or any(p not in tprops for p in ps):
                    had_error = True
                    feedback(f"LỖI (chưa thực hiện): tool_name phải là một tool đã cài và params phải là tên tham số của tool đó "
                             f"(tham số của {tn}: {list(tprops)}).")
                    trace["events"].append({"reject_ask": key})
                    continue
            # hallucinated-ID guard
            bad = [(k, x) for k, x in id_args(name, args, catalog_tools) if x not in seen and (key, k, x) not in warned_ids]
            if bad and name != "sys.ask_missing_info":
                had_error = True
                for k, x in bad:
                    warned_ids.add((key, k, x))
                feedback(f"CẢNH BÁO (chưa thực hiện): {', '.join(f'{k}={x!r}' for k, x in bad)} chưa xuất hiện trong dữ liệu đã đọc. "
                         "Hãy gọi tool đọc để lấy ID đúng; nếu chắc chắn thì gọi lại y hệt.")
                trace["events"].append({"warn_id": key})
                continue
            res = env.call(name, args)
            n_exec += 1
            n_write += (catalog_tools.get(name) or {}).get("kind") == "write"
            done_calls[key] = res
            seen += _dump(res)
            feedback(_dump(res))
            trace["events"].append({"call": {"name": name, "arguments": args}})
            if name == "sys.ask_missing_info":
                stop = True
                break
        if stop:
            break
        if had_error:
            retries += 1
            if retries > MAX_RETRY_PER_STEP + 2:
                trace["events"].append({"stop": "too_many_errors"})
                break
        else:
            retries = 0
    trace["n_gen"] = n_gen
    trace["seconds"] = round(time.time() - t0, 3)
    return trace
