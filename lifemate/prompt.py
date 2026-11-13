"""Prompt building: compact tool schemas, a relative-date table, the user context and the history as chat turns.

Messages follow the OpenAI/Qwen chat format (role user/assistant/tool, assistant.tool_calls), so any tokenizer with a
tool-calling chat template (Qwen2.5/Qwen3, Llama-3.x, ...) renders them with apply_chat_template(messages, tools=...).
"""
from __future__ import annotations

import datetime as dt
import json

from .textnorm import with_number_hint

WEEKDAYS = ["thứ hai", "thứ ba", "thứ tư", "thứ năm", "thứ sáu", "thứ bảy", "chủ nhật"]

# Schema keys kept for the model; descriptions of parameters are kept because they carry format hints
# ("ISO-8601 đầy đủ giây...", "lấy từ contacts.search") that matter for exact-match arguments.
_KEEP = ("type", "enum", "description", "items", "minimum", "maximum", "exclusiveMinimum", "format")


def compact_tool(t: dict) -> dict:
    """One catalog tool -> OpenAI-style function schema (what chat templates expect)."""
    p = t.get("parameters") or {}
    props = {}
    for k, v in (p.get("properties") or {}).items():
        q = {kk: vv for kk, vv in v.items() if kk in _KEEP}
        if v.get("x-match") == "fuzzy":
            q["description"] = (q.get("description", "") + " (văn bản tự do, ngắn gọn theo lời người dùng)").strip()
        props[k] = q
    params = {"type": "object", "properties": props, "required": list(p.get("required") or [])}
    desc = t.get("description", "")
    if p.get("x-one-of"):
        desc += " | Bắt buộc có một trong: " + " hoặc ".join("+".join(g) for g in p["x-one-of"])
    if t.get("kind") == "read":
        desc = "[đọc] " + desc
    elif t.get("kind") == "write":
        desc = "[ghi] " + desc
    if t.get("returns"):
        desc += f" | Trả về: {t['returns']}"
    return {"type": "function", "function": {"name": t["name"], "description": desc, "parameters": params}}


def tools_for_sample(item: dict, catalog_tools: dict) -> list[dict]:
    names = [n for a in item["context"]["installed_apps"].values() for n in a.get("tools", [])]
    names.append("sys.ask_missing_info")
    return [compact_tool(catalog_tools[n]) for n in names if n in catalog_tools]


def date_table(now: dt.datetime) -> str:
    """Explicit calendar so a small model never does weekday arithmetic itself (gold conventions, see README):
    'thứ X' = next occurrence after today; 'thứ X này' = this Mon-Sun week; 'thứ X tuần sau' = next Mon-Sun week."""
    d0 = now.date()
    lines = []
    special = {-1: "hôm qua", 0: "hôm nay", 1: "ngày mai", 2: "ngày kia / ngày mốt"}
    for k in range(-2, 15):
        d = d0 + dt.timedelta(days=k)
        tag = special.get(k, "")
        lines.append(f"{d.isoformat()} {WEEKDAYS[d.weekday()]}" + (f" ({tag})" if tag else ""))
    mon = d0 - dt.timedelta(days=d0.weekday())
    this_w = ", ".join(f"{WEEKDAYS[i]}={mon + dt.timedelta(days=i)}" for i in range(7))
    next_w = ", ".join(f"{WEEKDAYS[i]}={mon + dt.timedelta(days=7 + i)}" for i in range(7))
    return ("\n".join(lines) + f"\nTuần này (thứ hai→chủ nhật): {this_w}\nTuần sau: {next_w}\n"
            "Quy ước: 'thứ X' không kèm gì = ngày thứ X gần nhất sắp tới; 'thứ X này' = trong tuần này; "
            "'thứ X tuần sau/tuần tới' = trong tuần sau.")


