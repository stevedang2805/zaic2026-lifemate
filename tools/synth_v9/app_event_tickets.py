from common import *

A = "event_tickets"


def E(i, name, cat, date, time, venue, price, avail):
    return {"id": i, "name": name, "category": cat, "date": date, "time": time, "venue": venue, "price": price, "available": avail}


def build():
    S = []

    # 1. tìm theo tên -> đặt 2 vé
    s = Sc(A, "2026-11-18T20:00", [A], 0)
    s.state[A] = {"events": [E("ev_01", "Liveshow Hà Anh Tuấn - Chân Trời Rực Rỡ", "ca nhạc", s.d(9), "20:00", "Nhà hát Hòa Bình", 1500000, 40),
                             E("ev_02", "Kịch Ngày Xửa Ngày Xưa", "kịch", s.d(5), "19:30", "Nhà hát Bến Thành", 350000, 100)],
                  "bookings": []}
    s.say("Đặt hai vé liveshow Hà Anh Tuấn cho em với.",
          C(f"{A}.search", query="Hà Anh Tuấn"),
          C(f"{A}.book", event_id="ev_01", quantity=2))
    S.append(s)

    # 2. tìm theo loại (read)
    s = Sc(A, "2026-11-19T12:00", [A], 1)
    s.state[A] = {"events": [E("ev_01", "Đêm nhạc Trịnh", "ca nhạc", s.d(3), "20:00", "Nhà hát Lớn", 800000, 20),
                             E("ev_02", "Triển lãm tranh Đông Dương", "triển lãm", s.d(1), "09:00", "Bảo tàng Mỹ thuật", 50000, 500),
                             E("ev_03", "Hà Nội Rock Night", "ca nhạc", s.d(10), "19:00", "Cung Việt Xô", 400000, 0)],
                  "bookings": []}
    s.say("Cuối tháng này có show ca nhạc gì ở Hà Nội không?",
          C(f"{A}.search", query="ca nhạc"))
    S.append(s)

    # 3. thiếu số vé -> ask quantity
    s = Sc(A, "2026-11-20T18:30", [A], 2)
    s.state[A] = {"events": [E("ev_01", "Lễ hội pháo hoa quốc tế Đà Nẵng", "lễ hội", s.d(12), "20:00", "Bờ sông Hàn", 500000, 300)],
                  "bookings": []}
    s.say("Đặt vé xem pháo hoa quốc tế giúp em.",
          C(f"{A}.search", query="pháo hoa quốc tế"),
          ASK(f"{A}.book", "quantity"))
    S.append(s)

    # 4. hết vé -> chỉ search
    s = Sc(A, "2026-11-21T09:00", [A], 3)
    s.state[A] = {"events": [E("ev_01", "Festival Huế - Đêm Hoàng Cung", "lễ hội", s.d(4), "19:00", "Đại Nội", 300000, 0)],
                  "bookings": []}
    s.say("Lấy cho anh bốn vé Đêm Hoàng Cung.",
          C(f"{A}.search", query="Đêm Hoàng Cung"))
    S.append(s)

    # 5. đặt + thêm lịch
    s = Sc(A, "2026-11-22T10:10", [A, "calendar"], 4)
    s.state[A] = {"events": [E("ev_01", "Cải lương Tiếng Trống Mê Linh", "kịch", s.d(6), "19:30", "Nhà hát Tây Đô", 200000, 80)],
                  "bookings": []}
    s.state["calendar"] = events()
    s.say("Đặt ba vé Tiếng Trống Mê Linh rồi thêm vào lịch giúp mẹ nha.",
          C(f"{A}.search", query="Tiếng Trống Mê Linh"),
          C(f"{A}.book", event_id="ev_01", quantity=3),
          C("calendar.create_event", title="Cải lương Tiếng Trống Mê Linh", start=s.t(6, 19, 30), end=s.t(6, 20, 30), location="Nhà hát Tây Đô"))
    S.append(s)

    # 6. history search -> book
    s = Sc(A, "2026-11-23T21:00", [A], 5)
    s.state[A] = {"events": [E("ev_01", "Hội chợ sách Hà Nội", "triển lãm", s.d(2), "08:00", "Hoàng thành Thăng Long", 0, 1000),
                             E("ev_02", "Stand-up comedy Sài Gòn Tếu", "hài kịch", s.d(7), "20:00", "Idecaf", 250000, 30)],
                  "bookings": []}
    s.user("Tuần này có sự kiện gì hay?")
    s.bot("Có Hội chợ sách Hà Nội (miễn phí) và show Stand-up comedy Sài Gòn Tếu ở Idecaf ạ.", C(f"{A}.search"))
    s.say("Lấy hai vé cái show hài đi.",
          C(f"{A}.book", event_id="ev_02", quantity=2))
    S.append(s)

    # 7. liệt kê tất cả -> search {}
    s = Sc(A, "2026-11-24T19:15", [A], 6)
    s.state[A] = {"events": [E("ev_01", "Chung kết bóng đá sinh viên", "thể thao", s.d(3), "16:00", "SVĐ Cần Thơ", 50000, 200)],
                  "bookings": []}
    s.say("Có sự kiện gì đang bán vé không em?",
          C(f"{A}.search"))
    S.append(s)

    # 8. hai sự kiện gần giống -> ask event_id
    s = Sc(A, "2026-11-25T08:40", [A], 7)
    s.state[A] = {"events": [E("ev_01", "Phim Mai - suất 19:00", "phim", s.d(0), "19:00", "CGV Vincom", 90000, 50),
                             E("ev_02", "Phim Mai - suất 21:30", "phim", s.d(0), "21:30", "CGV Vincom", 90000, 60)],
                  "bookings": []}
    s.say("Đặt hai vé phim Mai tối nay.",
          C(f"{A}.search", query="phim Mai"),
          ASK(f"{A}.book", "event_id"))
    S.append(s)

    # 9. nói rõ suất -> không ask
    s = Sc(A, "2026-11-25T08:40", [A], 7)
    s.state[A] = {"events": [E("ev_01", "Phim Mai - suất 19:00", "phim", s.d(0), "19:00", "CGV Vincom", 90000, 50),
                             E("ev_02", "Phim Mai - suất 21:30", "phim", s.d(0), "21:30", "CGV Vincom", 90000, 60)],
                  "bookings": []}
    s.say("Đặt hai vé phim Mai suất chín rưỡi tối nay.",
          C(f"{A}.search", query="phim Mai"),
          C(f"{A}.book", event_id="ev_02", quantity=2))
    S.append(s)

    # 10. [] - chat
    s = Sc(A, "2026-11-26T22:00", [A], 0)
    s.state[A] = {"events": [], "bookings": []}
    s.say("Show hôm qua đã thật sự, giọng live hay hơn cả thu âm.")
    S.append(s)

    # 11. điều kiện: nếu còn vé thì đặt -> còn
    s = Sc(A, "2026-11-27T11:30", [A], 1)
    s.state[A] = {"events": [E("ev_01", "Concert Mỹ Tâm - My Soul 1981", "ca nhạc", s.d(8), "19:30", "Sân vận động Mỹ Đình", 2000000, 15)],
                  "bookings": []}
    s.say("Concert Mỹ Tâm còn vé không, còn thì đặt cho chị hai vé.",
          C(f"{A}.search", query="Mỹ Tâm"),
          C(f"{A}.book", event_id="ev_01", quantity=2))
    S.append(s)

    # 12. điều kiện: hết vé -> chỉ search
    s = Sc(A, "2026-11-27T11:30", [A], 1)
    s.state[A] = {"events": [E("ev_01", "Concert Mỹ Tâm - My Soul 1981", "ca nhạc", s.d(8), "19:30", "Sân vận động Mỹ Đình", 2000000, 0)],
                  "bookings": []}
    s.say("Concert Mỹ Tâm còn vé không, còn thì đặt cho chị hai vé.",
          C(f"{A}.search", query="Mỹ Tâm"))
    S.append(s)

    # 13. đặt + nhắn bạn
    s = Sc(A, "2026-11-28T17:20", [A, "chat_ott"], 2)
    s.state[A] = {"events": [E("ev_01", "Giải chạy Đà Nẵng Marathon", "thể thao", s.d(13), "04:30", "Công viên Biển Đông", 600000, 500)],
                  "bookings": []}
    s.state["chat_ott"] = chats(("chat_01", "Team chạy bộ", "group"), ("chat_02", "Mẹ", "direct"))
    s.say("Đăng ký hai suất Đà Nẵng Marathon, rồi nhắn nhóm Team chạy bộ là 'đã đăng ký 2 suất nhé'.",
          C(f"{A}.search", query="Đà Nẵng Marathon"),
          C(f"{A}.book", event_id="ev_01", quantity=2),
          C("chat_ott.list_chats"),
          C("chat_ott.send_message", chat_id="chat_01", content="đã đăng ký 2 suất nhé"))
    S.append(s)

    # 14. đặt vé + nhắc trước 1 tiếng
    s = Sc(A, "2026-11-29T09:00", [A, "reminders"], 3)
    s.state[A] = {"events": [E("ev_01", "Ca Huế trên sông Hương", "ca nhạc", s.d(1), "19:00", "Bến Tòa Khâm", 150000, 25)],
                  "bookings": []}
    s.state["reminders"] = reminders()
    s.say("Đặt bốn vé ca Huế trên sông Hương tối mai, nhắc tôi trước giờ diễn một tiếng.",
          C(f"{A}.search", query="ca Huế trên sông Hương"),
          C(f"{A}.book", event_id="ev_01", quantity=4),
          C("reminders.create", content="Đi xem ca Huế trên sông Hương", time=s.t(1, 18)))
    S.append(s)

    # 15. tìm theo địa điểm
    s = Sc(A, "2026-11-30T14:00", [A], 4)
    s.state[A] = {"events": [E("ev_01", "Đêm nhạc acoustic", "ca nhạc", s.d(2), "20:00", "Nhà văn hóa Thanh Niên", 100000, 60),
                             E("ev_02", "Workshop làm gốm", "workshop", s.d(4), "14:00", "Nhà văn hóa Thanh Niên", 200000, 12)],
                  "bookings": []}
    s.say("Ở Nhà văn hóa Thanh Niên sắp có gì?",
          C(f"{A}.search", query="Nhà văn hóa Thanh Niên"))
    S.append(s)

    # 16. [] - đã trả lời
    s = Sc(A, "2026-11-30T14:00", [A], 4)
    s.state[A] = {"events": [E("ev_01", "Workshop làm gốm", "workshop", s.d(4), "14:00", "Nhà văn hóa Thanh Niên", 200000, 12)],
                  "bookings": []}
    s.user("Workshop làm gốm giá nhiêu?")
    s.bot("Workshop làm gốm 200.000đ một vé, còn 12 chỗ ạ.", C(f"{A}.search", query="workshop làm gốm"))
    s.say("Hai trăm thôi hả, cũng ok đó.")
    S.append(s)

    # 17. sửa lời: "ba vé à không bốn"
    s = Sc(A, "2026-12-01T20:30", [A], 5)
    s.state[A] = {"events": [E("ev_01", "Xiếc Làng Tôi", "xiếc", s.d(5), "18:00", "Nhà hát Lớn Hà Nội", 700000, 50)],
                  "bookings": []}
    s.say("Đặt ba vé xiếc Làng Tôi, à mà bốn vé, có cả bà nội nữa.",
          C(f"{A}.search", query="Làng Tôi"),
          C(f"{A}.book", event_id="ev_01", quantity=4))
    S.append(s)

    # 18. một vé, giọng Nam
    s = Sc(A, "2026-12-02T08:15", [A], 6)
    s.state[A] = {"events": [E("ev_01", "Hội thảo AI cho doanh nghiệp", "hội thảo", s.d(3), "08:30", "GEM Center", 0, 200)],
                  "bookings": []}
    s.say("Đăng ký cho tui một chỗ hội thảo AI cho doanh nghiệp nghen.",
          C(f"{A}.search", query="AI cho doanh nghiệp"),
          C(f"{A}.book", event_id="ev_01", quantity=1))
    S.append(s)

    # 19. [] - không app nào: muốn huỷ vé (không có tool huỷ)
    s = Sc(A, "2026-12-03T10:00", [A], 7)
    s.state[A] = {"events": [E("ev_01", "Xiếc Làng Tôi", "xiếc", s.d(5), "18:00", "Nhà hát Lớn", 700000, 46)],
                  "bookings": [{"id": "tk_01", "event_id": "ev_01", "quantity": 4, "total": 2800000, "status": "confirmed"}]}
    s.say("Huỷ bốn vé xiếc hôm trước giúp anh, bận không đi được.")
    S.append(s)

    # 20. tiếng Anh lẫn
    s = Sc(A, "2026-12-04T19:00", [A], 0)
    s.state[A] = {"events": [E("ev_01", "Coldplay Tribute Night", "ca nhạc", s.d(9), "20:00", "Hard Rock Cafe", 450000, 70)],
                  "bookings": []}
    s.say("Book hai ticket Coldplay Tribute Night giùm.",
          C(f"{A}.search", query="Coldplay Tribute Night"),
          C(f"{A}.book", event_id="ev_01", quantity=2))
    S.append(s)

    # 21. đặt vé và ghi chú số ghế / tổng tiền
    s = Sc(A, "2026-12-05T13:40", [A, "notes"], 1)
    s.state[A] = {"events": [E("ev_01", "Vở kịch Số Đỏ", "kịch", s.d(6), "20:00", "Nhà hát Tuổi Trẻ", 300000, 90)],
                  "bookings": []}
    s.state["notes"] = notes()
    s.say("Đặt năm vé kịch Số Đỏ cho cả phòng, xong tạo ghi chú 'Tiền vé Số Đỏ' nội dung là mỗi người ba trăm nghìn.",
          C(f"{A}.search", query="Số Đỏ"),
          C(f"{A}.book", event_id="ev_01", quantity=5),
          C("notes.create", title="Tiền vé Số Đỏ", content="Mỗi người ba trăm nghìn"))
    S.append(s)

    # 22. [] - huỷ ý định
    s = Sc(A, "2026-12-06T16:00", [A], 2)
    s.state[A] = {"events": [E("ev_01", "Đêm nhạc Lam Trường", "ca nhạc", s.d(7), "20:00", "Nhà hát Trưng Vương", 900000, 30)],
                  "bookings": []}
    s.say("Đặt vé Lam Trường... ờ mà thôi, hôm đó em trực rồi.")
    S.append(s)

    # 23. đặt theo sự kiện thể thao + tạo lịch dùng giờ từ kết quả
    s = Sc(A, "2026-12-07T09:30", [A, "calendar"], 3)
    s.state[A] = {"events": [E("ev_01", "V-League: Huế vs Hà Nội FC", "thể thao", s.d(6), "18:00", "SVĐ Tự Do", 80000, 2000)],
                  "bookings": []}
    s.state["calendar"] = events()
    s.say("Lấy hai vé trận Huế gặp Hà Nội FC rồi bỏ vào lịch giúp tôi.",
          C(f"{A}.search", query="Huế vs Hà Nội FC"),
          C(f"{A}.book", event_id="ev_01", quantity=2),
          C("calendar.create_event", title="V-League: Huế vs Hà Nội FC", start=s.t(6, 18), end=s.t(6, 19), location="SVĐ Tự Do"))
    S.append(s)

    return S
