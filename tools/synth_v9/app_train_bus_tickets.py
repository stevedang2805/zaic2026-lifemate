from common import *

A = "train_bus_tickets"


def T(i, typ, op, org, dst, date, dep, arr, price, seats):
    return {"id": i, "type": typ, "operator": op, "origin": org, "destination": dst, "date": date, "depart": dep, "arrive": arr, "price": price, "seats_left": seats}


def build():
    S = []

    # 1. tìm tàu ngày mai -> đặt 2 vé chuyến sáng
    s = Sc(A, "2026-11-18T19:00", [A], 1)  # Hà Nội
    s.state[A] = {"trips": [T("trip_01", "train", "Đường sắt Việt Nam SE1", "Hà Nội", "Đà Nẵng", s.d(1), "06:00", "21:30", 650000, 20),
                            T("trip_02", "train", "Đường sắt Việt Nam SE3", "Hà Nội", "Đà Nẵng", s.d(1), "19:20", "11:00", 720000, 8),
                            T("trip_03", "bus", "Hải Vân Express", "Hà Nội", "Đà Nẵng", s.d(1), "18:00", "09:00", 450000, 30)],
                  "bookings": []}
    s.say("Đặt hai vé tàu đi Đà Nẵng sáng mai cho anh, chuyến sớm nhất.",
          C(f"{A}.search", origin="Hà Nội", destination="Đà Nẵng", date=s.d(1), type="train"),
          C(f"{A}.book", trip_id="trip_01", seats=2))
    S.append(s)

    # 2. xe khách, điểm đi là thành phố profile, ngày thứ sáu
    s = Sc(A, "2026-11-19T08:30", [A], 0)  # TP.HCM, thứ năm
    f = s.next_wd(4)
    s.state[A] = {"trips": [T("trip_01", "bus", "Phương Trang", "TP.HCM", "Đà Lạt", s.d(f), "22:00", "05:00", 320000, 12),
                            T("trip_02", "bus", "Thành Bưởi", "TP.HCM", "Đà Lạt", s.d(f), "23:00", "06:00", 300000, 0)],
                  "bookings": []}
    s.say("Tìm xe khách đi Đà Lạt tối thứ sáu, còn chỗ thì đặt cho em một vé Phương Trang.",
          C(f"{A}.search", origin="TP.HCM", destination="Đà Lạt", date=s.d(f), type="bus"),
          C(f"{A}.book", trip_id="trip_01", seats=1))
    S.append(s)

    # 3. chỉ tìm (read), không nói loại
    s = Sc(A, "2026-11-20T10:00", [A], 2)  # Đà Nẵng
    s.state[A] = {"trips": [T("trip_01", "train", "SE2", "Đà Nẵng", "Huế", s.d(2), "08:00", "10:40", 120000, 50),
                            T("trip_02", "bus", "Limousine Hoàng Long", "Đà Nẵng", "Huế", s.d(2), "09:00", "11:30", 150000, 6)],
                  "bookings": []}
    s.say("Xem giúp chị ngày kia có chuyến nào ra Huế, tàu hay xe gì cũng được.",
          C(f"{A}.search", origin="Đà Nẵng", destination="Huế", date=s.d(2)))
    S.append(s)

    # 4. thiếu ngày -> ask date
    s = Sc(A, "2026-11-21T14:20", [A], 3)
    s.state[A] = {"trips": [T("trip_01", "train", "SE4", "Huế", "Hà Nội", s.d(3), "15:00", "05:30", 700000, 10)], "bookings": []}
    s.say("Đặt cho tôi một vé tàu ra Hà Nội.",
          ASK(f"{A}.search", "date"))
    S.append(s)

    # 5. thiếu số ghế -> search rồi ask seats
    s = Sc(A, "2026-11-22T09:10", [A], 4)  # Cần Thơ
    s.state[A] = {"trips": [T("trip_01", "bus", "Phương Trang", "Cần Thơ", "TP.HCM", s.d(1), "07:00", "10:30", 165000, 25)], "bookings": []}
    s.say("Mai cả nhà lên Sài Gòn, đặt vé xe Phương Trang sáng mai giúp em.",
          C(f"{A}.search", origin="Cần Thơ", destination="TP.HCM", date=s.d(1), type="bus"),
          ASK(f"{A}.book", "seats"))
    S.append(s)

    # 6. xem vé đã đặt (read)
    s = Sc(A, "2026-11-23T11:00", [A], 5)
    s.state[A] = {"trips": [T("trip_01", "train", "SE1", "Hà Nội", "Vinh", s.d(4), "06:00", "12:00", 350000, 10)],
                  "bookings": [{"id": "tk_01", "trip_id": "trip_01", "seats": 2, "total": 700000, "status": "confirmed"}]}
    s.say("Tôi đã đặt những vé nào rồi nhỉ?",
          C(f"{A}.my_bookings"))
    S.append(s)

    # 7. huỷ vé -> my_bookings rồi cancel
    s = Sc(A, "2026-11-24T16:45", [A], 6)
    s.state[A] = {"trips": [T("trip_01", "bus", "Kumho", "TP.HCM", "Vũng Tàu", s.d(2), "08:00", "10:00", 180000, 15)],
                  "bookings": [{"id": "tk_01", "trip_id": "trip_01", "seats": 2, "total": 360000, "status": "confirmed"}]}
    s.say("Huỷ cái vé đi Vũng Tàu giùm em, bận đột xuất rồi.",
          C(f"{A}.my_bookings"),
          C(f"{A}.cancel", booking_id="tk_01"))
    S.append(s)

    # 8. hai vé, không rõ huỷ vé nào -> ask booking_id
    s = Sc(A, "2026-11-25T20:00", [A], 7)
    s.state[A] = {"trips": [T("trip_01", "bus", "Hoàng Long", "Hải Phòng", "Hà Nội", s.d(1), "07:00", "09:00", 120000, 20),
                            T("trip_02", "bus", "Hoàng Long", "Hải Phòng", "Hà Nội", s.d(3), "07:00", "09:00", 120000, 20)],
                  "bookings": [{"id": "tk_01", "trip_id": "trip_01", "seats": 1, "total": 120000, "status": "confirmed"},
                               {"id": "tk_02", "trip_id": "trip_02", "seats": 1, "total": 120000, "status": "confirmed"}]}
    s.say("Huỷ cho anh một vé đi Hà Nội.",
          C(f"{A}.my_bookings"),
          ASK(f"{A}.cancel", "booking_id"))
    S.append(s)

    # 9. history search -> book chuyến tối
    s = Sc(A, "2026-11-26T15:30", [A], 1)
    s.state[A] = {"trips": [T("trip_01", "train", "SE5", "Hà Nội", "Hải Phòng", s.d(2), "06:10", "08:40", 95000, 40),
                            T("trip_02", "train", "SE7", "Hà Nội", "Hải Phòng", s.d(2), "18:15", "20:45", 95000, 35)],
                  "bookings": []}
    s.user("Ngày kia có tàu nào đi Hải Phòng?")
    s.bot("Ngày kia có SE5 lúc 6:10 và SE7 lúc 18:15, giá 95.000đ ạ.", C(f"{A}.search", origin="Hà Nội", destination="Hải Phòng", date=s.d(2), type="train"))
    s.say("Lấy ba vé chuyến chiều.",
          C(f"{A}.book", trip_id="trip_02", seats=3))
    S.append(s)

    # 10. đặt + lịch
    s = Sc(A, "2026-11-27T21:10", [A, "calendar"], 2)
    s.state[A] = {"trips": [T("trip_01", "train", "SE1", "Đà Nẵng", "Nha Trang", s.d(5), "13:00", "22:30", 420000, 18)], "bookings": []}
    s.state["calendar"] = events()
    s.say(f"Đặt hai vé tàu vào Nha Trang {s.wd(5)} này, rồi tạo lịch 'Đi Nha Trang' đúng giờ tàu chạy.",
          C(f"{A}.search", origin="Đà Nẵng", destination="Nha Trang", date=s.d(5), type="train"),
          C(f"{A}.book", trip_id="trip_01", seats=2),
          C("calendar.create_event", title="Đi Nha Trang", start=s.t(5, 13), end=s.t(5, 14)))
    S.append(s)

    # 11. không có chuyến -> search rỗng, dừng
    s = Sc(A, "2026-11-28T09:00", [A], 3)
    s.state[A] = {"trips": [T("trip_01", "train", "SE2", "Huế", "Hà Nội", s.d(2), "15:00", "05:30", 700000, 10)], "bookings": []}
    s.say("Mai có tàu nào ra Hà Nội không, có thì đặt một vé.",
          C(f"{A}.search", origin="Huế", destination="Hà Nội", date=s.d(1), type="train"))
    S.append(s)

    # 12. [] - chat
    s = Sc(A, "2026-11-29T22:00", [A], 4)
    s.state[A] = {"trips": [], "bookings": []}
    s.say("Đi xe đêm mệt thật, lần sau chắc đi tàu cho khoẻ.")
    S.append(s)

    # 13. [] - không app nào: vé máy bay
    s = Sc(A, "2026-11-29T22:00", [A], 4)
    s.state[A] = {"trips": [], "bookings": []}
    s.say("Đặt cho em vé máy bay đi Hà Nội sáng mai.")
    S.append(s)

    # 14. đặt + nhắc trước 2 tiếng
    s = Sc(A, "2026-11-30T08:20", [A, "reminders"], 5)
    s.state[A] = {"trips": [T("trip_01", "bus", "Sao Việt", "Hà Nội", "Sa Pa", s.d(1), "22:00", "04:00", 350000, 9)], "bookings": []}
    s.state["reminders"] = reminders()
    s.say("Đặt hai vé xe đi Sa Pa tối mai, nhắc tôi trước giờ xe chạy hai tiếng.",
          C(f"{A}.search", origin="Hà Nội", destination="Sa Pa", date=s.d(1), type="bus"),
          C(f"{A}.book", trip_id="trip_01", seats=2),
          C("reminders.create", content="Chuẩn bị ra xe đi Sa Pa", time=s.t(1, 20)))
    S.append(s)

    # 15. huỷ vé rồi đặt lại ngày khác
    s = Sc(A, "2026-12-01T10:30", [A], 6)
    s.state[A] = {"trips": [T("trip_01", "train", "SE1", "TP.HCM", "Nha Trang", s.d(2), "06:00", "13:30", 380000, 20),
                            T("trip_02", "train", "SE1", "TP.HCM", "Nha Trang", s.d(4), "06:00", "13:30", 380000, 20)],
                  "bookings": [{"id": "tk_01", "trip_id": "trip_01", "seats": 1, "total": 380000, "status": "confirmed"}]}
    s.say(f"Huỷ vé tàu đi Nha Trang ngày kia, đổi sang {s.wd(4)} cũng chuyến sáng đó, một vé.",
          C(f"{A}.my_bookings"),
          C(f"{A}.cancel", booking_id="tk_01"),
          C(f"{A}.search", origin="TP.HCM", destination="Nha Trang", date=s.d(4), type="train"),
          C(f"{A}.book", trip_id="trip_02", seats=1))
    S.append(s)

    # 16. giọng miền Tây, "Sài Gòn" -> origin như người nói
    s = Sc(A, "2026-12-02T07:00", [A], 0)
    s.state[A] = {"trips": [T("trip_01", "bus", "Futa", "TP.HCM", "Cần Thơ", s.d(0), "13:00", "16:30", 165000, 30)], "bookings": []}
    s.say("Đặt dùm tui hai vé xe từ Sài Gòn dìa Cần Thơ trưa nay.",
          C(f"{A}.search", origin="Sài Gòn", destination="Cần Thơ", date=s.d(0), type="bus"),
          C(f"{A}.book", trip_id="trip_01", seats=2))
    S.append(s)

    # 17. [] - đã trả lời
    s = Sc(A, "2026-12-03T18:00", [A], 1)
    s.state[A] = {"trips": [T("trip_01", "train", "SE1", "Hà Nội", "Vinh", s.d(1), "06:00", "12:00", 350000, 10)], "bookings": []}
    s.user("Mai tàu đi Vinh mấy giờ?")
    s.bot("Mai có tàu SE1 khởi hành 6:00, đến Vinh 12:00, giá 350.000đ ạ.", C(f"{A}.search", origin="Hà Nội", destination="Vinh", date=s.d(1), type="train"))
    s.say("Sáu giờ sáng hả, sớm thế.")
    S.append(s)

    # 18. history: đã hỏi -> đặt 1 vé
    s = Sc(A, "2026-12-03T18:00", [A], 1)
    s.state[A] = {"trips": [T("trip_01", "train", "SE1", "Hà Nội", "Vinh", s.d(1), "06:00", "12:00", 350000, 10)], "bookings": []}
    s.user("Mai tàu đi Vinh mấy giờ?")
    s.bot("Mai có tàu SE1 khởi hành 6:00, đến Vinh 12:00, giá 350.000đ ạ.", C(f"{A}.search", origin="Hà Nội", destination="Vinh", date=s.d(1), type="train"))
    s.say("Ừ đặt một vé đi.",
          C(f"{A}.book", trip_id="trip_01", seats=1))
    S.append(s)

    # 19. ngày cụ thể đọc "mùng năm tháng mười hai" (phải trong bảng lịch ±14 ngày)
    s = Sc(A, "2026-11-26T09:00", [A], 2)
    s.state[A] = {"trips": [T("trip_01", "bus", "Hải Vân", "Đà Nẵng", "Quy Nhơn", "2026-12-05", "07:00", "12:00", 220000, 20)], "bookings": []}
    s.say("Đặt một vé xe đi Quy Nhơn ngày mùng năm tháng mười hai.",
          C(f"{A}.search", origin="Đà Nẵng", destination="Quy Nhơn", date="2026-12-05", type="bus"),
          C(f"{A}.book", trip_id="trip_01", seats=1))
    S.append(s)

    # 20. chọn theo giá rẻ nhất trong nhiều chuyến
    s = Sc(A, "2026-12-04T12:00", [A], 3)
    s.state[A] = {"trips": [T("trip_01", "bus", "Phúc Xuyên", "Huế", "Đà Nẵng", s.d(1), "08:00", "10:30", 130000, 10),
                            T("trip_02", "bus", "HAV Limousine", "Huế", "Đà Nẵng", s.d(1), "09:00", "11:00", 200000, 5),
                            T("trip_03", "bus", "Hạnh Cafe", "Huế", "Đà Nẵng", s.d(1), "10:00", "12:30", 110000, 15)],
                  "bookings": []}
    s.say("Mai vào Đà Nẵng, tìm xe khách rồi đặt cho tôi một vé chuyến rẻ nhất.",
          C(f"{A}.search", origin="Huế", destination="Đà Nẵng", date=s.d(1), type="bus"),
          C(f"{A}.book", trip_id="trip_03", seats=1))
    S.append(s)

    # 21. đặt + nhắn người nhà giờ đến
    s = Sc(A, "2026-12-05T15:40", [A, "chat_ott"], 4)
    s.state[A] = {"trips": [T("trip_01", "bus", "Phương Trang", "Cần Thơ", "TP.HCM", s.d(1), "05:00", "08:30", 165000, 20)], "bookings": []}
    s.state["chat_ott"] = chats(("chat_01", "Anh Hai", "direct"))
    s.say("Đặt một vé xe lên Sài Gòn chuyến năm giờ sáng mai, rồi nhắn Anh Hai là 'mai 8 rưỡi em tới bến xe miền Tây'.",
          C(f"{A}.search", origin="Cần Thơ", destination="Sài Gòn", date=s.d(1), type="bus"),
          C(f"{A}.book", trip_id="trip_01", seats=1),
          C("chat_ott.list_chats"),
          C("chat_ott.send_message", chat_id="chat_01", content="mai 8 rưỡi em tới bến xe miền Tây"))
    S.append(s)

    # 22. [] - huỷ ý định
    s = Sc(A, "2026-12-06T09:00", [A], 5)
    s.state[A] = {"trips": [], "bookings": []}
    s.say("Đặt vé tàu đi Lào Cai... à mà thôi, để coi lại lịch nghỉ đã.")
    S.append(s)

    # 23. tiếng Anh lẫn + tuần sau
    s = Sc(A, "2026-12-07T20:20", [A], 6)
    n = s.next_wd(5, next_week=True)
    s.state[A] = {"trips": [T("trip_01", "train", "SE19", "Hà Nội", "Đà Nẵng", s.d(n), "20:00", "12:00", 780000, 14)], "bookings": []}
    s.say("Book cho em hai vé train đi Đà Nẵng tối thứ bảy tuần sau.",
          C(f"{A}.search", origin="Hà Nội", destination="Đà Nẵng", date=s.d(n), type="train"),
          C(f"{A}.book", trip_id="trip_01", seats=2))
    S.append(s)

    # 24. đọc vé đã đặt rồi huỷ (history)
    s = Sc(A, "2026-12-08T11:30", [A], 7)
    s.state[A] = {"trips": [T("trip_01", "bus", "Hoàng Long", "Hải Phòng", "Hà Nội", s.d(2), "07:00", "09:00", 120000, 20)],
                  "bookings": [{"id": "tk_01", "trip_id": "trip_01", "seats": 2, "total": 240000, "status": "confirmed"}]}
    s.user("Xem vé xe tôi đã đặt.")
    s.bot("Bạn có 1 vé: Hoàng Long Hải Phòng - Hà Nội, 7:00 ngày kia, 2 ghế, mã tk_01 ạ.", C(f"{A}.my_bookings"))
    s.say("Huỷ vé đó đi, sếp đổi lịch rồi.",
          C(f"{A}.cancel", booking_id="tk_01"))
    S.append(s)

    return S
