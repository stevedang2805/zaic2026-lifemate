"""Tính giờ chính xác từ lời nói (lỗi val v9: '8 giờ kém 15 tối mai' -> 20:59; '45 phút nữa' -> sai phút).
Quy đổi: 'X giờ kém Y' = (X-1):(60-Y); 'rưỡi' = :30; 'N phút/tiếng nữa' = current_time + N; sáng/trưa/chiều/tối/đêm theo 24h."""
from common import *

A = "time"


def build():
    S = []
    R = lambda: reminders()

    # ---- reminders: "N phút nữa" / "N tiếng nữa" ----
    for now, n, unit, content, prof in [
        ("2026-11-18T13:10", 45, "phút", "gọi lại cho khách", 0),
        ("2026-11-19T09:47", 20, "phút", "tắt bếp", 1),
        ("2026-11-20T16:05", 90, "phút", "đi đón con", 2),
        ("2026-11-21T22:40", 30, "phút", "uống thuốc", 3),
        ("2026-11-22T07:15", 120, "phút", "rút đồ phơi", 4),
        ("2026-11-23T11:33", 15, "phút", "lấy cơm trong lò vi sóng", 5),
        ("2026-11-24T14:50", 180, "phút", "nộp báo cáo", 6),
        ("2026-11-25T23:20", 50, "phút", "kiểm tra máy giặt", 7),
    ]:
        s = Sc(A, now, ["reminders", "alarm"], prof)
        s.state["reminders"] = R(); s.state["alarm"] = alarms()
        spoken = {45: "bốn lăm phút nữa", 20: "hai mươi phút nữa", 90: "một tiếng rưỡi nữa", 30: "nửa tiếng nữa",
                  120: "hai tiếng nữa", 15: "mười lăm phút nữa", 180: "ba tiếng nữa", 50: "năm mươi phút nữa"}[n]
        s.say(f"{spoken.capitalize()} nhắc mình {content} nhé.", C("reminders.create", content=content, time=plus(s, n)))
        S.append(s)

    # ---- reminders: "X giờ kém Y" ----
    for now, dd, h, m, spoken, content, prof in [
        ("2026-11-18T10:00", 1, 19, 45, "tám giờ kém mười lăm tối mai", "uống thuốc", 0),
        ("2026-11-19T21:00", 1, 6, 50, "bảy giờ kém mười sáng mai", "đưa con đi học", 1),
        ("2026-11-20T08:30", 0, 16, 55, "năm giờ kém năm chiều nay", "họp online với đối tác", 2),
        ("2026-11-21T12:00", 0, 13, 40, "hai giờ kém hai mươi chiều nay", "gửi hợp đồng", 3),
        ("2026-11-22T19:00", 1, 11, 45, "mười hai giờ kém mười lăm trưa mai", "đặt cơm trưa", 4),
        ("2026-11-23T06:00", 0, 21, 50, "mười giờ kém mười tối nay", "khoá cửa", 5),
    ]:
        s = Sc(A, now, ["reminders"], prof)
        s.state["reminders"] = R()
        s.say(f"Nhắc tôi {content} lúc {spoken} nha.", C("reminders.create", content=content, time=s.t(dd, h, m)))
        S.append(s)

    # ---- reminders: buổi trong ngày -> 24h ----
    for now, dd, h, m, spoken, content, prof in [
        ("2026-11-18T09:00", 0, 15, 30, "ba giờ rưỡi chiều nay", "đi lấy hàng", 0),
        ("2026-11-18T22:00", 1, 5, 30, "năm rưỡi sáng mai", "ra sân bay", 1),
        ("2026-11-19T10:15", 0, 12, 0, "mười hai giờ trưa", "ăn trưa với sếp", 2),
        ("2026-11-20T20:10", 0, 23, 0, "mười một giờ đêm nay", "phơi đồ", 3),
        ("2026-11-21T08:00", 2, 20, 15, "tám giờ mười lăm tối ngày kia", "gọi điện cho bà", 4),
        ("2026-11-22T13:00", 0, 19, 0, "bảy giờ tối", "xem bóng đá", 5),
    ]:
        s = Sc(A, now, ["reminders"], prof)
        s.state["reminders"] = R()
        s.say(f"{spoken.capitalize()} nhắc em {content} giúp em.", C("reminders.create", content=content, time=s.t(dd, h, m)))
        S.append(s)

    # ---- reminders theo thứ (thứ X = lần tới gần nhất; thứ X tuần sau) ----
    s = Sc(A, "2026-11-18T09:00", ["reminders"], 6)  # thứ tư
    s.state["reminders"] = R()
    w = s.next_wd(4)
    s.say("Sáng thứ sáu tám giờ nhắc anh nộp tiền nhà.", C("reminders.create", content="nộp tiền nhà", time=s.t(w, 8)))
    S.append(s)
    s = Sc(A, "2026-11-18T09:00", ["reminders"], 7)
    s.state["reminders"] = R()
    w = s.next_wd(1, next_week=True)
    s.say("Thứ ba tuần sau lúc hai giờ chiều nhắc tôi đi khám răng.", C("reminders.create", content="đi khám răng", time=s.t(w, 14)))
    S.append(s)
    s = Sc(A, "2026-11-21T20:00", ["reminders"], 0)  # thứ bảy
    s.state["reminders"] = R()
    w = s.next_wd(6, same_week=True)
    s.say("Chủ nhật này chín giờ sáng nhắc chị đi lễ.", C("reminders.create", content="đi lễ", time=s.t(w, 9)))
    S.append(s)

    # ---- alarm ----
    for now, dd, h, m, spoken, prof in [
        ("2026-11-18T22:30", 1, 5, 45, "sáu giờ kém mười lăm sáng mai", 1),
        ("2026-11-19T23:10", 1, 4, 30, "bốn rưỡi sáng mai", 2),
        ("2026-11-20T13:00", 0, 14, 20, "hai giờ hai mươi chiều nay", 3),
        ("2026-11-21T00:30", 0, 6, 0, "sáu giờ sáng nay", 4),
    ]:
        s = Sc(A, now, ["alarm"], prof)
        s.state["alarm"] = alarms()
        s.say(f"Đặt báo thức {spoken} cho tôi.", C("alarm.create", time=s.t(dd, h, m)))
        S.append(s)
    s = Sc(A, "2026-11-22T14:00", ["alarm"], 5)
    s.state["alarm"] = alarms()
    s.say("Hai mươi lăm phút nữa gọi tôi dậy nhé, ngủ trưa chút.", C("alarm.create", time=plus(s, 25)))
    S.append(s)
    # đổi giờ báo thức có sẵn
    s = Sc(A, "2026-11-23T21:30", ["alarm"], 6)
    s.state["alarm"] = alarms(("alarm_01", s.t(1, 6), "", "weekdays", True), ("alarm_02", s.t(1, 9), "", "weekends", True))
    s.say("Báo thức sáu giờ sáng mai dời sớm lên thành năm giờ kém mười lăm giúp anh.",
          C("alarm.list"), C("alarm.update", alarm_id="alarm_01", time=s.t(1, 4, 45)))
    S.append(s)

    # ---- calendar: end = start + 1h ----
    for now, dd, h, m, spoken, title, prof in [
        ("2026-11-18T08:00", 0, 14, 30, "hai rưỡi chiều nay", "Họp team marketing", 7),
        ("2026-11-19T19:00", 1, 9, 45, "mười giờ kém mười lăm sáng mai", "Phỏng vấn ứng viên", 0),
        ("2026-11-20T10:00", 2, 18, 30, "sáu rưỡi tối ngày kia", "Ăn tối với gia đình", 1),
    ]:
        s = Sc(A, now, ["calendar"], prof)
        s.state["calendar"] = events()
        st = s.t(dd, h, m)
        s.say(f"Tạo lịch '{title}' lúc {spoken}.", C("calendar.create_event", title=title, start=st, end=end1h(st)))
        S.append(s)
    # calendar có giờ kết thúc nói rõ
    s = Sc(A, "2026-11-21T09:00", ["calendar"], 2)
    s.state["calendar"] = events()
    s.say("Thêm lịch học tiếng Anh từ bảy giờ đến chín giờ tối nay.", C("calendar.create_event", title="Học tiếng Anh", start=s.t(0, 19), end=s.t(0, 21)))
    S.append(s)
    # dời lịch muộn nửa tiếng
    s = Sc(A, "2026-11-22T08:30", ["calendar"], 3)
    s.state["calendar"] = events(("evt_01", "Họp giao ban", s.t(0, 9), s.t(0, 10), "Phòng họp A"), ("evt_02", "Gặp khách", s.t(0, 15), s.t(0, 16), "Cafe"))
    s.say("Dời cuộc họp giao ban sáng nay muộn nửa tiếng.", C("calendar.list_events"), C("calendar.update_event", event_id="evt_01", start=s.t(0, 9, 30), end=s.t(0, 10, 30)))
    S.append(s)
    s = Sc(A, "2026-11-24T10:00", ["calendar"], 4)
    s.state["calendar"] = events(("evt_01", "Gặp khách hàng Hoà Phát", s.t(0, 14), s.t(0, 15), "Văn phòng"))
    s.say("Lịch gặp khách hàng Hoà Phát chiều nay lùi sớm lại một tiếng nhé.", C("calendar.list_events"), C("calendar.update_event", event_id="evt_01", start=s.t(0, 13), end=s.t(0, 14)))
    S.append(s)

    # ---- tasks due ----
    s = Sc(A, "2026-11-25T09:00", ["tasks"], 5)
    s.state["tasks"] = tasks()
    s.say("Thêm việc nộp báo cáo quý, hạn năm giờ chiều thứ sáu.", C("tasks.add", title="Nộp báo cáo quý", due=s.t(s.next_wd(4), 17)))
    S.append(s)
    s = Sc(A, "2026-11-26T15:00", ["tasks"], 6)
    s.state["tasks"] = tasks()
    s.say("Ghi việc gửi hồ sơ xin visa, hạn mười giờ kém mười lăm sáng mai, ưu tiên cao.", C("tasks.add", title="Gửi hồ sơ xin visa", due=s.t(1, 9, 45), priority="high"))
    S.append(s)

    # ---- parking / grocery / ride_hailing time ----
    s = Sc(A, "2026-11-27T13:20", ["parking"], 7)
    s.state["parking"] = parking_state([("lot_01", "Bãi xe Vincom Plaza", "1 Lê Thánh Tông", "Ngô Quyền", 15000, 20)])
    s.say("Bốn mươi phút nữa đặt cho tôi chỗ đỗ ở Vincom Plaza, gửi hai tiếng.",
          C("parking.find", near="Vincom Plaza"), C("parking.reserve", lot_id="lot_01", from_time=plus(s, 40), hours=2))
    S.append(s)
    s = Sc(A, "2026-11-28T09:00", ["parking"], 0)
    s.state["parking"] = parking_state([("lot_01", "Bãi xe Takashimaya", "92 Nam Kỳ Khởi Nghĩa", "Quận 1", 30000, 15)])
    s.say("Đặt chỗ đỗ ở Takashimaya lúc hai giờ kém mười lăm chiều nay, ba tiếng.",
          C("parking.find", near="Takashimaya"), C("parking.reserve", lot_id="lot_01", from_time=s.t(0, 13, 45), hours=3))
    S.append(s)
    s = Sc(A, "2026-11-29T10:00", ["grocery"], 1)
    s.state["grocery"] = {"products": [{"id": "prod_01", "name": "Thịt gà phi lê 500g", "price": 69000, "unit": "khay", "category": "thịt", "in_stock": True}], "cart": [], "orders": []}
    s.say("Đặt hai khay thịt gà phi lê, giao lúc năm giờ kém mười lăm chiều nay.",
          C("grocery.search", query="thịt gà phi lê"), C("grocery.add_to_cart", product_id="prod_01", quantity=2), C("grocery.checkout", delivery_time=s.t(0, 16, 45)))
    S.append(s)
    s = Sc(A, "2026-11-30T05:10", ["ride_hailing"], 2)
    s.state["ride_hailing"] = {"quotes": [{"vehicle": "bike", "price": 45000, "eta_min": 4}, {"vehicle": "car4", "price": 120000, "eta_min": 6}], "rides": []}
    s.say("Đặt xe ô tô bốn chỗ đón ở nhà lúc sáu giờ kém mười lăm ra sân bay Đà Nẵng.",
          C("ride_hailing.book", pickup=s.prof["home_address"], dropoff="sân bay Đà Nẵng", vehicle="car4", schedule_time=s.t(0, 5, 45)))
    S.append(s)
    s = Sc(A, "2026-12-01T17:00", ["ride_hailing"], 3)
    s.state["ride_hailing"] = {"quotes": [{"vehicle": "bike", "price": 30000, "eta_min": 3}], "rides": []}
    s.say("Ba mươi phút nữa đặt xe máy đón tôi ở công ty về nhà.",
          C("ride_hailing.book", pickup=s.prof["work_address"], dropoff=s.prof["home_address"], vehicle="bike", schedule_time=plus(s, 30)))
    S.append(s)

    return S
