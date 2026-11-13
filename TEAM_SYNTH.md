# Việc A — Tạo dữ liệu synthetic cho các app chưa có trong train

## Vì sao việc này quan trọng nhất
- Khi transcript đúng, LLM của mình vẫn chỉ đạt **49 điểm trên app lạ**, nhưng **68 điểm trên app đã train**.
- 65% mẫu public cài ít nhất một trong 11 app **không có trong train**. Các đội top đạt 92–96 điểm, gần như chắc chắn nhờ dữ liệu cho các app này.
- Mỗi mẫu bạn viết sẽ được **chính simulator của BTC** chạy kiểm tra. Mẫu sai bị từ chối kèm lý do, nên không lo đưa nhãn sai vào train.

## LUẬT — đọc kỹ
- **KHÔNG** mở, copy hay chép lại bất cứ thứ gì trong `public_test/public_test.jsonl` hoặc `public_test/public_test_environment/`, kể cả "lấy cảm hứng" từ câu hay dữ liệu trong đó. Luật cấm dùng public test để train; vi phạm có thể bị loại.
- Được dùng: catalog `public_test_tools_catalog.json` (schema tool), code `public_test/zaic_tools/apps/<app>.py` (docstring đầu file mô tả cấu trúc state), và dữ liệu train.
- Được dùng LLM bên ngoài (ChatGPT, Gemini, Claude...) để **viết spec**; luật cho phép dùng để tạo synthetic data trong giai đoạn phát triển.

## Chia app

| Người | App (ưu tiên từ trên xuống) |
|---|---|
| A1 | ecommerce, grocery, pantry, recipes, habit_tracker, stocks |
| A2 | event_tickets, train_bus_tickets, public_transit, parking, translator |

Mục tiêu: **khoảng 40 mẫu cho mỗi app**, tổng khoảng 450 mẫu. Khoảng một nửa nên kết hợp app mới với app quen thuộc (contacts, calendar, reminders, banking, ewallet, sms, chat_ott, maps...), vì mẫu thật thường gồm nhiều app.

Tỉ lệ nên theo train:
- Khoảng 65% làm được ngay, với 1–3 write.
- 15% thiếu thông tin, phải gọi `sys.ask_missing_info`.
- 8% out-of-scope, gold là `[]`.
- 30–40% có history (1–3 lượt trước đó).

## Cách làm
1. Đọc docstring đầu file `public_test/zaic_tools/apps/<app>.py`, phần `State: {...}`, và schema của app trong catalog.
2. Viết spec, mỗi mẫu một dòng JSON, vào `synth_specs/<app>.jsonl`. Xem 4 mẫu ở `synth_specs/example_parking.jsonl`.
3. Chạy (thư mục `DATA` chứa `train/` và `public_test/`):
   ```bash
   python -m lifemate.synth_build --root DATA --tools-from public_test --specs "synth_specs/*.jsonl"
   ```
   Mẫu nào sai sẽ hiện `REJECT <id>: <lý do>`. Sửa spec rồi chạy lại cho đến khi không còn mẫu bị từ chối.
4. Gửi file `synth_specs/*.jsonl`. Không cần gửi output, vì output build lại được.

## Quy ước gold (đo trên 1545 mẫu train; bộ lint tự kiểm tra phần lớn)
1. **Phải đọc rồi mới dùng ID.** Muốn dùng `lot_id` thì phải gọi `parking.find` trước. ID không được tự bịa.
2. **Gọi ít nhất có thể.** Không đọc lại cùng một thứ. Nếu history đã có kết quả đọc và sau đó chưa có write nào vào app đó, thì không đọc lại.
3. **Tool đọc dạng liệt kê gọi với `{}`**, trừ khi tool bắt buộc có filter (ví dụ `parking.find` bắt buộc `near`).
4. **Thiếu thông tin:** làm hết phần làm được, rồi gọi **một** `sys.ask_missing_info` ở cuối, với **đúng 1 tham số** (`params: ["from_time"]`). Có 2 đối tượng cùng khớp (2 contact tên Minh, 2 vé cùng loại mà người dùng nói "huỷ một vé") thì hỏi tham số ID.
5. **Gold là `[]` khi:** chào hỏi hoặc tán gẫu; người dùng đổi ý ("à thôi khỏi"); không app đã cài nào làm được; điều kiện đã biết là sai từ history; câu hỏi đã được trả lời trong history.
6. **Tự sửa lời** ("à không", "à nhầm", "à lộn"): chỉ làm theo ý sau cùng.
7. **Tham số tùy chọn** chỉ truyền khi người dùng nói rõ. Không tự thêm `note`, `label`, hay giá trị mặc định.
8. **Định dạng:**
   - Thời điểm: `2026-11-20T09:30:00+07:00`.
   - Ngày: `2026-11-20`.
   - Tiền và số lượng: số nguyên (`500000`).
   - Số điện thoại: chuỗi.
   - "thứ X" là ngày thứ X gần nhất sắp tới; "thứ X tuần sau" là thứ X của tuần kế tiếp (tuần tính từ thứ hai).
9. **Câu nói phải giống người thật:** nói tắt, có từ địa phương (nớ, rứa, hỉ, nghen, nha, bữa ni...), số đọc bằng chữ ("ba trăm rưỡi", "chín giờ kém mười lăm"), có câu điều kiện ("nếu còn chỗ thì...", "rẻ hơn 500 nghìn thì..."), và có những câu cần cộng trừ giờ hoặc tiền.
10. **Đa dạng state:** đổi tên, giá, giờ, số lượng; cho đối tượng hết chỗ, hết hàng; có 2 đối tượng tên gần giống nhau.

## Tăng tốc bằng LLM
Đưa cho LLM 4 thứ: (1) docstring state của app, (2) schema các tool của app lấy từ catalog, (3) mục Quy ước ở trên, (4) 4 mẫu trong `example_parking.jsonl`. Sau đó yêu cầu: *"Viết 20 spec mới cho app X theo đúng định dạng JSONL, đa dạng tình huống..."*. Chạy `synth_build` và giữ lại các mẫu được chấp nhận. Sửa tay hoặc nhờ LLM sửa các mẫu bị REJECT. **Đọc qua gold của từng mẫu:** bộ lint chỉ kiểm tra được tính hợp lệ, không kiểm tra được gold có đúng ý câu nói không.
