"""Câu điều kiện (lỗi val v9: train_0282/0293/0328 'mai mà mưa thì huỷ…' -> trả []).
Luôn đọc để kiểm tra điều kiện rồi mới quyết định; điều kiện sai -> chỉ có lần đọc. Câu chữ viết mới, dựa trên mẫu train."""
from common import *

A = "cond"


def build():
    S = []

    def pair(fn):
        for flag in (True, False):
            S.append(fn(flag))

    # 1. chiều nay mưa -> đặt xe ô tô về nhà
    def f(rain):
        s = Sc(A, "2026-11-18T15:00", ["weather", "ride_hailing"], 0)
        s.state["weather"] = weather(s.city, {s.d(0): ("mưa giông" if rain else "nắng nhẹ", 25, 31, 90 if rain else 10)})
        s.state["ride_hailing"] = {"quotes": [{"vehicle": "car4", "price": 110000}], "rides": []}
        g = [C("weather.get_forecast", date=s.d(0))]
        if rain: g.append(C("ride_hailing.book", pickup=s.prof["work_address"], dropoff=s.prof["home_address"], vehicle="car4"))
        return s.say("Chiều nay có mưa không em, mưa thì gọi ô tô bốn chỗ từ công ty về nhà luôn, không thì anh chạy xe máy.", *g)
    pair(f)

    # 2. cuối tuần nắng -> tạo lịch picnic
    def f(sun):
        s = Sc(A, "2026-11-19T20:00", ["weather", "calendar"], 1)  # thứ năm
        sat = s.next_wd(5)
        s.state["weather"] = weather(s.city, {s.d(sat): ("nắng" if sun else "mưa", 20, 28, 5 if sun else 80)})
        s.state["calendar"] = events()
        g = [C("weather.get_forecast", date=s.d(sat))]
        if sun: g.append(C("calendar.create_event", title="Đi picnic Ba Vì", start=s.t(sat, 7), end=s.t(sat, 8)))
        return s.say("Thứ bảy này trời đẹp thì tạo lịch đi picnic Ba Vì lúc bảy giờ sáng, xấu trời thì thôi.", *g)
    pair(f)

    # 3. mai lạnh dưới 18 độ -> nhắc mang áo ấm
    def f(cold):
        s = Sc(A, "2026-11-20T21:00", ["weather", "reminders"], 5)
        s.state["weather"] = weather(s.city, {s.d(1): ("rét", 14 if cold else 21, 19 if cold else 27, 10)})
        s.state["reminders"] = reminders()
        g = [C("weather.get_forecast", date=s.d(1))]
        if cold: g.append(C("reminders.create", content="Mang áo ấm cho con", time=s.t(1, 6, 30)))
        return s.say("Sáng mai nhiệt độ xuống dưới mười tám độ thì sáu rưỡi nhắc tôi mang áo ấm cho con, còn ấm thì khỏi.", *g)
    pair(f)

    # 4. hoá đơn điện trên 1 triệu -> nhắn vợ; không thì trả luôn bằng ví (cả 2 nhánh hành động)
    def f(high):
        s = Sc(A, "2026-11-21T10:00", ["bill_payment", "ewallet", "chat_ott"], 2)
        s.state["bill_payment"] = {"bills": [{"id": "bill_01", "type": "electricity", "provider": "EVN", "amount": 1250000 if high else 640000, "paid": False}], "autopays": []}
        s.state["ewallet"] = ewallet(2000000)
        s.state["chat_ott"] = chats(("chat_01", "Vợ", "direct"))
        g = [C("bill_payment.list_bills", type="electricity")]
        if high:
            g += [C("chat_ott.list_chats"), C("chat_ott.send_message", chat_id="chat_01", content="Tiền điện tháng này hơn 1 triệu, em xem lại nhé")]
        else:
            g += [C("bill_payment.pay", bill_id="bill_01", source="ewallet")]
        return s.say("Xem tiền điện tháng này, trên một triệu thì nhắn vợ là tiền điện tháng này hơn một triệu em xem lại nhé, dưới thì trả luôn bằng ví.", *g)
    pair(f)

    # 5. ví đủ -> trả tiền nước
    def f(ok):
        s = Sc(A, "2026-11-22T09:30", ["bill_payment", "ewallet"], 3)
        s.state["bill_payment"] = {"bills": [{"id": "bill_01", "type": "water", "provider": "Cấp nước Huế", "amount": 180000, "paid": False}], "autopays": []}
        s.state["ewallet"] = ewallet(500000 if ok else 90000)
        g = [C("ewallet.get_balance")]
        if ok: g += [C("bill_payment.list_bills", type="water"), C("bill_payment.pay", bill_id="bill_01", source="ewallet")]
        return s.say("Ví còn đủ tiền thì trả tiền nước bằng ví giúp mình, không đủ thì để mình chuyển khoản sau.", *g)
    pair(f)

    # 6. dầu diesel dưới 22k -> ghi chú đổ dầu
    def f(low):
        s = Sc(A, "2026-11-23T07:00", ["fuel_price", "tasks"], 4)
        s.state["fuel_price"] = fuel(24500, 23100, 21300 if low else 22800)
        s.state["tasks"] = tasks()
        g = [C("fuel_price.get_price", type="diesel")]
        if low: g.append(C("tasks.add", title="Đổ đầy bình dầu xe tải"))
        return s.say("Dầu diesel hôm nay mà dưới hai mươi hai nghìn thì thêm việc đổ đầy bình dầu xe tải, cao hơn thì để tuần sau.", *g)
    pair(f)

    # 7. vàng thế giới vượt ngưỡng -> email
    def f(high):
        s = Sc(A, "2026-11-24T08:00", ["gold_price", "email", "contacts"], 6)
        s.state["gold_price"] = {"prices": [{"type": "world", "buy": 2710 if high else 2620, "sell": 2712 if high else 2622, "unit": "USD/ounce"}]}
        s.state["email"] = {"emails": [], "sent": [], "drafts": []}
        s.state["contacts"] = {"contacts": [{"id": "c_01", "name": "Anh Khoa", "relation": "đối tác", "phone": "0909000111", "email": "khoa.le@example.test"}]}
        g = [C("gold_price.get_price", type="world")]
        if high: g += [C("contacts.search", query="Khoa"), C("email.send", to=["khoa.le@example.test"], subject="Giá vàng thế giới", body="Vàng thế giới đã vượt 2700 USD một ounce")]
        return s.say("Vàng thế giới mà vượt hai nghìn bảy trăm đô một ounce thì gửi email cho anh Khoa báo là vàng đã vượt 2700, tiêu đề giá vàng thế giới, chưa vượt thì thôi.", *g)
    pair(f)

    # 8. còn chỗ trên chuyến bay -> đặt
    def f(ok):
        s = Sc(A, "2026-11-25T21:00", ["flights"], 1)
        s.state["flights"] = {"flights": ([{"id": "fl_01", "origin": "HAN", "destination": "DAD", "date": s.d(2), "depart": "08:00", "arrive": "09:20", "airline": "Vietjet", "price": 1200000 if ok else 2600000, "flight_no": "VJ511"}]), "bookings": []}
        g = [C("flights.search", origin="Hà Nội", destination="Đà Nẵng", date=s.d(2))]
        if ok: g.append(C("flights.book", flight_id="fl_01", passengers=1))
        return s.say("Ngày kia bay Hà Nội đi Đà Nẵng, vé dưới một triệu rưỡi thì đặt một vé, đắt hơn thì thôi để anh đi tàu.", *g)
    pair(f)

    # 9. có tin nhắn nhỡ của mẹ -> gọi lại
    def f(missed):
        s = Sc(A, "2026-11-26T12:30", ["phone", "contacts"], 7)
        s.state["phone"] = {"calls": ([{"id": "call_01", "contact_id": "c_01", "name": "Mẹ", "phone": "0912000111", "direction": "in", "missed": True, "time": s.t(0, 11)}] if missed else
                                      [{"id": "call_01", "contact_id": "c_02", "name": "Sếp", "phone": "0988000222", "direction": "in", "missed": True, "time": s.t(0, 11)}])}
        s.state["contacts"] = contacts(("c_01", "Mẹ", "mẹ", "0912000111"), ("c_02", "Sếp", "sếp", "0988000222"))
        g = [C("phone.recent_calls", missed_only=True)]
        if missed: g.append(C("phone.call", contact_id="c_01"))
        return s.say("Coi có cuộc gọi nhỡ nào của mẹ không, có thì gọi lại cho mẹ luôn.", *g)
    pair(f)

    # 10. tối nay có trận trên VTV3 -> ghi hình
    def f(has):
        s = Sc(A, "2026-11-27T17:00", ["tv"], 0)
        prog = [{"id": "prg_01", "channel": "VTV3", "title": "Bóng đá: Việt Nam - Thái Lan" if has else "Phim truyện: Hương vị tình thân", "start": s.t(0, 20), "date": s.d(0)}]
        s.state["tv"] = {"channels": ["VTV1", "VTV3", "HTV7"], "programs": prog, "recordings": []}
        g = [C("tv.guide", channel="VTV3")]
        if has: g.append(C("tv.record", program_id="prg_01"))
        return s.say("Tối nay VTV3 có chiếu bóng đá Việt Nam thì ghi hình giúp anh, không có thì thôi.", *g)
    pair(f)

    # 11. hết vé tàu -> đặt xe khách (cả hai nhánh hành động)
    def f(train_ok):
        s = Sc(A, "2026-11-28T20:00", ["train_bus_tickets"], 2)
        trips = [{"id": "trip_01", "type": "train", "operator": "SE2", "origin": "Đà Nẵng", "destination": "Huế", "date": s.d(1), "depart": "07:00", "arrive": "09:40", "price": 110000, "seats_left": 6 if train_ok else 0},
                 {"id": "trip_02", "type": "bus", "operator": "Hoàng Long", "origin": "Đà Nẵng", "destination": "Huế", "date": s.d(1), "depart": "07:30", "arrive": "10:00", "price": 140000, "seats_left": 20}]
        s.state["train_bus_tickets"] = {"trips": trips, "bookings": []}
        g = [C("train_bus_tickets.search", origin="Đà Nẵng", destination="Huế", date=s.d(1), type="train")]
        if train_ok:
            g.append(C("train_bus_tickets.book", trip_id="trip_01", seats=2))
        else:
            g += [C("train_bus_tickets.search", origin="Đà Nẵng", destination="Huế", date=s.d(1), type="bus"), C("train_bus_tickets.book", trip_id="trip_02", seats=2)]
        return s.say("Mai ra Huế, còn vé tàu thì đặt hai vé tàu, hết rồi thì đặt hai vé xe khách.", *g)
    pair(f)

    # 12. lịch tối nay trống -> đặt bàn? (không có app) -> tạo lịch đi xem phim
    def f(free):
        s = Sc(A, "2026-11-29T14:00", ["calendar", "chat_ott"], 3)
        s.state["calendar"] = events() if free else events(("evt_01", "Tiệc công ty", s.t(0, 18, 30), s.t(0, 21), "Nhà hàng Sen"))
        s.state["chat_ott"] = chats(("chat_01", "Ngân", "direct"))
        g = [C("calendar.list_events")]
        if free: g += [C("chat_ott.list_chats"), C("chat_ott.send_message", chat_id="chat_01", content="Tối nay đi xem phim nhé")]
        return s.say("Tối nay tôi có lịch gì không, rảnh thì nhắn Ngân là tối nay đi xem phim nhé.", *g)
    pair(f)

    # 13. có email chưa đọc của sếp -> đọc
    def f(has):
        s = Sc(A, "2026-11-30T08:10", ["email"], 4)
        s.state["email"] = {"emails": ([{"id": "em_01", "from": "sep@company.test", "subject": "Kế hoạch tuần", "body": "Họp lúc 9h", "unread": True, "folder": "inbox"}] if has else
                                       [{"id": "em_01", "from": "news@vnexpress.test", "subject": "Bản tin sáng", "body": "...", "unread": True, "folder": "inbox"}]), "sent": [], "drafts": []}
        g = [C("email.list", unread_only=True)]
        if has: g.append(C("email.read", email_id="em_01"))
        return s.say("Có email chưa đọc nào của sếp không, có thì đọc nội dung cho tôi nghe.", *g)
    pair(f)

    # 14. HPG lời trên 10% -> bán nửa
    def f(gain):
        s = Sc(A, "2026-12-01T10:00", ["stocks"], 5)
        st = stocks_state(holdings=[("HPG", "Hòa Phát", 2000, 25000)]); st["holdings"][0]["price"] = 28200 if gain else 26000
        s.state["stocks"] = st
        g = [C("stocks.get_portfolio")]
        if gain: g.append(C("stocks.place_order", symbol="HPG", side="sell", quantity=1000))
        return s.say("HPG trong danh mục mà lời trên mười phần trăm thì bán một nửa giá thị trường, chưa tới thì giữ.", *g)
    pair(f)

    # 15. đơn đồ ăn chưa giao -> huỷ (food_delivery)
    def f(pending):
        s = Sc(A, "2026-12-02T12:40", ["food_delivery"], 6)
        s.state["food_delivery"] = {"restaurants": [], "menus": {}, "orders": [{"id": "fo_01", "restaurant_id": "r1", "items": [{"item_id": "m1", "name": "Cơm gà", "quantity": 1, "price": 45000}], "total": 45000, "status": "placed" if pending else "delivered"}]}
        g = [C("food_delivery.order_history")]
        if pending: g.append(C("food_delivery.cancel_order", order_id="fo_01"))
        return s.say("Đơn cơm gà trưa nay mà shipper chưa lấy thì huỷ đi, đã giao rồi thì thôi.", *g)
    pair(f)

    return S