SYSTEM_RULES = """Bạn là trợ lý giọng nói tiếng Việt điều khiển các ứng dụng của người dùng CHỈ bằng cách gọi tool. Bạn được chấm theo các tool call và trạng thái dữ liệu cuối cùng, không theo câu trả lời.

QUY TẮC
1. Chỉ xử lý yêu cầu CUỐI CÙNG của người dùng. Các lượt trước là ngữ cảnh; hành động trong đó đã được thực hiện xong.
2. Gọi ít tool nhất có thể. Mỗi tool call thừa đều bị trừ điểm.
   - KHÔNG gọi tool đọc nếu thông tin hoặc ID cần dùng đã có trong kết quả tool ở các lượt trước.
   - KHÔNG gọi lại cùng một tool đọc với cùng tham số.
   - Tool đọc dạng liệt kê (get_status, list_events, list_chats, list...) thường gọi với arguments {} (không lọc).
   - Tìm người: contacts.search với query đúng tên/quan hệ người dùng nói (vd "Minh", "mẹ").
3. Mọi ID (device_id, contact_id, event_id, ...) phải lấy từ kết quả tool; tuyệt đối không tự bịa ID.
4. Thiếu thông tin: nếu một tham số bắt buộc mà người dùng không nói và không suy ra được (số tiền, giờ, người nhận, ...), hoặc có nhiều đối tượng cùng khớp mà không rõ chọn cái nào (vd danh bạ có 2 người tên Minh, có 2 gói cùng loại mà chỉ huỷ "một gói"): làm xong các việc khác trước, rồi gọi sys.ask_missing_info(tool_name=<tool cần gọi>, params=[<đúng 1 tên tham số thiếu>]) và DỪNG.
5. KHÔNG gọi tool nào nếu: chỉ chào hỏi, cảm ơn, tán gẫu; người dùng đổi ý huỷ yêu cầu ("à thôi khỏi", "để sau"); không có app đã cài nào làm được việc đó; yêu cầu có điều kiện mà lịch sử đã cho thấy điều kiện sai; câu hỏi đã được trả lời trong lịch sử; yêu cầu nguy hại hoặc trái phép.
6. Người dùng tự sửa lời ("à không", "à nhầm", "à lộn") thì chỉ làm theo ý sau cùng.
7. Câu điều kiện ("nếu mai mưa thì ..."): gọi tool đọc để kiểm tra điều kiện (nếu chưa biết), rồi chỉ thực hiện nhánh đúng.
8. Định dạng tham số:
   - Thời điểm: ISO-8601 đủ giây và múi giờ, vd 2026-11-11T05:30:00+07:00. Ngày: YYYY-MM-DD. Dùng bảng lịch bên dưới, không tự tính thứ.
   - "sáng" 0-11h, "trưa" 11-13h, "chiều" 13-18h, "tối" 18-23h ("7 giờ tối" = 19:00). "rưỡi" = :30.
   - Tiền: số nguyên VND, vd "năm trăm nghìn" = 500000, "ba trăm rưỡi" = 350000, "1 triệu 2" = 1200000.
   - Số nguyên không có dấu chấm/phẩy. Số điện thoại giữ dạng chuỗi chữ số.
   - Nội dung tin nhắn, ghi chú, tiêu đề: ngắn gọn, giữ đúng ý và từ ngữ của người dùng.
9. Chỉ truyền tham số cần thiết; không thêm tham số tuỳ chọn mà người dùng không yêu cầu.
10. Khi đã xong (hoặc không cần làm gì): trả lời một câu ngắn bằng tiếng Việt, không gọi thêm tool."""


def system_prompt(item: dict) -> str:
    ctx = item["context"]
    now = dt.datetime.fromisoformat(ctx["current_time"])
    prof = ctx.get("user_profile") or {}
    prof_lines = "\n".join(f"- {k}: {v}" for k, v in prof.items())
    loc = ctx.get("location") or {}
    apps = ", ".join(ctx["installed_apps"].keys())
    return (f"{SYSTEM_RULES}\n\nNGỮ CẢNH\n- Bây giờ: {ctx['current_time']} ({WEEKDAYS[now.weekday()]}), múi giờ {ctx.get('timezone')}\n"
            f"- Vị trí hiện tại: lat {loc.get('lat')}, lng {loc.get('lng')}\n{prof_lines}\n- App đã cài: {apps}\n\n"
            f"LỊCH\n{date_table(now)}")


def _dump(x) -> str:
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


def history_messages(item: dict, transcribe) -> list[dict]:
    """history -> chat messages. transcribe(audio_path) -> text. Assistant tool calls of earlier turns are rendered as
    real tool calls + tool results, so the model sees IDs it may reuse without re-reading."""
    msgs = []
    for h in item.get("history", []):
        if h["role"] == "user":
            msgs.append({"role": "user", "content": with_number_hint(transcribe(h["audio"], h))})
            continue
        calls = h.get("tool_calls") or []
        if calls:
            msgs.append({"role": "assistant", "content": "", "tool_calls": [
                {"type": "function", "function": {"name": c["name"], "arguments": c.get("arguments") or {}}} for c in calls]})
            results = h.get("tool_results")
            for i, _c in enumerate(calls):
                r = results[i] if results and i < len(results) else {"note": "(kết quả không được lưu)"}
                msgs.append({"role": "tool", "content": _dump(r)})
        if h.get("text"):
            msgs.append({"role": "assistant", "content": h["text"]})
    return msgs


def build_messages(item: dict, transcribe) -> list[dict]:
    msgs = [{"role": "system", "content": system_prompt(item)}]
    msgs += history_messages(item, transcribe)
    msgs.append({"role": "user", "content": with_number_hint(transcribe(item["audio"], None))})
    return msgs


def visible_text(item: dict) -> str:
    """Everything the agent has seen from the environment before this turn (for the hallucinated-ID guard)."""
    return _dump([h.get("tool_results") for h in item.get("history", [])]) + _dump(item.get("history", []))


def shrink(messages: list[dict], tools: list[dict], level: int) -> tuple[list[dict], list[dict]]:
    """Progressively smaller prompt when it does not fit the context window.
    level 1: drop parameter descriptions; level 2: also drop history turns older than the last 4 user turns;
    level 3: also truncate long tool results of the history."""
    if level >= 1:
        tools = [{"type": "function", "function": {**t["function"], "parameters": {
            **t["function"]["parameters"],
            "properties": {k: {kk: vv for kk, vv in v.items() if kk != "description"}
                           for k, v in t["function"]["parameters"]["properties"].items()}}}} for t in tools]
    if level >= 2:
        # messages = [system, *history, current user, *current-turn steps]; keep the current turn intact
        last_user = max(i for i, m in enumerate(messages) if m["role"] == "user" and i > 0 and
                        all(mm["role"] != "user" for mm in messages[i + 1:]))
        users = [i for i in range(1, last_user) if messages[i]["role"] == "user"]
        if len(users) > 4:
            cut = users[-4]
            messages = [messages[0]] + messages[cut:]
    if level >= 3:
        messages = [({**m, "content": m["content"][:1500] + "…"} if m["role"] == "tool" and len(m["content"]) > 1500 else m)
                    for m in messages]
    return messages, tools
