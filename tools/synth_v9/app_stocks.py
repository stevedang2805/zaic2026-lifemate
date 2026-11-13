from common import *

A = "stocks"


def Q(sym, name, price, chg):
    return {"symbol": sym, "name": name, "price": price, "change_pct": chg}


def Hd(sym, name, qty, avg, price):
    return {"symbol": sym, "name": name, "quantity": qty, "avg_price": avg, "price": price}


def ST(holdings=(), quotes=()):
    return {"holdings": list(holdings), "orders": [], "alerts": [], "quotes": list(quotes)}


def build():
    S = []

    # 1. mua thị trường
    s = Sc(A, "2026-11-18T09:35", [A], 0)
    s.state[A] = ST(quotes=[Q("FPT", "FPT Corp", 128500, 1.2), Q("VNM", "Vinamilk", 65300, -0.4)])
    s.say("Mua cho anh hai trăm cổ FPT giá thị trường.",
          C(f"{A}.place_order", symbol="FPT", side="buy", quantity=200))
    S.append(s)

    # 2. mua giới hạn giá
    s = Sc(A, "2026-11-19T10:05", [A], 1)
    s.state[A] = ST(quotes=[Q("HPG", "Hòa Phát", 27800, 0.7)])
    s.say("Đặt lệnh mua một nghìn cổ phiếu HPG giá hai mươi bảy nghìn rưỡi.",
          C(f"{A}.place_order", symbol="HPG", side="buy", quantity=1000, price=27500))
    S.append(s)

    # 3. bán một phần danh mục: cần get_portfolio? Số lượng nói rõ -> không cần đọc. Gold: place_order sell
    s = Sc(A, "2026-11-20T13:40", [A], 2)
    s.state[A] = ST(holdings=[Hd("MWG", "Thế Giới Di Động", 500, 52000, 61000)])
    s.say("Bán ba trăm cổ MWG giá thị trường đi em.",
          C(f"{A}.place_order", symbol="MWG", side="sell", quantity=300))
    S.append(s)

    # 4. bán hết -> phải xem danh mục để biết số lượng
    s = Sc(A, "2026-11-21T09:20", [A], 3)
    s.state[A] = ST(holdings=[Hd("VCB", "Vietcombank", 150, 88000, 91500), Hd("SSI", "SSI", 400, 30000, 28700)])
    s.say("Bán hết chỗ VCB tôi đang giữ, giá thị trường.",
          C(f"{A}.get_portfolio"),
          C(f"{A}.place_order", symbol="VCB", side="sell", quantity=150))
    S.append(s)

    # 5. hỏi giá (read)
    s = Sc(A, "2026-11-22T11:00", [A], 4)
    s.state[A] = ST(quotes=[Q("VIC", "Vingroup", 44200, 2.1)])
    s.say("VIC giờ nhiêu rồi?",
          C(f"{A}.get_quote", symbol="VIC"))
    S.append(s)

    # 6. xem danh mục (read)
    s = Sc(A, "2026-11-23T15:10", [A], 5)
    s.state[A] = ST(holdings=[Hd("FPT", "FPT Corp", 100, 110000, 128500), Hd("ACB", "ACB", 1000, 24000, 25100)])
    s.say("Danh mục của chị giờ lời lỗ thế nào rồi?",
          C(f"{A}.get_portfolio"))
    S.append(s)

    # 7. cảnh báo vượt ngưỡng -> above
    s = Sc(A, "2026-11-24T09:50", [A], 6)
    s.state[A] = ST(quotes=[Q("FPT", "FPT Corp", 128500, 1.2)])
    s.say("FPT mà lên tới một trăm ba mươi nghìn thì báo cho anh nhé.",
          C(f"{A}.set_price_alert", symbol="FPT", price=130000, direction="above"))
    S.append(s)

    # 8. cảnh báo rớt -> below
    s = Sc(A, "2026-11-25T14:20", [A], 7)
    s.state[A] = ST(holdings=[Hd("HPG", "Hòa Phát", 2000, 26000, 27800)])
    s.say("Đặt cảnh báo HPG rớt xuống dưới hai mươi lăm nghìn.",
          C(f"{A}.set_price_alert", symbol="HPG", price=25000, direction="below"))
    S.append(s)

    # 9. điều kiện giá: nếu dưới X thì mua -> đúng
    s = Sc(A, "2026-11-26T10:30", [A], 0)
    s.state[A] = ST(quotes=[Q("VNM", "Vinamilk", 64800, -0.9)])
    s.say("Xem VNM đang giá nhiêu, dưới sáu lăm thì mua năm trăm cổ giá thị trường.",
          C(f"{A}.get_quote", symbol="VNM"),
          C(f"{A}.place_order", symbol="VNM", side="buy", quantity=500))
    S.append(s)

    # 10. điều kiện sai -> chỉ xem giá
    s = Sc(A, "2026-11-26T10:30", [A], 0)
    s.state[A] = ST(quotes=[Q("VNM", "Vinamilk", 66200, 1.1)])
    s.say("Xem VNM đang giá nhiêu, dưới sáu lăm thì mua năm trăm cổ giá thị trường.",
          C(f"{A}.get_quote", symbol="VNM"))
    S.append(s)

    # 11. thiếu số lượng -> ask quantity
    s = Sc(A, "2026-11-27T09:05", [A], 1)
    s.state[A] = ST(quotes=[Q("MSN", "Masan", 72000, 0.3)])
    s.say("Mua ít MSN giá thị trường cho em.",
          ASK(f"{A}.place_order", "quantity"))
    S.append(s)

    # 12. thiếu mã -> ask symbol? Người dùng: "mua 100 cổ ngân hàng nào đó" -> ask symbol
    s = Sc(A, "2026-11-27T09:05", [A], 1)
    s.state[A] = ST(quotes=[Q("VCB", "Vietcombank", 91500, 0.2), Q("TCB", "Techcombank", 23400, 0.5)])
    s.say("Mua một trăm cổ phiếu ngân hàng giá thị trường, mã nào cũng được.",
          ASK(f"{A}.place_order", "symbol"))
    S.append(s)

    # 13. history có get_quote; lượt sau mua
    s = Sc(A, "2026-11-28T10:15", [A], 2)
    s.state[A] = ST(quotes=[Q("SSI", "SSI", 28700, -1.0)])
    s.user("SSI giờ bao nhiêu?")
    s.bot("SSI đang 28.700đ, giảm 1% ạ.", C(f"{A}.get_quote", symbol="SSI"))
    s.say("Rẻ, múc một nghìn cổ giá thị trường.",
          C(f"{A}.place_order", symbol="SSI", side="buy", quantity=1000))
    S.append(s)

    # 14. [] - chat / nhận định thị trường
    s = Sc(A, "2026-11-29T20:00", [A], 3)
    s.state[A] = ST(holdings=[Hd("FPT", "FPT Corp", 100, 110000, 128500)])
    s.say("Theo em thì tuần sau thị trường lên hay xuống?")
    S.append(s)

    # 15. bán + nhắc
    s = Sc(A, "2026-12-01T09:40", [A, "reminders"], 4)
    s.state[A] = ST(holdings=[Hd("DGC", "Hóa chất Đức Giang", 300, 95000, 112000)])
    s.state["reminders"] = reminders()
    s.say("Bán một trăm cổ DGC giá một trăm mười lăm nghìn, rồi nhắc anh hai giờ chiều kiểm tra lệnh khớp chưa.",
          C(f"{A}.place_order", symbol="DGC", side="sell", quantity=100, price=115000),
          C("reminders.create", content="Kiểm tra lệnh bán DGC khớp chưa", time=s.t(0, 14)))
    S.append(s)

    # 16. không đủ cổ phiếu để bán -> get_portfolio thấy không đủ -> không đặt lệnh
    s = Sc(A, "2026-12-02T10:00", [A], 5)
    s.state[A] = ST(holdings=[Hd("VHM", "Vinhomes", 200, 40000, 43500)])
    s.say("Bán năm trăm cổ VHM giá thị trường, kiểm tra danh mục trước xem đủ không.",
          C(f"{A}.get_portfolio"))
    S.append(s)

    # 17. hai lệnh một lúc
    s = Sc(A, "2026-12-03T09:30", [A], 6)
    s.state[A] = ST(quotes=[Q("FPT", "FPT Corp", 128500, 1.2), Q("MWG", "Thế Giới Di Động", 61000, 0.8)])
    s.say("Mua một trăm FPT với hai trăm MWG, đều giá thị trường.",
          C(f"{A}.place_order", symbol="FPT", side="buy", quantity=100),
          C(f"{A}.place_order", symbol="MWG", side="buy", quantity=200))
    S.append(s)

    # 18. cảnh báo hai chiều cho 1 mã
    s = Sc(A, "2026-12-04T11:10", [A], 7)
    s.state[A] = ST(holdings=[Hd("VNM", "Vinamilk", 300, 60000, 65300)])
    s.say("VNM lên bảy mươi hoặc xuống sáu mươi thì đều báo tôi.",
          C(f"{A}.set_price_alert", symbol="VNM", price=70000, direction="above"),
          C(f"{A}.set_price_alert", symbol="VNM", price=60000, direction="below"))
    S.append(s)

    # 19. [] - đã trả lời trong history
    s = Sc(A, "2026-12-05T13:00", [A], 0)
    s.state[A] = ST(quotes=[Q("HPG", "Hòa Phát", 27800, 0.7)])
    s.user("HPG giờ sao?")
    s.bot("HPG đang 27.800đ, tăng 0,7% ạ.", C(f"{A}.get_quote", symbol="HPG"))
    s.say("Hai bảy tám à, vẫn chưa về vùng anh muốn.")
    S.append(s)

    # 20. mã đọc bằng chữ: "vê en em" -> cần symbol VNM; dùng dạng dễ: "mã vê cê bê"
    s = Sc(A, "2026-12-06T09:15", [A], 1)
    s.state[A] = ST(quotes=[Q("VCB", "Vietcombank", 91500, 0.2)])
    s.say("Giá mã VCB hôm nay thế nào?",
          C(f"{A}.get_quote", symbol="VCB"))
    S.append(s)

    # 21. ghi chú giá vào notes sau khi xem
    s = Sc(A, "2026-12-07T15:30", [A, "notes"], 2)
    s.state[A] = ST(quotes=[Q("FPT", "FPT Corp", 131000, 1.9)])
    s.state["notes"] = notes(("note_01", "Theo dõi FPT", "20/11: 128.5"))
    s.say("Xem giá FPT rồi thêm vào ghi chú Theo dõi FPT dòng hôm nay giá bao nhiêu.",
          C(f"{A}.get_quote", symbol="FPT"),
          C("notes.list"),
          C("notes.append", note_id="note_01", content=f"{s.dm(0)}: 131.000"))
    S.append(s)

    # 22. bán toàn bộ 2 mã
    s = Sc(A, "2026-12-08T14:00", [A], 3)
    s.state[A] = ST(holdings=[Hd("SSI", "SSI", 400, 30000, 28700), Hd("ACB", "ACB", 1000, 24000, 25100)])
    s.say("Thị trường xấu quá, bán sạch danh mục đi, giá thị trường.",
          C(f"{A}.get_portfolio"),
          C(f"{A}.place_order", symbol="SSI", side="sell", quantity=400),
          C(f"{A}.place_order", symbol="ACB", side="sell", quantity=1000))
    S.append(s)

    # 23. [] - huỷ
    s = Sc(A, "2026-12-09T09:00", [A], 4)
    s.state[A] = ST(quotes=[Q("VIC", "Vingroup", 44200, 2.1)])
    s.say("Mua hai trăm VIC... thôi khoan, để anh xem tin đã.")
    S.append(s)

    # 24. tiếng Anh lẫn: "buy 100 shares FPT, limit 125k"
    s = Sc(A, "2026-12-10T10:20", [A], 5)
    s.state[A] = ST(quotes=[Q("FPT", "FPT Corp", 128500, 1.2)])
    s.say("Buy một trăm share FPT, limit một trăm hai lăm nghìn.",
          C(f"{A}.place_order", symbol="FPT", side="buy", quantity=100, price=125000))
    S.append(s)

    # 25. báo bạn qua chat sau khi mua
    s = Sc(A, "2026-12-11T09:45", [A, "chat_ott"], 6)
    s.state[A] = ST(quotes=[Q("HPG", "Hòa Phát", 27800, 0.7)])
    s.state["chat_ott"] = chats(("chat_01", "Tuấn", "direct"), ("chat_02", "Hội chứng khoán", "group"))
    s.say("Mua năm trăm HPG giá thị trường, xong nhắn Tuấn là 'tao vào HPG rồi'.",
          C(f"{A}.place_order", symbol="HPG", side="buy", quantity=500),
          C("chat_ott.list_chats"),
          C("chat_ott.send_message", chat_id="chat_01", content="tao vào HPG rồi"))
    S.append(s)

    # 26. [] - không app nào: muốn nạp tiền vào tài khoản chứng khoán (không có tool)
    s = Sc(A, "2026-12-11T09:45", [A], 6)
    s.state[A] = ST(quotes=[Q("HPG", "Hòa Phát", 27800, 0.7)])
    s.say("Nạp thêm năm mươi triệu vào tài khoản chứng khoán cho anh.")
    S.append(s)

    # 27. cảnh báo khi "về" giá thấp hơn hiện tại -> below
    s = Sc(A, "2026-11-30T10:40", [A], 7)
    s.state[A] = ST(quotes=[Q("MWG", "Thế Giới Di Động", 61000, 0.8)])
    s.say("MWG về năm mươi lăm thì nhắc tôi mua nhé.",
          C(f"{A}.set_price_alert", symbol="MWG", price=55000, direction="below"))
    S.append(s)

    # 28. xem giá hai mã
    s = Sc(A, "2026-11-30T10:40", [A], 7)
    s.state[A] = ST(quotes=[Q("VCB", "Vietcombank", 91500, 0.2), Q("TCB", "Techcombank", 23400, 0.5)])
    s.say("So giúp em giá VCB với TCB hôm nay.",
          C(f"{A}.get_quote", symbol="VCB"),
          C(f"{A}.get_quote", symbol="TCB"))
    S.append(s)

    return S
