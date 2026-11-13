"""Print a ready-to-paste prompt for writing synthetic specs of one app with an external LLM.

python -m lifemate.synth_prompt --root DATA --app parking --n 20 > prompt_parking.txt

The prompt contains the app's simulator source (so the LLM knows the exact state fields), its tool schemas, the gold
conventions measured on train, and two worked examples. Paste it into ChatGPT/Claude/Gemini, save the reply to
synth_specs/<app>.jsonl, then run lifemate.synth_build to verify.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CONVENTIONS = """QUY ƯỚC BẮT BUỘC (đo trên 1545 mẫu train thật — sai là bị loại tự động)
1. Phải gọi tool đọc để lấy ID trước khi dùng ID đó trong tool ghi. Không bịa ID.
2. Gọi ít tool nhất có thể: không đọc trùng; nếu history đã có kết quả đọc và sau đó không có tool ghi nào vào cùng app, thì KHÔNG đọc lại.
3. Tool đọc dạng liệt kê gọi với arguments {} (trừ khi schema bắt buộc tham số).
4. Thiếu thông tin: làm xong các việc khác trước, rồi gọi sys.ask_missing_info ở CUỐI, với ĐÚNG 1 tham số:
   {"name": "sys.ask_missing_info", "arguments": {"tool_name": "<app.tool>", "params": ["<ten_tham_so>"]}}
   Dùng cả khi có nhiều đối tượng cùng khớp mà không rõ chọn cái nào.
5. gold = [] khi: chào hỏi/tán gẫu; người dùng đổi ý ("à thôi khỏi"); không app đã cài nào làm được;
   điều kiện đã biết là sai từ history; câu hỏi đã được trả lời trong history.
6. Người dùng tự sửa lời ("à không", "à nhầm"): chỉ làm theo ý sau cùng.
7. Tham số tùy chọn chỉ truyền khi người dùng nói rõ. KHÔNG tự thêm note, label, hay giá trị mặc định.
8. Định dạng: thời điểm "2026-11-20T09:30:00+07:00"; ngày "2026-11-20"; tiền và số lượng là số nguyên (500000);
   số điện thoại là chuỗi. "thứ X" = thứ X gần nhất sắp tới; "thứ X tuần sau" = tuần kế tiếp (tuần bắt đầu thứ hai).
9. audio_text phải giống lời nói thật: nói tắt, từ địa phương (nha, nghen, rứa, hỉ, bữa ni), số đọc bằng chữ
   ("ba trăm rưỡi", "chín giờ kém mười lăm"), câu điều kiện ("nếu còn chỗ thì..."), câu cần cộng trừ giờ/tiền.
10. State phải đa dạng: tên/giá/giờ/số lượng khác nhau; có đối tượng hết chỗ hoặc hết hàng; có 2 đối tượng tên gần giống nhau."""

MIX = ["contacts", "calendar", "reminders", "notes", "tasks", "sms", "chat_ott", "banking", "ewallet", "maps",
       "weather", "alarm", "bill_payment", "email", "shopping_list"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data")
    ap.add_argument("--app", required=True)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--tools-from", default="public_test")
    a = ap.parse_args()
    root = Path(a.root)
    split = a.tools_from
    src = root / split / "zaic_tools" / "apps" / f"{a.app}.py"
    cat = json.load(open(root / split / f"{split}_tools_catalog.json", encoding="utf-8"))
    app = next((x for x in cat["apps"] if x["id"] == a.app), None)
    if app is None:
        raise SystemExit(f"app {a.app} không có trong catalog của {split}")
    mix = [m for m in MIX if any(x["id"] == m for x in cat["apps"])][:6]
    mix_schema = {m: [t["name"] for x in cat["apps"] if x["id"] == m for t in x["tools"]] for m in mix}
    examples = [l.strip() for l in open(Path(__file__).resolve().parents[1] / "synth_specs" / "example_parking.jsonl",
                                        encoding="utf-8") if l.strip()][:2]
    print(f"""Bạn giúp tôi tạo dữ liệu huấn luyện cho một trợ lý giọng nói tiếng Việt điều khiển ứng dụng bằng tool call.
Hãy viết {a.n} mẫu cho app "{a.app}" ({app.get('name_vi')}: {app.get('description')}).

=== CODE MÔ PHỎNG CỦA APP (cho biết chính xác state cần có field gì) ===
{src.read_text(encoding='utf-8')}

=== SCHEMA CÁC TOOL CỦA APP ===
{json.dumps(app['tools'], ensure_ascii=False, indent=1)}

=== CÁC APP KHÁC CÓ THỂ CÀI KÈM (khoảng một nửa số mẫu nên dùng 2-3 app) ===
{json.dumps(mix_schema, ensure_ascii=False)}
State của các app này: contacts={{"contacts":[{{"id","name","relation","phone"}}]}};
calendar={{"events":[{{"id","title","start","end","location"}}]}};
reminders={{"reminders":[{{"id","content","time","done"}}]}};
notes={{"notes":[{{"id","title","content"}}]}}; tasks={{"tasks":[{{"id","title","due","priority","done"}}]}};
sms={{"messages":[]}}; chat_ott={{"chats":[{{"id","name","type","members","messages"}}]}};
banking={{"accounts":[{{"id","name","balance"}}],"beneficiaries":[{{"id","name","bank","account_number"}}],"transactions":[]}};
ewallet={{"balance":3000000,"transactions":[]}}

{CONVENTIONS}

=== ĐỊNH DẠNG ĐẦU RA ===
Mỗi mẫu là MỘT dòng JSON (JSONL), không bọc trong markdown, không giải thích thêm. Các khóa:
id, context{{current_time, timezone, location{{lat,lng}}, user_profile{{name,home_address,work_address,city}}, installed_apps[] }},
state{{<app>: {{...}} cho MỌI app đã cài}}, history[], audio_text, gold[]
- history: lượt user {{"role":"user","audio_text":"..."}}, lượt assistant {{"role":"assistant","text":"...","tool_calls":[...]}}
  (KHÔNG tự viết tool_results, hệ thống tự chạy ra). Các hành động trong history coi như đã thực hiện.
- id đặt dạng "synth_{a.app}_0001" tăng dần.

=== HAI VÍ DỤ ĐÚNG ===
{examples[0]}
{examples[1]}

=== YÊU CẦU PHÂN BỔ {a.n} MẪU ===
- khoảng 65% làm được ngay (1-3 tool ghi), 15% phải gọi sys.ask_missing_info, 8% gold = [], còn lại là đọc thông tin rồi trả lời.
- khoảng 35% có history 1-3 lượt; khoảng 50% dùng thêm app khác ngoài {a.app}.
- current_time trải từ 2026-09 đến 2026-12, đủ các thứ trong tuần, các thành phố Hà Nội / TP.HCM / Đà Nẵng / Huế.
- Mỗi mẫu một state khác nhau, tên và số liệu khác nhau. KHÔNG lặp lại cùng một kịch bản.

Chỉ in ra {a.n} dòng JSONL.""")


if __name__ == "__main__":
    main()
