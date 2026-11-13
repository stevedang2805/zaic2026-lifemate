"""Giá trị đã có trong history -> hành động luôn, KHÔNG ask_missing_info (lỗi val v9: train_0441 'đăng ký luôn khoá đấy' -> ask;
train_0486 'cho nó chạy giặt nhanh luôn' -> ask cycle). Dùng ID/giá trị từ lượt trước, không đọc lại read còn mới."""
from common import *

A = "hist"


def build():
    S = []

    # 1. đã liệt kê sự kiện -> "đặt luôn cái đó"
    s = Sc(A, "2026-11-18T19:00", ["event_tickets"], 0)
    s.state["event_tickets"] = {"events": [{"id": "ev_01", "name": "Đêm nhạc Bằng Kiều", "category": "ca nhạc", "date": s.d(6), "time": "20:00", "venue": "Nhà hát Hòa Bình", "price": 1200000, "available": 30},
                                           {"id": "ev_02", "name": "Kịch Thành phố tôi yêu", "category": "kịch", "date": s.d(3), "time": "19:30", "venue": "Idecaf", "price": 300000, "available": 50}], "bookings": []}
    s.user("Cuối tuần có show ca nhạc nào không em?")
    s.bot("Có Đêm nhạc Bằng Kiều ở Nhà hát Hòa Bình, 20:00, vé 1.200.000đ ạ.", C("event_tickets.search", query="ca nhạc"))
    s.say("Ừ thế lấy luôn cho chị hai vé show đó nhé.", C("event_tickets.book", event_id="ev_01", quantity=2))
    S.append(s)

    # 2. đã hỏi số lượng ở lượt trước, user nói số luôn trong câu sau
    s = Sc(A, "2026-11-19T10:00", ["grocery"], 1)
    s.state["grocery"] = {"products": [{"id": "prod_01", "name": "Sữa chua Vinamilk lốc 4", "price": 26000, "unit": "lốc", "category": "sữa", "in_stock": True}], "cart": [], "orders": []}
    s.user("Trên app có sữa chua Vinamilk không?")
    s.bot("Có Sữa chua Vinamilk lốc 4, giá 26.000đ ạ.", C("grocery.search", query="sữa chua Vinamilk"))
    s.say("Thế cho ba lốc vào giỏ rồi đặt luôn nhé.", C("grocery.add_to_cart", product_id="prod_01", quantity=3), C("grocery.checkout"))
    S.append(s)

    # 3. smart home: đã get_status, "bật cái ở phòng khách lên chế độ làm mát" -> không ask
    s = Sc(A, "2026-11-20T14:00", ["smart_home"], 2)
    s.state["smart_home"] = smart(("ac_01", "Điều hoà phòng khách", "phòng khách", "climate", {"mode": "off"}), ("ac_02", "Điều hoà phòng ngủ", "phòng ngủ", "climate", {"mode": "off"}))
    s.user("Nhà mình có mấy cái điều hoà?")
    s.bot("Nhà có 2 điều hoà: phòng khách và phòng ngủ, đều đang tắt ạ.", C("smart_home.get_status", type="climate"))
    s.say("Bật cái phòng khách chế độ làm mát hai sáu độ đi.", C("smart_home.climate_set", device_id="ac_01", mode="cool", temperature=26))
    S.append(s)

    # 4. trợ lý đã hỏi giờ, user trả lời ngắn
    s = Sc(A, "2026-11-21T21:00", ["reminders"], 3)
    s.state["reminders"] = reminders()
    s.user("Mai nhắc tôi đi lấy giấy khám sức khoẻ.")
    s.bot("Anh muốn nhắc lúc mấy giờ ạ?", ASK("reminders.create", "time"))
    s.say("Tám rưỡi sáng.", C("reminders.create", content="Đi lấy giấy khám sức khoẻ", time=s.t(1, 8, 30)))
    S.append(s)

    # 5. trợ lý đã hỏi số tiền, user trả lời
    s = Sc(A, "2026-11-22T11:00", ["ewallet", "contacts"], 4)
    s.state["ewallet"] = ewallet(2000000)
    s.state["contacts"] = contacts(("c_01", "Bé Na", "con gái", "0901222333"))
    s.user("Nạp tiền điện thoại cho bé Na.")
    s.bot("Anh muốn nạp bao nhiêu tiền ạ?", C("contacts.search", query="bé Na"), ASK("ewallet.topup_mobile", "amount"))
    s.say("Một trăm nghìn.", C("ewallet.topup_mobile", phone="0901222333", amount=100000))
    S.append(s)

    # 6. trợ lý hỏi chọn 1 trong 2, user chọn bằng mô tả
    s = Sc(A, "2026-11-23T09:00", ["banking"], 5)
    s.state["banking"] = banking([("acc_01", "Tài khoản lương", 20000000), ("acc_02", "Tài khoản tiết kiệm online", 50000000)], [("ben_01", "Chủ nhà", "BIDV")])
    s.user("Chuyển tiền nhà bốn triệu cho chủ nhà.")
    s.bot("Bạn muốn chuyển từ tài khoản lương hay tài khoản tiết kiệm online ạ?", C("banking.get_balance"), C("banking.list_beneficiaries"), ASK("banking.transfer", "from_account_id"))
    s.say("Tài khoản lương.", C("banking.transfer", from_account_id="acc_01", beneficiary_id="ben_01", amount=4000000))
    S.append(s)

    # 7. history có kết quả tìm tuyến, user bảo nạp thẻ đủ đi 2 lượt (giá vé trong history 7000) -> 14000? tránh suy diễn; nạp số nói rõ
    s = Sc(A, "2026-11-24T07:00", ["public_transit"], 1)
    s.state["public_transit"] = {"card_balance": 3000, "routes": [{"id": "bus_32", "name": "Tuyến 32", "type": "bus", "stops": ["Giáp Bát", "Cầu Giấy"], "fare": 7000, "duration_min": 40, "headway_min": 10}], "departures": [], "topups": []}
    s.user("Từ Giáp Bát lên Cầu Giấy đi xe gì?")
    s.bot("Bạn đi tuyến 32, khoảng 40 phút, vé 7.000đ ạ.", C("public_transit.find_routes", origin="Giáp Bát", destination="Cầu Giấy"))
    s.say("Thẻ còn có ba nghìn, nạp năm chục nghìn đi.", C("public_transit.topup_card", amount=50000))
    S.append(s)

    # 8. đã đọc danh sách công thức, "lưu cái thứ hai"
    s = Sc(A, "2026-11-25T18:00", ["recipes"], 6)
    s.state["recipes"] = {"recipes": [{"id": "rcp_01", "name": "Canh bí đỏ nấu tôm", "servings": 4, "tags": [], "ingredients": [], "steps": []},
                                      {"id": "rcp_02", "name": "Canh chua tôm", "servings": 4, "tags": [], "ingredients": [], "steps": []}], "saved": []}
    s.user("Có món canh nào nấu với tôm?")
    s.bot("Có 2 món: Canh bí đỏ nấu tôm và Canh chua tôm ạ.", C("recipes.search", query="canh tôm"))
    s.say("Lưu món thứ hai giúp em.", C("recipes.save", recipe_id="rcp_02"))
    S.append(s)

    # 9. đã có kết quả tìm chuyến bay; user chọn chuyến chiều, số người đã nói ở lượt đầu
    s = Sc(A, "2026-11-26T20:00", ["flights"], 7)
    s.state["flights"] = {"flights": [{"id": "fl_01", "origin": "HPH", "destination": "SGN", "date": s.d(3), "depart": "06:30", "arrive": "08:40", "airline": "Vietjet", "price": 1500000, "flight_no": "VJ281"},
                                      {"id": "fl_02", "origin": "HPH", "destination": "SGN", "date": s.d(3), "depart": "15:00", "arrive": "17:10", "airline": "Bamboo", "price": 1700000, "flight_no": "QH1153"}], "bookings": []}
    s.user(f"Vợ chồng tôi muốn bay Hải Phòng vào Sài Gòn ngày {s.dm(3)}, có chuyến nào?")
    s.bot("Ngày đó có VJ281 lúc 6:30 (1.500.000đ) và QH1153 lúc 15:00 (1.700.000đ) ạ.", C("flights.search", origin="Hải Phòng", destination="Sài Gòn", date=s.d(3)))
    s.say("Lấy chuyến buổi chiều.", C("flights.book", flight_id="fl_02", passengers=2))
    S.append(s)

    # 10. history: đã xem danh sách việc, "xong cái đầu tiên rồi"
    s = Sc(A, "2026-11-27T17:00", ["tasks"], 0)
    s.state["tasks"] = tasks(("task_01", "Gửi hợp đồng cho khách", "", "high", False), ("task_02", "Đặt phòng họp", "", "normal", False))
    s.user("Hôm nay còn việc gì chưa làm?")
    s.bot("Còn 2 việc: Gửi hợp đồng cho khách (ưu tiên cao) và Đặt phòng họp ạ.", C("tasks.list", status="open"))
    s.say("Cái gửi hợp đồng xong rồi, đánh dấu giúp tôi.", C("tasks.complete", task_id="task_01"))
    S.append(s)

    # 11. history: assistant báo đã tìm thấy liên hệ, user muốn gọi
    s = Sc(A, "2026-11-28T09:00", ["contacts", "phone"], 1)
    s.state["contacts"] = contacts(("c_01", "Thầy Phong", "giáo viên chủ nhiệm", "0904555666"))
    s.state["phone"] = {"calls": []}
    s.user("Số của thầy Phong chủ nhiệm là bao nhiêu?")
    s.bot("Số của thầy Phong là 0904555666 ạ.", C("contacts.search", query="thầy Phong"))
    s.say("Gọi luôn cho thầy giúp tôi.", C("phone.call", contact_id="c_01"))
    S.append(s)

    # 12. history: user đã nói giờ ở lượt trước, giờ mới bảo "tạo lịch đi"
    s = Sc(A, "2026-11-29T10:00", ["calendar"], 2)
    s.state["calendar"] = events()
    s.user("Ba giờ chiều nay tôi có hẹn với nha sĩ ở Nha khoa Kim.")
    s.bot("Dạ, chiều nay 15:00 anh có hẹn nha sĩ ở Nha khoa Kim ạ.")
    s.say("Ừ, tạo lịch cho cuộc hẹn đó luôn.", C("calendar.create_event", title="Hẹn nha sĩ", start=s.t(0, 15), end=s.t(0, 16), location="Nha khoa Kim"))
    S.append(s)

    # 13. history: đã get_quotes -> book loại rẻ nhất
    s = Sc(A, "2026-11-30T18:00", ["ride_hailing"], 3)
    s.state["ride_hailing"] = {"quotes": [{"vehicle": "bike", "price": 28000}, {"vehicle": "car4", "price": 85000}], "rides": []}
    s.user("Từ công ty về nhà đi xe gì rẻ nhất?")
    s.bot("Xe máy 28.000đ, ô tô 4 chỗ 85.000đ ạ.", C("ride_hailing.get_quotes", pickup=s.prof["work_address"], dropoff=s.prof["home_address"]))
    s.say("Đặt cái rẻ nhất đi.", C("ride_hailing.book", pickup=s.prof["work_address"], dropoff=s.prof["home_address"], vehicle="bike"))
    S.append(s)

    # 14. history: đã tra giá vàng nhẫn, user đặt nhắc với số đó (không tra lại)
    s = Sc(A, "2026-12-01T09:00", ["gold_price", "notes"], 4)
    s.state["gold_price"] = gold(130000000, 132000000, 128000000, 130500000)
    s.state["notes"] = notes()
    s.user("Vàng nhẫn hôm nay bao nhiêu?")
    s.bot("Vàng nhẫn mua vào 128.000.000đ, bán ra 130.500.000đ một lượng ạ.", C("gold_price.get_price", type="ring"))
    s.say("Ghi chú lại giá bán ra hôm nay giúp tôi.", C("notes.create", content=f"Giá vàng nhẫn bán ra {s.dm(0)}: 130.500.000đ một lượng"))
    S.append(s)

    # 15. history: trợ lý hỏi kênh nào, user trả lời
    s = Sc(A, "2026-12-02T20:00", ["tv"], 5)
    s.state["tv"] = {"channels": ["VTV1", "VTV3", "HTV7"], "programs": [], "recordings": []}
    s.user("Mở tivi xem thời sự.")
    s.bot("Bạn muốn xem kênh nào ạ?", C("tv.guide"), ASK("tv.tune", "channel"))
    s.say("VTV1.", C("tv.tune", channel="VTV1"))
    S.append(s)

    # 16. history: đã liệt kê bãi; "đặt cái rẻ nhất từ giờ hai tiếng"
    s = Sc(A, "2026-12-03T13:00", ["parking"], 6)
    s.state["parking"] = parking_state([("lot_01", "Bãi xe Saigon Centre", "65 Lê Lợi", "Quận 1", 35000, 10), ("lot_02", "Bãi xe Công viên 23/9", "Phạm Ngũ Lão", "Quận 1", 15000, 40)])
    s.user("Quận 1 có bãi đỗ nào?")
    s.bot("Có Bãi xe Saigon Centre (35.000đ/giờ) và Bãi xe Công viên 23/9 (15.000đ/giờ) ạ.", C("parking.find", near="Quận 1"))
    s.say("Đặt cái rẻ hơn từ bây giờ, hai tiếng.", C("parking.reserve", lot_id="lot_02", from_time=s.now_iso(), hours=2))
    S.append(s)

    return S
