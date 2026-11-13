"""Map lời nói -> mã enum (lỗi val v9: 'giặt nhanh' -> intensive thay vì quick, 'chế độ thường' sai mã).
Chỉ truyền tham số tuỳ chọn khi người dùng NÓI RÕ (quy ước gold)."""
from common import *

A = "enum"


def build():
    S = []

    # ---- smart_home climate mode ----
    for phrase, mode, temp, prof in [("bật điều hoà phòng ngủ chế độ làm mát hai mươi lăm độ", "cool", 25, 0),
                                     ("chuyển điều hoà phòng ngủ sang hút ẩm, trời nồm quá", "dry", None, 1),
                                     ("bật sưởi điều hoà phòng ngủ hai mươi tám độ cho bé", "heat", 28, 2),
                                     ("để điều hoà phòng ngủ chạy chế độ quạt thôi, không cần lạnh", "fan", None, 3),
                                     ("tắt điều hoà phòng ngủ đi", "off", None, 4)]:
        s = Sc(A, "2026-11-18T21:00", ["smart_home"], prof)
        s.state["smart_home"] = smart(("ac_01", "Điều hoà phòng ngủ", "phòng ngủ", "climate", {"mode": "cool", "temperature": 26}),
                                      ("ac_02", "Điều hoà phòng khách", "phòng khách", "climate", {"mode": "off"}))
        args = {"device_id": "ac_01", "mode": mode}
        if temp: args["temperature"] = temp
        s.say(phrase.capitalize() + ".", C("smart_home.get_status"), C("smart_home.climate_set", **args))
        S.append(s)

    # ---- fan speed / light brightness ----
    s = Sc(A, "2026-11-19T14:00", ["smart_home"], 5)
    s.state["smart_home"] = smart(("fan_01", "Quạt trần phòng khách", "phòng khách", "fan", {"power": "on", "speed": 1}))
    s.say("Quạt trần phòng khách tăng lên số ba.", C("smart_home.get_status"), C("smart_home.fan_set", device_id="fan_01", speed=3))
    S.append(s)
    s = Sc(A, "2026-11-19T22:00", ["smart_home"], 6)
    s.state["smart_home"] = smart(("light_01", "Đèn ngủ", "phòng ngủ", "light", {"power": "on", "brightness": 80}))
    s.say("Giảm đèn ngủ xuống ba mươi phần trăm.", C("smart_home.get_status"), C("smart_home.light_set", device_id="light_01", brightness=30))
    S.append(s)
    s = Sc(A, "2026-11-20T06:30", ["smart_home"], 7)
    s.state["smart_home"] = smart(("cur_01", "Rèm phòng khách", "phòng khách", "curtain", {"power": "off"}))
    s.say("Mở rèm phòng khách ra.", C("smart_home.get_status"), C("smart_home.switch_set", device_id="cur_01", power="on"))
    S.append(s)

    # ---- ride_hailing vehicle / payment ----
    for phrase, veh, pay, prof in [("Gọi xe máy từ nhà ra bến xe Miền Đông", "bike", None, 0),
                                   ("Đặt ô tô bảy chỗ từ nhà ra bến xe Miền Đông, cả nhà sáu người", "car7", None, 0),
                                   ("Gọi taxi bốn chỗ từ nhà ra bến xe Miền Đông, trả tiền mặt", "car4", "cash", 0),
                                   ("Book grab bike từ nhà ra bến xe Miền Đông, thanh toán bằng ví", "bike", "ewallet", 0)]:
        s = Sc(A, "2026-11-21T07:00", ["ride_hailing"], prof)
        s.state["ride_hailing"] = {"quotes": [{"vehicle": "bike", "price": 52000}, {"vehicle": "car4", "price": 140000}, {"vehicle": "car7", "price": 175000}], "rides": []}
        args = {"pickup": s.prof["home_address"], "dropoff": "bến xe Miền Đông", "vehicle": veh}
        if pay: args["payment"] = pay
        s.say(phrase + ".", C("ride_hailing.book", **args))
        S.append(s)

    # ---- maps mode ----
    for phrase, mode, prof in [("Từ nhà đi bộ ra Hồ Gươm mất bao lâu?", "walk", 1), ("Đi xe buýt từ nhà ra Hồ Gươm mất bao lâu?", "transit", 1),
                               ("Lái ô tô từ nhà ra Hồ Gươm hết mấy phút?", "car", 1), ("Từ nhà chạy xe máy ra Hồ Gươm bao xa?", None, 1)]:
        s = Sc(A, "2026-11-22T08:00", ["maps"], prof)
        s.state["maps"] = {"places": [], "saved_places": []}
        args = {"origin": s.prof["home_address"], "destination": "Hồ Gươm"}
        if mode: args["mode"] = mode
        s.say(phrase, C("maps.get_route", **args))
        S.append(s)

    # ---- bill_payment type / source ----
    bills = {"bills": [{"id": "bill_01", "type": "electricity", "provider": "EVN", "amount": 850000, "paid": False},
                       {"id": "bill_02", "type": "water", "provider": "Cấp nước Sawaco", "amount": 120000, "paid": False},
                       {"id": "bill_03", "type": "internet", "provider": "FPT Telecom", "amount": 220000, "paid": False},
                       {"id": "bill_04", "type": "tuition", "provider": "Trường Tiểu học Lê Văn Tám", "amount": 2500000, "paid": False}], "autopays": []}
    for phrase, typ, bid, src, prof in [("Trả tiền điện tháng này bằng tài khoản ngân hàng", "electricity", "bill_01", "bank", 2),
                                        ("Thanh toán tiền nước bằng ví điện tử", "water", "bill_02", "ewallet", 3),
                                        ("Đóng tiền mạng FPT qua ngân hàng giúp mình", "internet", "bill_03", "bank", 4),
                                        ("Nộp học phí cho con bằng chuyển khoản ngân hàng", "tuition", "bill_04", "bank", 5)]:
        s = Sc(A, "2026-11-23T10:00", ["bill_payment", "ewallet"], prof)
        import copy
        s.state["bill_payment"] = copy.deepcopy(bills); s.state["ewallet"] = ewallet(3000000)
        s.say(phrase + ".", C("bill_payment.list_bills", type=typ), C("bill_payment.pay", bill_id=bid, source=src))
        S.append(s)
    s = Sc(A, "2026-11-23T10:00", ["bill_payment"], 6)
    s.state["bill_payment"] = {"bills": [], "autopays": []}
    s.say("Bật tự động thanh toán tiền điện hằng tháng cho tôi.", C("bill_payment.schedule_autopay", type="electricity", enabled=True))
    S.append(s)

    # ---- gold / fuel type ----
    for phrase, typ, prof in [("Giá vàng nhẫn hôm nay bao nhiêu?", "ring", 7), ("Vàng thế giới đang bao nhiêu một ounce?", "world", 0), ("Giá vàng miếng SJC sao rồi?", "sjc", 1)]:
        s = Sc(A, "2026-11-24T09:00", ["gold_price"], prof)
        s.state["gold_price"] = gold(130000000, 132000000, 128000000, 130500000)
        s.state["gold_price"]["prices"].append({"type": "world", "buy": 2650, "sell": 2652, "unit": "USD/ounce"})
        s.say(phrase, C("gold_price.get_price", type=typ))
        S.append(s)
    for phrase, typ, prof in [("Xăng chín lăm hôm nay giá nhiêu?", "ron95", 2), ("Giá xăng E5 bao nhiêu một lít?", "e5", 3), ("Dầu diesel giờ bao nhiêu tiền?", "diesel", 4)]:
        s = Sc(A, "2026-11-24T09:00", ["fuel_price"], prof)
        s.state["fuel_price"] = fuel(24500, 23100, 21500)
        s.say(phrase, C("fuel_price.get_price", type=typ))
        S.append(s)

    # ---- tasks priority ----
    for phrase, pr, prof in [("Thêm việc gọi cho ngân hàng, việc gấp nha", "high", 5), ("Ghi việc dọn kho, không gấp đâu, ưu tiên thấp", "low", 6), ("Thêm việc mua quà sinh nhật mẹ", None, 7)]:
        s = Sc(A, "2026-11-25T09:00", ["tasks"], prof)
        s.state["tasks"] = tasks()
        title = {"high": "Gọi cho ngân hàng", "low": "Dọn kho", None: "Mua quà sinh nhật mẹ"}[pr]
        args = {"title": title}
        if pr: args["priority"] = pr
        s.say(phrase + ".", C("tasks.add", **args))
        S.append(s)

    # ---- alarm repeat (chỉ khi nói rõ) ----
    for phrase, rep, h, m, prof in [("Đặt báo thức sáu giờ sáng các ngày trong tuần", "weekdays", 6, 0, 0), ("Báo thức tám rưỡi sáng cuối tuần nhé", "weekends", 8, 30, 1),
                                    ("Đặt báo thức năm giờ rưỡi sáng hằng ngày", "daily", 5, 30, 2)]:
        s = Sc(A, "2026-11-26T22:00", ["alarm"], prof)
        s.state["alarm"] = alarms()
        dd = 1
        if rep == "weekends":
            dd = s.next_wd(5)
        s.say(phrase + ".", C("alarm.create", time=s.t(dd, h, m), repeat=rep))
        S.append(s)
    s = Sc(A, "2026-11-26T22:00", ["reminders"], 3)
    s.state["reminders"] = reminders()
    s.say("Nhắc tôi tưới cây lúc bảy giờ sáng mỗi tuần.", C("reminders.create", content="tưới cây", time=s.t(1, 7), repeat="weekly"))
    S.append(s)

    # ---- music / tv control ----
    for phrase, action, prof in [("Tạm dừng nhạc chút", "pause", 4), ("Phát tiếp bài đang nghe đi", "resume", 5), ("Chuyển bài tiếp theo", "next", 6), ("Quay lại bài trước", "previous", 7)]:
        s = Sc(A, "2026-11-27T20:00", ["music"], prof)
        s.state["music"] = {"tracks": [{"id": "trk_01", "title": "Nơi này có anh", "artist": "Sơn Tùng M-TP"}], "playlists": [],
                            "now_playing": {"track_id": "trk_01", "title": "Nơi này có anh", "status": "playing" if action != "resume" else "paused"}}
        s.say(phrase + ".", C("music.control", action=action))
        S.append(s)
    s = Sc(A, "2026-11-27T20:00", ["music"], 0)
    s.state["music"] = {"tracks": [], "playlists": [], "now_playing": None}
    s.say("Chỉnh âm lượng nhạc xuống hai mươi.", C("music.control", action="volume", volume=20))
    S.append(s)
    for phrase, args, prof in [("Tắt tiếng tivi giùm", {"action": "mute"}, 1), ("Tắt tivi đi con", {"action": "off"}, 2), ("Bật tivi lên", {"action": "on"}, 3),
                               ("Vặn tivi to lên ba mươi", {"action": "volume", "volume": 30}, 4)]:
        s = Sc(A, "2026-11-28T19:30", ["tv"], prof)
        s.state["tv"] = {"channels": ["VTV1", "VTV3", "HTV7"], "programs": [], "recordings": [], "power": "on", "volume": 15}
        s.say(phrase + ".", C("tv.control", **args))
        S.append(s)

    # ---- email archive vs delete ----
    for phrase, act, prof in [("Xoá cái email quảng cáo của Shopee đi", "delete", 5), ("Lưu trữ email quảng cáo của Shopee lại", "archive", 6)]:
        s = Sc(A, "2026-11-29T08:00", ["email"], prof)
        s.state["email"] = {"emails": [{"id": "em_01", "from": "promo@shopee.test", "subject": "Siêu sale 12.12", "body": "...", "unread": True, "folder": "inbox"},
                                       {"id": "em_02", "from": "hr@company.test", "subject": "Lịch nghỉ Tết", "body": "...", "unread": True, "folder": "inbox"}], "sent": [], "drafts": []}
        s.say(phrase + ".", C("email.list"), C("email.archive", email_id="em_01", action=act))
        S.append(s)

    # ---- flights seat class ----
    for phrase, cls, prof in [("Đặt hai vé thương gia chuyến bay sáng mai đi Hà Nội", "business", 0), ("Đặt hai vé phổ thông chuyến bay sáng mai đi Hà Nội", "economy", 0), ("Đặt hai vé chuyến bay sáng mai đi Hà Nội", None, 0)]:
        s = Sc(A, "2026-11-30T20:00", ["flights"], prof)
        s.state["flights"] = {"flights": [{"id": "fl_01", "origin": "SGN", "destination": "HAN", "date": s.d(1), "depart": "07:00", "arrive": "09:10", "airline": "Vietnam Airlines", "price": 2100000, "flight_no": "VN210"}], "bookings": []}
        args = {"flight_id": "fl_01", "passengers": 2}
        if cls: args["seat_class"] = cls
        s.say(phrase + ".", C("flights.search", origin="TP.HCM", destination="Hà Nội", date=s.d(1)), C("flights.book", **args))
        S.append(s)

    # ---- ecommerce return reason / payment ----
    for phrase, reason, prof in [("Cái áo giao sai màu, làm trả hàng giúp em", "wrong_item", 1), ("Cái nồi bị nứt đáy, trả hàng đi", "damaged", 2),
                                 ("Mua về không ưng lắm, trả lại cái đơn đó", "changed_mind", 3), ("Trả hàng đơn đó giúp chị, giao trễ cả tuần", "other", 4)]:
        s = Sc(A, "2026-12-01T10:00", ["ecommerce"], prof)
        s.state["ecommerce"] = {"products": [], "cart": [], "returns": [],
                                "orders": [{"id": "ord_01", "items": [{"product_id": "p1", "name": "Sản phẩm", "price": 300000, "quantity": 1}], "total": 300000, "status": "delivered", "placed_at": s.t(-5, 9), "delivered_at": s.t(-1, 15), "payment": "cod"}]}
        s.say(phrase + ".", C("ecommerce.order_status"), C("ecommerce.request_return", order_id="ord_01", reason=reason))
        S.append(s)

    # ---- translator language codes ----
    for lang, code, prof in [("tiếng Hàn", "ko", 5), ("tiếng Nhật", "ja", 6), ("tiếng Trung", "zh", 7), ("tiếng Pháp", "fr", 0), ("tiếng Thái", "th", 1), ("tiếng Đức", "de", 2), ("tiếng Tây Ban Nha", "es", 3)]:
        s = Sc(A, "2026-12-02T10:00", ["translator"], prof)
        s.state["translator"] = {"dictionary": []}
        s.say(f"Dịch sang {lang} câu 'cảm ơn bạn rất nhiều'.", C("translator.translate", text="Cảm ơn bạn rất nhiều", to_lang=code))
        S.append(s)

    return S
