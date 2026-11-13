from common import *

A = "parking"


def L(i, name, addr, area, price, spots):
    return {"id": i, "name": name, "address": addr, "area": area, "price_per_hour": price, "available_spots": spots}


def SES(i, lot, frm, hours, total, status="reserved"):
    import datetime as dt
    end = (dt.datetime.fromisoformat(frm) + dt.timedelta(hours=hours)).isoformat()
    return {"id": i, "lot_id": lot, "from_time": frm, "hours": hours, "end_time": end, "total": total, "status": status}


def build():
    S = []

    # 1. tìm + đặt 2 tiếng từ giờ cụ thể
    s = Sc(A, "2026-11-18T08:30", [A], 0)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Vincom Đồng Khởi", "72 Lê Thánh Tôn, Quận 1", "Quận 1", 30000, 12),
                           L("lot_02", "Bãi xe Saigon Centre", "65 Lê Lợi, Quận 1", "Quận 1", 25000, 0)], "sessions": []}
    s.say("Đặt chỗ đỗ ở Vincom Đồng Khởi từ chín rưỡi sáng nay, gửi hai tiếng.",
          C(f"{A}.find", near="Vincom Đồng Khởi"),
          C(f"{A}.reserve", lot_id="lot_01", from_time=s.t(0, 9, 30), hours=2))
    S.append(s)

    # 2. "bây giờ" -> from_time = current_time
    s = Sc(A, "2026-11-19T14:05", [A], 1)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Lotte Center", "54 Liễu Giai, Ba Đình", "Ba Đình", 20000, 30)], "sessions": []}
    s.say("Tìm bãi gần Lotte Center, đặt ngay bây giờ một tiếng.",
          C(f"{A}.find", near="Lotte Center"),
          C(f"{A}.reserve", lot_id="lot_01", from_time=s.now_iso(), hours=1))
    S.append(s)

    # 3. thiếu số giờ -> ask hours
    s = Sc(A, "2026-11-20T10:00", [A], 2)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Chợ Hàn", "119 Trần Phú, Hải Châu", "Hải Châu", 10000, 20)], "sessions": []}
    s.say("Đặt chỗ đỗ gần chợ Hàn lúc mười một giờ trưa nay.",
          C(f"{A}.find", near="chợ Hàn"),
          ASK(f"{A}.reserve", "hours"))
    S.append(s)

    # 4. thiếu giờ bắt đầu -> ask from_time
    s = Sc(A, "2026-11-20T10:00", [A], 2)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Chợ Hàn", "119 Trần Phú, Hải Châu", "Hải Châu", 10000, 20)], "sessions": []}
    s.say("Chiều nay đặt cho chị chỗ đỗ gần chợ Hàn, gửi ba tiếng.",
          C(f"{A}.find", near="chợ Hàn"),
          ASK(f"{A}.reserve", "from_time"))
    S.append(s)

    # 5. chỉ tìm (read)
    s = Sc(A, "2026-11-21T07:40", [A], 3)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Đại Nội", "23 Tháng 8, TP Huế", "Thành Nội", 10000, 50),
                           L("lot_02", "Bãi xe Bến Thuyền Tòa Khâm", "49 Lê Lợi, TP Huế", "Phú Hội", 15000, 8)], "sessions": []}
    s.say("Quanh Đại Nội có bãi đỗ xe nào không, giá sao?",
          C(f"{A}.find", near="Đại Nội"))
    S.append(s)

    # 6. kết thúc phiên đang đỗ
    s = Sc(A, "2026-11-22T16:30", [A], 4)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Vincom Xuân Khánh", "209 đường 30/4, Ninh Kiều", "Ninh Kiều", 15000, 10)],
                  "sessions": [SES("park_01", "lot_01", "2026-11-22T14:00:00+07:00", 3, 45000)]}
    s.say("Em ra xe rồi, kết thúc phiên đỗ ở Vincom giúp em.",
          C(f"{A}.list_sessions"),
          C(f"{A}.end_session", session_id="park_01"))
    S.append(s)

    # 7. hai phiên, không rõ -> ask session_id
    s = Sc(A, "2026-11-23T18:00", [A], 5)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Royal City", "72A Nguyễn Trãi", "Thanh Xuân", 20000, 10), L("lot_02", "Bãi xe Times City", "458 Minh Khai", "Hai Bà Trưng", 20000, 5)],
                  "sessions": [SES("park_01", "lot_01", "2026-11-23T15:00:00+07:00", 4, 80000), SES("park_02", "lot_02", "2026-11-23T17:00:00+07:00", 2, 40000)]}
    s.say("Kết thúc phiên đỗ xe giúp tôi.",
          C(f"{A}.list_sessions"),
          ASK(f"{A}.end_session", "session_id"))
    S.append(s)

    # 8. bãi hết chỗ, user cho phép bãi khác gần đó -> chọn bãi còn chỗ trong kết quả find
    s = Sc(A, "2026-11-24T09:15", [A], 0)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Nhà hát Thành phố", "7 Công Trường Lam Sơn, Quận 1", "Quận 1", 30000, 0),
                           L("lot_02", "Bãi xe Công viên 23/9", "Phạm Ngũ Lão, Quận 1", "Quận 1", 15000, 40)], "sessions": []}
    s.say("Đặt chỗ ở Quận 1 gần Nhà hát Thành phố mười giờ sáng nay hai tiếng, bãi đó hết thì bãi nào trong Quận 1 cũng được.",
          C(f"{A}.find", near="Quận 1"),
          C(f"{A}.reserve", lot_id="lot_02", from_time=s.t(0, 10), hours=2))
    S.append(s)

    # 9. đặt + lịch họp (đỗ đúng giờ họp)
    s = Sc(A, "2026-11-25T07:50", [A, "calendar"], 1)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Keangnam", "Phạm Hùng, Nam Từ Liêm", "Nam Từ Liêm", 25000, 60)], "sessions": []}
    s.state["calendar"] = events(("evt_01", "Họp đối tác", s.t(0, 14), s.t(0, 16), "Keangnam"))
    s.say("Xem chiều nay họp ở Keangnam lúc mấy giờ, đặt chỗ đỗ đúng giờ đó, gửi hai tiếng.",
          C("calendar.list_events"),
          C(f"{A}.find", near="Keangnam"),
          C(f"{A}.reserve", lot_id="lot_01", from_time=s.t(0, 14), hours=2))
    S.append(s)

    # 10. history find -> reserve
    s = Sc(A, "2026-11-26T11:20", [A], 2)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Bệnh viện Đà Nẵng", "124 Hải Phòng", "Hải Châu", 10000, 15), L("lot_02", "Bãi xe Công viên 29/3", "Điện Biên Phủ", "Thanh Khê", 5000, 100)],
                  "sessions": []}
    s.user("Gần bệnh viện Đà Nẵng có bãi nào?")
    s.bot("Có Bãi xe Bệnh viện Đà Nẵng ở 124 Hải Phòng, 10.000đ/giờ, còn 15 chỗ ạ.", C(f"{A}.find", near="bệnh viện Đà Nẵng"))
    s.say("Đặt chỗ đó lúc hai giờ chiều nay, gửi ba tiếng.",
          C(f"{A}.reserve", lot_id="lot_01", from_time=s.t(0, 14), hours=3))
    S.append(s)

    # 11. [] - chat
    s = Sc(A, "2026-11-27T19:00", [A], 3)
    s.state[A] = {"lots": [], "sessions": []}
    s.say("Phí gửi xe trung tâm giờ đắt thật, ba chục một tiếng.")
    S.append(s)

    # 12. xem phiên đang đỗ (read)
    s = Sc(A, "2026-11-28T12:00", [A], 4)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Sense City", "1 Đại lộ Hòa Bình, Ninh Kiều", "Ninh Kiều", 10000, 20)],
                  "sessions": [SES("park_01", "lot_01", "2026-11-28T10:00:00+07:00", 4, 40000)]}
    s.say("Xe tôi đang đỗ ở đâu, đến mấy giờ hết hạn?",
          C(f"{A}.list_sessions"))
    S.append(s)

    # 13. đặt ngày mai + nhắc
    s = Sc(A, "2026-11-29T20:30", [A, "reminders"], 5)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe sân bay Nội Bài P1", "Nội Bài, Sóc Sơn", "Sóc Sơn", 15000, 200)], "sessions": []}
    s.state["reminders"] = reminders()
    s.say("Đặt chỗ đỗ ở sân bay Nội Bài từ năm giờ sáng mai, gửi mười hai tiếng, và nhắc tôi bốn giờ sáng dậy.",
          C(f"{A}.find", near="sân bay Nội Bài"),
          C(f"{A}.reserve", lot_id="lot_01", from_time=s.t(1, 5), hours=12),
          C("reminders.create", content="Dậy ra sân bay", time=s.t(1, 4)))
    S.append(s)

    # 14. kết thúc phiên rồi đặt chỗ mới nơi khác
    s = Sc(A, "2026-11-30T13:10", [A], 6)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Bitexco", "2 Hải Triều, Quận 1", "Quận 1", 35000, 5), L("lot_02", "Bãi xe Landmark 81", "720A Điện Biên Phủ, Bình Thạnh", "Bình Thạnh", 30000, 50)],
                  "sessions": [SES("park_01", "lot_01", "2026-11-30T09:00:00+07:00", 5, 175000)]}
    s.say("Kết thúc chỗ đỗ ở Bitexco, rồi đặt chỗ ở Landmark 81 lúc hai giờ chiều, hai tiếng.",
          C(f"{A}.list_sessions"),
          C(f"{A}.end_session", session_id="park_01"),
          C(f"{A}.find", near="Landmark 81"),
          C(f"{A}.reserve", lot_id="lot_02", from_time=s.t(0, 14), hours=2))
    S.append(s)

    # 15. [] - đã trả lời
    s = Sc(A, "2026-12-01T08:00", [A], 7)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Vincom Lê Thánh Tông", "1 Lê Thánh Tông", "Ngô Quyền", 15000, 25)], "sessions": []}
    s.user("Bãi Vincom Lê Thánh Tông còn chỗ không?")
    s.bot("Bãi xe Vincom Lê Thánh Tông còn 25 chỗ, 15.000đ/giờ ạ.", C(f"{A}.find", near="Vincom Lê Thánh Tông"))
    s.say("Còn nhiều thế thì lát qua không cần đặt trước đâu.")
    S.append(s)

    # 16. giọng Nam, "gửi nửa ngày" = 12 tiếng? Mơ hồ -> dùng "bốn tiếng"
    s = Sc(A, "2026-12-02T06:45", [A], 0)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Bệnh viện Chợ Rẫy", "201B Nguyễn Chí Thanh, Quận 5", "Quận 5", 10000, 30)], "sessions": []}
    s.say("Đặt dùm tui chỗ đậu xe ở Chợ Rẫy bảy giờ sáng nay, gửi bốn tiếng.",
          C(f"{A}.find", near="Chợ Rẫy"),
          C(f"{A}.reserve", lot_id="lot_01", from_time=s.t(0, 7), hours=4))
    S.append(s)

    # 17. tiếng Anh lẫn
    s = Sc(A, "2026-12-03T17:30", [A], 1)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Aeon Mall Long Biên", "27 Cổ Linh, Long Biên", "Long Biên", 10000, 80)], "sessions": []}
    s.say("Book chỗ parking ở Aeon Long Biên lúc sáu giờ tối nay, ba tiếng.",
          C(f"{A}.find", near="Aeon Long Biên"),
          C(f"{A}.reserve", lot_id="lot_01", from_time=s.t(0, 18), hours=3))
    S.append(s)

    # 18. [] - huỷ
    s = Sc(A, "2026-12-04T09:00", [A], 2)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Chợ Cồn", "290 Hùng Vương", "Hải Châu", 5000, 40)], "sessions": []}
    s.say("Đặt chỗ đỗ ở chợ Cồn... à thôi, hôm nay đi xe máy.")
    S.append(s)

    # 19. điều kiện: nếu còn chỗ thì đặt -> còn
    s = Sc(A, "2026-12-05T11:30", [A], 3)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Big C Huế", "Bà Triệu, TP Huế", "Phú Nhuận", 10000, 3)], "sessions": []}
    s.say("Big C Huế còn chỗ đỗ không, còn thì đặt một tiếng từ mười hai giờ trưa.",
          C(f"{A}.find", near="Big C Huế"),
          C(f"{A}.reserve", lot_id="lot_01", from_time=s.t(0, 12), hours=1))
    S.append(s)

    # 20. điều kiện: hết chỗ -> chỉ find
    s = Sc(A, "2026-12-05T11:30", [A], 3)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Big C Huế", "Bà Triệu, TP Huế", "Phú Nhuận", 10000, 0)], "sessions": []}
    s.say("Big C Huế còn chỗ đỗ không, còn thì đặt một tiếng từ mười hai giờ trưa.",
          C(f"{A}.find", near="Big C Huế"))
    S.append(s)

    # 21. [] - không app nào: muốn gia hạn phiên (không có tool)
    s = Sc(A, "2026-12-06T15:00", [A], 4)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Sense City", "1 Đại lộ Hòa Bình", "Ninh Kiều", 10000, 20)],
                  "sessions": [SES("park_01", "lot_01", "2026-12-06T13:00:00+07:00", 2, 20000)]}
    s.say("Gia hạn thêm một tiếng cho phiên đỗ ở Sense City giúp em.")
    S.append(s)

    # 22. đặt + nhắn bạn địa chỉ bãi
    s = Sc(A, "2026-12-07T18:20", [A, "chat_ott"], 5)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Phố cổ Hàng Bài", "2 Hàng Bài, Hoàn Kiếm", "Hoàn Kiếm", 30000, 6)], "sessions": []}
    s.state["chat_ott"] = chats(("chat_01", "Nhóm bạn cấp 3", "group"))
    s.say("Đặt chỗ đỗ ở Hàng Bài bảy giờ tối nay ba tiếng, rồi nhắn nhóm bạn cấp 3 là 'tao gửi xe ở 2 Hàng Bài nhé'.",
          C(f"{A}.find", near="Hàng Bài"),
          C(f"{A}.reserve", lot_id="lot_01", from_time=s.t(0, 19), hours=3),
          C("chat_ott.list_chats"),
          C("chat_ott.send_message", chat_id="chat_01", content="tao gửi xe ở 2 Hàng Bài nhé"))
    S.append(s)

    # 23. history: đã list sessions, kết thúc phiên được nhắc tới
    s = Sc(A, "2026-12-08T17:00", [A], 6)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Crescent Mall", "101 Tôn Dật Tiên, Quận 7", "Quận 7", 20000, 30)],
                  "sessions": [SES("park_01", "lot_01", "2026-12-08T14:00:00+07:00", 4, 80000)]}
    s.user("Xe tôi đỗ ở Crescent đến mấy giờ?")
    s.bot("Phiên đỗ ở Bãi xe Crescent Mall từ 14:00, 4 tiếng, hết hạn 18:00 ạ.", C(f"{A}.list_sessions"))
    s.say("Tôi về sớm rồi, kết thúc luôn đi.",
          C(f"{A}.end_session", session_id="park_01"))
    S.append(s)

    # 24. ngày mai theo thứ
    s = Sc(A, "2026-12-09T21:00", [A], 7)
    w = s.next_wd(5)
    s.state[A] = {"lots": [L("lot_01", "Bãi xe Cát Bi Plaza", "1 Lê Hồng Phong", "Ngô Quyền", 10000, 40)], "sessions": []}
    s.say(f"Thứ bảy này đặt chỗ ở Cát Bi Plaza từ chín giờ sáng, gửi năm tiếng.",
          C(f"{A}.find", near="Cát Bi Plaza"),
          C(f"{A}.reserve", lot_id="lot_01", from_time=s.t(w, 9), hours=5))
    S.append(s)

    return S
