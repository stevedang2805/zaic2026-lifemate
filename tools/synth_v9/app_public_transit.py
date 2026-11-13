from common import *

A = "public_transit"


def Rt(i, name, typ, stops, fare, dur, headway, aliases=None):
    d = {"id": i, "name": name, "type": typ, "stops": stops, "fare": fare, "duration_min": dur, "headway_min": headway}
    if aliases:
        d["aliases"] = aliases
    return d


def ST(balance, routes=(), departures=()):
    return {"card_balance": balance, "routes": list(routes), "departures": list(departures), "topups": []}


HN_ROUTES = [
    Rt("bus_32", "Tuyến 32", "bus", ["Giáp Bát", "Kim Liên", "Cầu Giấy", "Nhổn"], 7000, 60, 10),
    Rt("metro_2a", "Metro Cát Linh - Hà Đông", "metro", ["Cát Linh", "La Thành", "Thái Hà", "Láng", "Yên Nghĩa"], 12000, 25, 6),
    Rt("bus_09", "Tuyến 09", "bus", ["Bờ Hồ", "Cầu Giấy", "Mỹ Đình"], 7000, 40, 15),
]
HCM_ROUTES = [
    Rt("metro_1", "Metro số 1 Bến Thành - Suối Tiên", "metro", ["Bến Thành", "Ba Son", "Thảo Điền", "Thủ Đức", "Suối Tiên"], 20000, 30, 8),
    Rt("bus_19", "Tuyến 19", "bus", ["Bến Thành", "Đại học Bách Khoa", "Khu chế xuất Linh Trung"], 7000, 50, 12),
]


def build():
    S = []

    # 1. tìm tuyến
    s = Sc(A, "2026-11-18T07:30", [A], 1)
    s.state[A] = ST(45000, HN_ROUTES)
    s.say("Từ Cầu Giấy đi Nhổn thì bắt xe buýt nào?",
          C(f"{A}.find_routes", origin="Cầu Giấy", destination="Nhổn"))
    S.append(s)

    # 2. chuyến kế tiếp tại trạm, có số tuyến
    s = Sc(A, "2026-11-18T07:30", [A], 1)
    s.state[A] = ST(45000, HN_ROUTES, [{"stop": "Cầu Giấy", "route": "bus_32", "time": "07:38"}, {"stop": "Cầu Giấy", "route": "bus_09", "time": "07:35"}, {"stop": "Cầu Giấy", "route": "bus_32", "time": "07:48"}])
    s.say("Xe 32 ở trạm Cầu Giấy bao giờ tới chuyến tiếp theo?",
          C(f"{A}.next_departures", stop="Cầu Giấy", route="32"))
    S.append(s)

    # 3. nạp thẻ
    s = Sc(A, "2026-11-19T18:00", [A], 0)
    s.state[A] = ST(8000, HCM_ROUTES)
    s.say("Nạp hai trăm nghìn vào thẻ xe buýt giúp em.",
          C(f"{A}.topup_card", amount=200000))
    S.append(s)

    # 4. thiếu số tiền -> ask amount
    s = Sc(A, "2026-11-19T18:00", [A], 0)
    s.state[A] = ST(8000, HCM_ROUTES)
    s.say("Thẻ xe sắp hết tiền rồi, nạp thêm giúp em.",
          ASK(f"{A}.topup_card", "amount"))
    S.append(s)

    # 5. từ nhà đến công ty (nhà -> home_address)
    s = Sc(A, "2026-11-20T06:50", [A], 0)
    r = Rt("metro_1", "Metro số 1 Bến Thành - Suối Tiên", "metro", ["Bến Thành", "Ba Son", "Thảo Điền", "Thủ Đức", "Suối Tiên"], 20000, 30, 8,
           aliases={"nhà": "Bến Thành", "45 Lê Thánh Tôn": "Bến Thành", "công ty": "Ba Son", "12 Nguyễn Huệ": "Ba Son"})
    s.state[A] = ST(50000, [r])
    s.say("Từ nhà tới công ty đi metro được không, tuyến nào?",
          C(f"{A}.find_routes", origin=s.prof["home_address"], destination=s.prof["work_address"]))
    S.append(s)

    # 6. tìm tuyến + nạp thẻ nếu dưới 20k: cần biết số dư -> không có tool đọc số dư; user nói rõ nạp
    s = Sc(A, "2026-11-21T08:10", [A], 1)
    s.state[A] = ST(5000, HN_ROUTES)
    s.say("Chỉ anh tuyến từ Giáp Bát lên Cầu Giấy, với nạp thẻ năm chục nghìn luôn.",
          C(f"{A}.find_routes", origin="Giáp Bát", destination="Cầu Giấy"),
          C(f"{A}.topup_card", amount=50000))
    S.append(s)

    # 7. chuyến kế tiếp không nói tuyến
    s = Sc(A, "2026-11-22T17:20", [A], 0)
    s.state[A] = ST(30000, HCM_ROUTES, [{"stop": "Bến Thành", "route": "metro_1", "time": "17:28"}, {"stop": "Bến Thành", "route": "bus_19", "time": "17:25"}])
    s.say("Ở ga Bến Thành sắp có chuyến nào không?",
          C(f"{A}.next_departures", stop="Bến Thành"))
    S.append(s)

    # 8. nạp + nhắc
    s = Sc(A, "2026-11-23T21:00", [A, "reminders"], 2)
    s.state[A] = ST(12000)
    s.state["reminders"] = reminders()
    s.say("Nạp một trăm nghìn vào thẻ đi xe, rồi nhắc tôi sáu rưỡi sáng mai ra bến.",
          C(f"{A}.topup_card", amount=100000),
          C("reminders.create", content="Ra bến xe buýt", time=s.t(1, 6, 30)))
    S.append(s)

    # 9. [] - chat
    s = Sc(A, "2026-11-24T08:00", [A], 1)
    s.state[A] = ST(20000, HN_ROUTES)
    s.say("Sáng nay xe buýt đông kinh khủng, đứng suốt từ Giáp Bát lên.")
    S.append(s)

    # 10. tuyến từ địa điểm tới địa điểm, không có trong state -> fallback vẫn trả tuyến (ok)
    s = Sc(A, "2026-11-25T13:00", [A], 2)
    s.state[A] = ST(20000)
    s.say("Từ Cầu Rồng tới Bà Nà đi buýt tuyến nào vậy?",
          C(f"{A}.find_routes", origin="Cầu Rồng", destination="Bà Nà"))
    S.append(s)

    # 11. history: đã tìm tuyến -> hỏi chuyến kế tiếp tại điểm lên
    s = Sc(A, "2026-11-26T07:00", [A], 1)
    s.state[A] = ST(40000, HN_ROUTES, [{"stop": "Kim Liên", "route": "bus_32", "time": "07:12"}])
    s.user("Từ Kim Liên đi Nhổn bắt xe gì?")
    s.bot("Bạn đi tuyến 32, lên ở Kim Liên, xuống Nhổn, khoảng 40 phút, giá 7.000đ ạ.", C(f"{A}.find_routes", origin="Kim Liên", destination="Nhổn"))
    s.say("Thế chuyến 32 tiếp theo ở Kim Liên mấy giờ?",
          C(f"{A}.next_departures", stop="Kim Liên", route="32"))
    S.append(s)

    # 12. [] - đã trả lời
    s = Sc(A, "2026-11-26T07:00", [A], 1)
    s.state[A] = ST(40000, HN_ROUTES)
    s.user("Từ Kim Liên đi Nhổn bắt xe gì?")
    s.bot("Bạn đi tuyến 32, lên ở Kim Liên, xuống Nhổn, khoảng 40 phút, giá 7.000đ ạ.", C(f"{A}.find_routes", origin="Kim Liên", destination="Nhổn"))
    s.say("Bảy nghìn thôi à, rẻ nhỉ.")
    S.append(s)

    # 13. nạp số tiền đọc kiểu "năm chục"
    s = Sc(A, "2026-11-27T19:30", [A], 3)
    s.state[A] = ST(3000)
    s.say("Nạp năm chục vô thẻ xe buýt.",
          C(f"{A}.topup_card", amount=50000))
    S.append(s)

    # 14. [] - không app nào: đặt xe công nghệ
    s = Sc(A, "2026-11-27T19:30", [A], 3)
    s.state[A] = ST(3000)
    s.say("Đặt cho tôi một chuyến xe ôm công nghệ về nhà.")
    S.append(s)

    # 15. metro: chuyến kế tiếp
    s = Sc(A, "2026-11-28T08:05", [A], 1)
    s.state[A] = ST(60000, HN_ROUTES, [{"stop": "Cát Linh", "route": "metro_2a", "time": "08:10"}, {"stop": "Cát Linh", "route": "metro_2a", "time": "08:16"}])
    s.say("Tàu điện ở Cát Linh chuyến tới mấy giờ?",
          C(f"{A}.next_departures", stop="Cát Linh"))
    S.append(s)

    # 16. tìm tuyến + ghi chú
    s = Sc(A, "2026-11-29T10:00", [A, "notes"], 0)
    s.state[A] = ST(25000, HCM_ROUTES)
    s.state["notes"] = notes()
    s.say("Tìm tuyến từ Bến Thành đi Suối Tiên rồi ghi chú lại tên tuyến giúp em.",
          C(f"{A}.find_routes", origin="Bến Thành", destination="Suối Tiên"),
          C("notes.create", content="Bến Thành đi Suối Tiên: Metro số 1 Bến Thành - Suối Tiên"))
    S.append(s)

    # 17. nạp hai lần? không. Nạp 300k + nhắn mẹ
    s = Sc(A, "2026-11-30T20:15", [A, "chat_ott"], 2)
    s.state[A] = ST(1000)
    s.state["chat_ott"] = chats(("chat_01", "Mẹ", "direct"))
    s.say("Nạp ba trăm nghìn thẻ xe buýt, rồi nhắn mẹ là 'con nạp thẻ xe cho mẹ rồi nha'.",
          C(f"{A}.topup_card", amount=300000),
          C("chat_ott.list_chats"),
          C("chat_ott.send_message", chat_id="chat_01", content="con nạp thẻ xe cho mẹ rồi nha"))
    S.append(s)

    # 18. tìm tuyến từ công ty về nhà (alias)
    s = Sc(A, "2026-12-01T17:45", [A], 1)
    r = Rt("bus_26", "Tuyến 26", "bus", ["Mỹ Đình", "Keangnam", "Láng Hạ", "Bờ Hồ"], 7000, 45, 12,
           aliases={"công ty": "Keangnam", "Tòa nhà Keangnam": "Keangnam", "nhà": "Láng Hạ", "27 Láng Hạ": "Láng Hạ"})
    s.state[A] = ST(15000, [r])
    s.say("Từ công ty về nhà bắt buýt số mấy nhỉ?",
          C(f"{A}.find_routes", origin=s.prof["work_address"], destination=s.prof["home_address"]))
    S.append(s)

    # 19. tiếng Anh lẫn: "top up"
    s = Sc(A, "2026-12-02T12:30", [A], 0)
    s.state[A] = ST(9000)
    s.say("Top up thẻ metro một trăm năm mươi nghìn nhé.",
          C(f"{A}.topup_card", amount=150000))
    S.append(s)

    # 20. hai câu hỏi đọc
    s = Sc(A, "2026-12-03T07:15", [A], 0)
    s.state[A] = ST(30000, HCM_ROUTES, [{"stop": "Thảo Điền", "route": "metro_1", "time": "07:22"}])
    s.say("Từ Thảo Điền đi Bến Thành đi tuyến nào, và ở ga Thảo Điền chuyến tới lúc mấy giờ?",
          C(f"{A}.find_routes", origin="Thảo Điền", destination="Bến Thành"),
          C(f"{A}.next_departures", stop="Thảo Điền"))
    S.append(s)

    # 21. [] - huỷ
    s = Sc(A, "2026-12-04T18:00", [A], 2)
    s.state[A] = ST(30000)
    s.say("Nạp thẻ xe hai trăm... khoan, để mai nạp, giờ chưa có lương.")
    S.append(s)

    # 22. nạp + đánh dấu task "nạp thẻ xe buýt" xong
    s = Sc(A, "2026-12-05T09:00", [A, "tasks"], 3)
    s.state[A] = ST(0)
    s.state["tasks"] = tasks(("task_01", "Nạp thẻ xe buýt", "", "normal", False), ("task_02", "Nộp học phí", "", "high", False))
    s.say("Nạp một trăm nghìn vào thẻ buýt rồi tick xong cái việc nạp thẻ trong danh sách luôn.",
          C(f"{A}.topup_card", amount=100000),
          C("tasks.list"),
          C("tasks.complete", task_id="task_01"))
    S.append(s)

    return S
