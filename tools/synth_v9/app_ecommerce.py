from common import *

A = "ecommerce"


def P(i, name, price, seller, cat, rating=4.5, stock=True, tags=None):
    d = {"id": i, "name": name, "price": price, "seller": seller, "category": cat, "rating": rating, "in_stock": stock}
    if tags:
        d["tags"] = tags
    return d


def O(i, items, total, status, placed, delivered=None, payment="cod"):
    d = {"id": i, "items": items, "total": total, "status": status, "placed_at": placed, "payment": payment}
    if delivered:
        d["delivered_at"] = delivered
    return d


def build():
    S = []

    # 1. tìm -> thêm giỏ -> đặt, giao về nhà, trả bằng ví (payment nói rõ)
    s = Sc(A, "2026-11-18T20:15", [A, "ewallet"], 0)
    s.state[A] = {"products": [P("prod_01", "Nồi chiên không dầu Lock&Lock 5.2L", 1590000, "Lock&Lock Official", "gia dụng"),
                               P("prod_02", "Nồi cơm điện Sharp 1.8L", 890000, "Sharp Việt Nam", "gia dụng"),
                               P("prod_03", "Máy xay sinh tố Philips", 1150000, "Philips Store", "gia dụng")],
                  "cart": [], "orders": [], "returns": []}
    s.state["ewallet"] = ewallet(5000000)
    s.say("Em ơi mua giùm chị cái nồi chiên không dầu, giao về nhà, thanh toán bằng ví điện tử luôn nha.",
          C(f"{A}.search", query="nồi chiên không dầu"),
          C(f"{A}.add_to_cart", product_id="prod_01", quantity=1),
          C(f"{A}.checkout", address=s.prof["home_address"], payment="ewallet"))
    S.append(s)

    # 2. hai sản phẩm khớp, chọn cái rẻ hơn, không nói địa chỉ -> checkout {}
    s = Sc(A, "2026-11-21T12:40", [A], 1)
    s.state[A] = {"products": [P("prod_11", "Tai nghe Bluetooth Sony WH-CH520", 1290000, "Sony Center", "điện tử"),
                               P("prod_12", "Tai nghe Bluetooth Baseus Bowie D03", 450000, "Baseus Official", "điện tử"),
                               P("prod_13", "Loa Bluetooth JBL Go 3", 890000, "JBL Store", "điện tử")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Tìm tai nghe bluetooth, cái nào rẻ nhất thì cho vào giỏ rồi đặt luôn.",
          C(f"{A}.search", query="tai nghe bluetooth"),
          C(f"{A}.add_to_cart", product_id="prod_12", quantity=1),
          C(f"{A}.checkout"))
    S.append(s)

    # 3. giới hạn giá nói rõ -> max_price; số lượng 2; chỉ thêm giỏ, chưa đặt
    s = Sc(A, "2026-11-25T09:05", [A, "notes"], 2)
    s.state[A] = {"products": [P("prod_21", "Áo thun nam cotton basic", 149000, "Coolmate", "thời trang"),
                               P("prod_22", "Áo thun nam Uniqlo Airism", 390000, "Uniqlo VN", "thời trang"),
                               P("prod_23", "Áo thun polo nam Routine", 259000, "Routine", "thời trang")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Bỏ vô giỏ cho anh hai cái áo thun nam, loại dưới hai trăm nghìn thôi, chưa thanh toán đâu để anh coi lại đã.",
          C(f"{A}.search", query="áo thun nam", max_price=200000),
          C(f"{A}.add_to_cart", product_id="prod_21", quantity=2))
    S.append(s)

    # 4. huỷ đơn đang giao (status shipping) -> order_status {} rồi cancel
    s = Sc(A, "2026-12-02T18:30", [A], 3)
    s.state[A] = {"products": [], "cart": [],
                  "orders": [O("ord_01", [{"product_id": "prod_31", "name": "Bàn phím cơ Keychron K2", "price": 2190000, "quantity": 1}], 2190000, "shipping", "2026-11-30T10:00:00+07:00"),
                              O("ord_02", [{"product_id": "prod_32", "name": "Chuột Logitech MX Master 3S", "price": 2390000, "quantity": 1}], 2390000, "delivered", "2026-11-20T10:00:00+07:00", "2026-11-23T15:00:00+07:00")],
                  "returns": []}
    s.say("Cái đơn bàn phím cơ đang giao á, huỷ giùm tui đi, tui lỡ đặt trùng rồi.",
          C(f"{A}.order_status"),
          C(f"{A}.cancel_order", order_id="ord_01"))
    S.append(s)

    # 5. trả hàng vì hỏng -> reason damaged
    s = Sc(A, "2026-11-28T21:00", [A, "chat_ott"], 4)
    s.state[A] = {"products": [], "cart": [],
                  "orders": [O("ord_01", [{"product_id": "prod_41", "name": "Bình giữ nhiệt Elmich 500ml", "price": 320000, "quantity": 2}], 640000, "delivered", "2026-11-22T09:00:00+07:00", "2026-11-26T14:20:00+07:00")],
                  "returns": []}
    s.state["chat_ott"] = chats(("chat_01", "Gia đình", "group"))
    s.say("Hai cái bình giữ nhiệt vừa nhận bị móp hết trơn, làm yêu cầu trả hàng hoàn tiền đơn đó cho em.",
          C(f"{A}.order_status"),
          C(f"{A}.request_return", order_id="ord_01", reason="damaged"))
    S.append(s)

    # 6. trả hàng vì giao sai -> wrong_item
    s = Sc(A, "2026-12-05T08:10", [A], 5)
    s.state[A] = {"products": [], "cart": [],
                  "orders": [O("ord_01", [{"product_id": "prod_51", "name": "Giày chạy bộ Nike Pegasus 41 size 42", "price": 3290000, "quantity": 1}], 3290000, "delivered", "2026-11-29T11:00:00+07:00", "2026-12-03T16:00:00+07:00", "bank"),
                              O("ord_02", [{"product_id": "prod_52", "name": "Tất thể thao Adidas", "price": 120000, "quantity": 3}], 360000, "placed", "2026-12-04T20:00:00+07:00")],
                  "returns": []}
    s.say("Đôi giày Nike người ta giao size 40 chứ không phải 42, anh muốn trả lại đơn đó.",
          C(f"{A}.order_status"),
          C(f"{A}.request_return", order_id="ord_01", reason="wrong_item"))
    S.append(s)

    # 7. đổi ý không cần nữa -> changed_mind, kèm nhắc việc ra bưu cục
    s = Sc(A, "2026-11-19T19:45", [A, "reminders"], 6)
    s.state[A] = {"products": [], "cart": [],
                  "orders": [O("ord_01", [{"product_id": "prod_61", "name": "Đèn bàn học LED Rạng Đông", "price": 450000, "quantity": 1}], 450000, "delivered", "2026-11-14T08:00:00+07:00", "2026-11-17T10:00:00+07:00")],
                  "returns": []}
    s.state["reminders"] = reminders()
    s.say("Cái đèn bàn mua tuần trước chị không dùng tới, trả lại đi, với nhắc chị chín giờ sáng mai mang ra bưu cục gửi.",
          C(f"{A}.order_status"),
          C(f"{A}.request_return", order_id="ord_01", reason="changed_mind"),
          C("reminders.create", content="Mang đèn bàn ra bưu cục gửi trả", time=s.t(1, 9)))
    S.append(s)

    # 8. chỉ hỏi trạng thái một đơn cụ thể trong history -> đọc có order_id? Gold: order_status {} (liệt kê) vì chưa biết id
    s = Sc(A, "2026-11-23T14:00", [A], 7)
    s.state[A] = {"products": [], "cart": [],
                  "orders": [O("ord_01", [{"product_id": "prod_71", "name": "Sữa rửa mặt Cetaphil 500ml", "price": 285000, "quantity": 1}], 285000, "shipping", "2026-11-21T09:30:00+07:00")],
                  "returns": []}
    s.say("Đơn sữa rửa mặt của em tới đâu rồi, coi giúp em với.",
          C(f"{A}.order_status"))
    S.append(s)

    # 9. history đã có order_status, lượt sau huỷ -> dùng id, không đọc lại
    s = Sc(A, "2026-12-01T10:20", [A], 0)
    s.state[A] = {"products": [], "cart": [],
                  "orders": [O("ord_01", [{"product_id": "prod_81", "name": "Máy sấy tóc Panasonic EH-NE65", "price": 1050000, "quantity": 1}], 1050000, "placed", "2026-11-30T22:00:00+07:00"),
                              O("ord_02", [{"product_id": "prod_82", "name": "Lược điện Dyson", "price": 9900000, "quantity": 1}], 9900000, "shipping", "2026-11-28T22:00:00+07:00")],
                  "returns": []}
    s.user("Mấy đơn của chị đang thế nào rồi em?")
    s.bot("Chị có 2 đơn: máy sấy tóc Panasonic vừa đặt tối qua, và lược điện Dyson đang trên đường giao ạ.", C(f"{A}.order_status"))
    s.say("Ừ cái máy sấy đó huỷ đi, chị thấy chỗ khác rẻ hơn.",
          C(f"{A}.cancel_order", order_id="ord_01"))
    S.append(s)

    # 10. thiếu số lượng? Không: "mua" mặc định 1. Thiếu: hai sản phẩm cùng tên, user không phân biệt -> ask product_id
    s = Sc(A, "2026-11-26T16:30", [A], 1)
    s.state[A] = {"products": [P("prod_91", "Ốp lưng iPhone 15 Pro trong suốt Spigen", 350000, "Spigen VN", "phụ kiện"),
                               P("prod_92", "Ốp lưng iPhone 15 Pro silicon đen Apple", 1190000, "Apple Store", "phụ kiện")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Đặt cho tôi cái ốp lưng iPhone 15 Pro.",
          C(f"{A}.search", query="ốp lưng iPhone 15 Pro"),
          ASK(f"{A}.add_to_cart", "product_id"))
    S.append(s)

    # 11. hết hàng -> chỉ search, không thêm giỏ (báo lại)
    s = Sc(A, "2026-11-30T09:00", [A], 2)
    s.state[A] = {"products": [P("prod_101", "Máy lọc không khí Xiaomi 4 Lite", 2490000, "Xiaomi Official", "gia dụng", stock=False)],
                  "cart": [], "orders": [], "returns": []}
    s.say("Mua cái máy lọc không khí Xiaomi 4 Lite đi em.",
          C(f"{A}.search", query="máy lọc không khí Xiaomi 4 Lite"))
    S.append(s)

    # 12. giỏ đã có hàng từ lượt trước -> chỉ checkout, địa chỉ công ty
    s = Sc(A, "2026-11-20T11:50", [A], 3)
    s.state[A] = {"products": [P("prod_111", "Bộ cờ vua gỗ 40cm", 420000, "Gỗ Việt", "đồ chơi")],
                  "cart": [], "orders": [], "returns": []}
    s.user("Tìm bộ cờ vua gỗ bỏ vào giỏ cho anh.")
    s.bot("Đã thêm Bộ cờ vua gỗ 40cm giá 420.000đ vào giỏ ạ.", C(f"{A}.search", query="bộ cờ vua gỗ"), C(f"{A}.add_to_cart", product_id="prod_111", quantity=1))
    s.say("Ok đặt đi, giao tới chỗ làm của anh nhé.",
          C(f"{A}.checkout", address=s.prof["work_address"]))
    S.append(s)

    # 13. điều kiện giá: nếu dưới 1 triệu thì mua, kết quả trên 1 triệu -> chỉ search
    s = Sc(A, "2026-12-03T22:10", [A], 4)
    s.state[A] = {"products": [P("prod_121", "Đồng hồ thông minh Xiaomi Smart Band 9", 1090000, "Xiaomi Official", "điện tử")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Coi cái Xiaomi Smart Band 9 giá nhiêu, dưới một triệu thì mua cho em một cái.",
          C(f"{A}.search", query="Xiaomi Smart Band 9"))
    S.append(s)

    # 14. điều kiện đúng -> mua
    s = Sc(A, "2026-12-03T22:10", [A], 4)
    s.state[A] = {"products": [P("prod_121", "Đồng hồ thông minh Xiaomi Smart Band 9", 890000, "Xiaomi Official", "điện tử")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Coi cái Xiaomi Smart Band 9 giá nhiêu, dưới một triệu thì mua cho em một cái.",
          C(f"{A}.search", query="Xiaomi Smart Band 9"),
          C(f"{A}.add_to_cart", product_id="prod_121", quantity=1),
          C(f"{A}.checkout"))
    S.append(s)

    # 15. ba món một lần, cùng giỏ, đặt chung, chuyển khoản ngân hàng
    s = Sc(A, "2026-11-22T15:20", [A], 5)
    s.state[A] = {"products": [P("prod_131", "Giấy in A4 Double A 80gsm", 95000, "VPP Hồng Hà", "văn phòng phẩm"),
                               P("prod_132", "Bút bi Thiên Long TL-027 hộp 20", 60000, "Thiên Long", "văn phòng phẩm"),
                               P("prod_133", "Băng keo trong 5cm", 15000, "VPP Hồng Hà", "văn phòng phẩm")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Đặt cho văn phòng năm ram giấy A4 với hai hộp bút bi Thiên Long, thanh toán chuyển khoản ngân hàng.",
          C(f"{A}.search", query="giấy A4"),
          C(f"{A}.add_to_cart", product_id="prod_131", quantity=5),
          C(f"{A}.search", query="bút bi Thiên Long"),
          C(f"{A}.add_to_cart", product_id="prod_132", quantity=2),
          C(f"{A}.checkout", payment="bank"))
    S.append(s)

    # 16. [] - sàn không bán thứ user hỏi? không: ngoài phạm vi: hỏi vận chuyển bao lâu (chat phiếm)
    s = Sc(A, "2026-11-24T08:00", [A, "weather"], 6)
    s.state[A] = {"products": [], "cart": [], "orders": [], "returns": []}
    s.state["weather"] = weather(s.city, {s.d(0): ("mưa rào", 24, 29, 80)})
    s.say("Dạo này sale nhiều quá mà ví thì mỏng, em thấy anh có nên nhịn mua sắm tháng này không?")
    S.append(s)

    # 17. [] - đã trả lời trong history (hỏi lại giá)
    s = Sc(A, "2026-11-27T13:15", [A], 7)
    s.state[A] = {"products": [P("prod_141", "Robot hút bụi Ecovacs Deebot N10", 6490000, "Ecovacs VN", "gia dụng")],
                  "cart": [], "orders": [], "returns": []}
    s.user("Robot hút bụi Ecovacs N10 trên sàn đang bao nhiêu?")
    s.bot("Robot hút bụi Ecovacs Deebot N10 đang bán 6.490.000đ, shop Ecovacs VN ạ.", C(f"{A}.search", query="robot hút bụi Ecovacs N10"))
    s.say("Sáu triệu rưỡi hả, đắt thế. Thôi để anh nghĩ đã, khỏi mua.")
    S.append(s)

    # 18. history có search, lượt sau quyết định mua 1 cái -> add + checkout, không search lại
    s = Sc(A, "2026-11-27T13:15", [A], 7)
    s.state[A] = {"products": [P("prod_141", "Robot hút bụi Ecovacs Deebot N10", 6490000, "Ecovacs VN", "gia dụng")],
                  "cart": [], "orders": [], "returns": []}
    s.user("Robot hút bụi Ecovacs N10 trên sàn đang bao nhiêu?")
    s.bot("Robot hút bụi Ecovacs Deebot N10 đang bán 6.490.000đ, shop Ecovacs VN ạ.", C(f"{A}.search", query="robot hút bụi Ecovacs N10"))
    s.say("Được đó, lấy một cái, giao về nhà anh.",
          C(f"{A}.add_to_cart", product_id="prod_141", quantity=1),
          C(f"{A}.checkout", address=s.prof["home_address"]))
    S.append(s)

    # 19. sửa lời giữa câu: "ba cái à không hai cái"
    s = Sc(A, "2026-12-06T17:40", [A], 0)
    s.state[A] = {"products": [P("prod_151", "Khăn tắm cotton Mollis 70x140", 185000, "Mollis", "gia dụng")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Lấy cho chị ba cái khăn tắm Mollis, à không, hai cái thôi, bỏ giỏ rồi đặt luôn.",
          C(f"{A}.search", query="khăn tắm Mollis"),
          C(f"{A}.add_to_cart", product_id="prod_151", quantity=2),
          C(f"{A}.checkout"))
    S.append(s)

    # 20. mua tặng + nhắn chat báo cho người nhận
    s = Sc(A, "2026-11-29T10:30", [A, "chat_ott", "contacts"], 1)
    s.state[A] = {"products": [P("prod_161", "Hộp quà socola Ferrero Rocher 24 viên", 290000, "Ferrero VN", "thực phẩm")],
                  "cart": [], "orders": [], "returns": []}
    s.state["chat_ott"] = chats(("chat_01", "Mẹ", "direct"), ("chat_02", "Lan", "direct"))
    s.state["contacts"] = contacts(("c_01", "Lan", "em gái", "0912345678"))
    s.say("Đặt hộp socola Ferrero 24 viên gửi về nhà, xong nhắn Zalo cho Lan là anh gửi quà sinh nhật rồi nhé.",
          C(f"{A}.search", query="socola Ferrero 24 viên"),
          C(f"{A}.add_to_cart", product_id="prod_161", quantity=1),
          C(f"{A}.checkout", address=s.prof["home_address"]),
          C("chat_ott.list_chats"),
          C("chat_ott.send_message", chat_id="chat_02", content="Anh gửi quà sinh nhật cho em rồi nhé"))
    S.append(s)

    # 21. đọc trạng thái đơn đã có id trong history -> order_status(order_id)
    s = Sc(A, "2026-12-04T09:15", [A], 2)
    s.state[A] = {"products": [P("prod_171", "Vali kéo 24 inch Larita", 1390000, "Larita", "du lịch")],
                  "cart": [], "orders": [], "returns": []}
    s.user("Mua cái vali Larita 24 inch, giao về nhà.")
    s.bot("Đã đặt vali kéo 24 inch Larita, mã đơn ord_01, giao về nhà ạ.",
          C(f"{A}.search", query="vali Larita 24 inch"), C(f"{A}.add_to_cart", product_id="prod_171", quantity=1), C(f"{A}.checkout", address=s.prof["home_address"]))
    s.say("Đơn vali đó giờ trạng thái sao rồi?",
          C(f"{A}.order_status", order_id="ord_01"))
    S.append(s)

    # 22. hủy đơn: hai đơn cùng đang placed, không rõ đơn nào -> ask order_id
    s = Sc(A, "2026-11-30T20:00", [A], 3)
    s.state[A] = {"products": [], "cart": [],
                  "orders": [O("ord_01", [{"product_id": "prod_181", "name": "Áo khoác gió nam", "price": 350000, "quantity": 1}], 350000, "placed", "2026-11-30T19:00:00+07:00"),
                              O("ord_02", [{"product_id": "prod_182", "name": "Quần jean nam", "price": 420000, "quantity": 1}], 420000, "placed", "2026-11-30T19:05:00+07:00")],
                  "returns": []}
    s.say("Huỷ giúp tôi cái đơn vừa đặt lúc nãy.",
          C(f"{A}.order_status"),
          ASK(f"{A}.cancel_order", "order_id"))
    S.append(s)

    # 23. đơn delivered mà user đòi huỷ -> không huỷ được; user nói "không được thì trả hàng" -> request_return other
    s = Sc(A, "2026-12-02T11:00", [A], 4)
    s.state[A] = {"products": [], "cart": [],
                  "orders": [O("ord_01", [{"product_id": "prod_191", "name": "Ghế công thái học Sihoo M57", "price": 3990000, "quantity": 1}], 3990000, "delivered", "2026-11-25T09:00:00+07:00", "2026-11-30T13:00:00+07:00")],
                  "returns": []}
    s.say("Cái ghế Sihoo huỷ đơn được không, không huỷ được thì làm trả hàng giúp chị, lý do là ngồi không hợp.",
          C(f"{A}.order_status"),
          C(f"{A}.request_return", order_id="ord_01", reason="other"))
    S.append(s)

    # 24. nhiều món khác loại, giới hạn giá cho 1 món; thêm ghi chú
    s = Sc(A, "2026-11-21T21:30", [A, "notes"], 5)
    s.state[A] = {"products": [P("prod_201", "Bàn gấp laptop gỗ", 260000, "Gỗ Việt", "nội thất"),
                               P("prod_202", "Bàn làm việc gỗ 120cm", 1850000, "Nội thất Hòa Phát", "nội thất"),
                               P("prod_203", "Đèn kẹp bàn LED", 120000, "Rạng Đông", "gia dụng")],
                  "cart": [], "orders": [], "returns": []}
    s.state["notes"] = notes()
    s.say("Mua cái bàn gấp laptop với cái đèn kẹp bàn, đặt luôn, rồi ghi chú lại là đã sắm đồ cho góc học tập.",
          C(f"{A}.search", query="bàn gấp laptop"),
          C(f"{A}.add_to_cart", product_id="prod_201", quantity=1),
          C(f"{A}.search", query="đèn kẹp bàn"),
          C(f"{A}.add_to_cart", product_id="prod_203", quantity=1),
          C(f"{A}.checkout"),
          C("notes.create", content="Đã sắm đồ cho góc học tập: bàn gấp laptop và đèn kẹp bàn"))
    S.append(s)

    # 25. chỉ xem giá (read) với max_price nói rõ "tầm dưới 3 triệu"
    s = Sc(A, "2026-11-19T10:10", [A], 6)
    s.state[A] = {"products": [P("prod_211", "Máy hút bụi cầm tay Deerma DX700", 690000, "Deerma", "gia dụng"),
                               P("prod_212", "Máy hút bụi Dyson V8", 9900000, "Dyson VN", "gia dụng")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Trên sàn có máy hút bụi nào tầm dưới ba triệu không, liệt kê anh xem.",
          C(f"{A}.search", query="máy hút bụi", max_price=3000000))
    S.append(s)

    # 26. [] - app không làm được: muốn đổi size (không có tool đổi hàng, chỉ trả hàng) -> nhưng user không muốn trả. Dùng chat phiếm khác: hỏi review
    s = Sc(A, "2026-11-19T10:10", [A], 6)
    s.state[A] = {"products": [], "cart": [], "orders": [], "returns": []}
    s.say("Ê theo em thì mua đồ điện tử trên sàn hay ra cửa hàng mua an tâm hơn?")
    S.append(s)

    # 27. lịch sử: đã add_to_cart, user đổi ý thôi không mua -> []
    s = Sc(A, "2026-12-07T15:00", [A], 7)
    s.state[A] = {"products": [P("prod_221", "Tủ lạnh mini Aqua 90L", 3290000, "Aqua VN", "gia dụng")],
                  "cart": [], "orders": [], "returns": []}
    s.user("Cho cái tủ lạnh mini Aqua vào giỏ.")
    s.bot("Đã thêm Tủ lạnh mini Aqua 90L vào giỏ, giá 3.290.000đ ạ.", C(f"{A}.search", query="tủ lạnh mini Aqua"), C(f"{A}.add_to_cart", product_id="prod_221", quantity=1))
    s.say("À mà thôi, để tháng sau có lương rồi tính, khoan đặt.")
    S.append(s)

    # 28. mua + tạo nhắc kiểm tra đơn sau 3 ngày
    s = Sc(A, "2026-11-24T19:20", [A, "reminders"], 0)
    s.state[A] = {"products": [P("prod_231", "Sách Atomic Habits bản tiếng Việt", 125000, "Nhã Nam", "sách")],
                  "cart": [], "orders": [], "returns": []}
    s.state["reminders"] = reminders()
    s.say("Đặt cuốn Atomic Habits, rồi ba ngày nữa tầm tám giờ tối nhắc chị kiểm tra đơn.",
          C(f"{A}.search", query="Atomic Habits"),
          C(f"{A}.add_to_cart", product_id="prod_231", quantity=1),
          C(f"{A}.checkout"),
          C("reminders.create", content="Kiểm tra đơn sách Atomic Habits", time=s.t(3, 20)))
    S.append(s)

    # 29. tìm theo shop: "của shop Coolmate"
    s = Sc(A, "2026-11-26T08:45", [A], 1)
    s.state[A] = {"products": [P("prod_241", "Quần short thể thao Coolmate", 189000, "Coolmate", "thời trang"),
                               P("prod_242", "Quần short kaki Routine", 299000, "Routine", "thời trang")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Mua hai cái quần short thể thao của Coolmate, trả tiền khi nhận hàng.",
          C(f"{A}.search", query="quần short thể thao Coolmate"),
          C(f"{A}.add_to_cart", product_id="prod_241", quantity=2),
          C(f"{A}.checkout", payment="cod"))
    S.append(s)

    # 30. kiểm tra đơn -> nếu đã giao thì tick việc trong tasks
    s = Sc(A, "2026-12-01T17:30", [A, "tasks"], 2)
    s.state[A] = {"products": [], "cart": [],
                  "orders": [O("ord_01", [{"product_id": "prod_251", "name": "Máy in Canon LBP2900", "price": 2890000, "quantity": 1}], 2890000, "delivered", "2026-11-27T09:00:00+07:00", "2026-11-30T14:00:00+07:00")],
                  "returns": []}
    s.state["tasks"] = tasks(("task_01", "Nhận máy in cho văn phòng", "", "normal", False), ("task_02", "Gửi báo cáo tuần", "", "high", False))
    s.say("Xem đơn máy in giao chưa, giao rồi thì đánh dấu xong cái việc nhận máy in giúp em.",
          C(f"{A}.order_status"),
          C("tasks.list"),
          C("tasks.complete", task_id="task_01"))
    S.append(s)

    # 31. số lượng thiếu rõ ràng? "mua pin AA" -> mặc định 1 vỉ. Thay vào đó: ask vì user nói "mua ít pin AA, lấy mấy vỉ nhỉ"? Không tự nhiên. Dùng: "bạn đặt giúp tôi nước giặt Omo, số lượng như lần trước" không có lần trước -> ask quantity
    s = Sc(A, "2026-11-28T09:40", [A], 3)
    s.state[A] = {"products": [P("prod_261", "Nước giặt OMO Matic 3.6kg", 189000, "Unilever", "tiêu dùng")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Đặt nước giặt OMO Matic loại 3.6 ký, lấy mấy can luôn cho đỡ phải mua lại.",
          C(f"{A}.search", query="nước giặt OMO Matic 3.6kg"),
          ASK(f"{A}.add_to_cart", "quantity"))
    S.append(s)

    # 32. giọng miền Trung, đặt hàng giao về quê (địa chỉ đọc)
    s = Sc(A, "2026-12-08T12:00", [A], 3)
    s.state[A] = {"products": [P("prod_271", "Máy đo huyết áp Omron HEM-7121", 890000, "Omron VN", "sức khỏe")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Mua cái máy đo huyết áp Omron gửi về cho mạ, địa chỉ là 34 Bùi Thị Xuân, thành phố Huế nghe.",
          C(f"{A}.search", query="máy đo huyết áp Omron"),
          C(f"{A}.add_to_cart", product_id="prod_271", quantity=1),
          C(f"{A}.checkout", address="34 Bùi Thị Xuân, thành phố Huế"))
    S.append(s)

    # 33. hỏi "đơn nào chưa giao" -> order_status {}
    s = Sc(A, "2026-11-25T18:00", [A], 4)
    s.state[A] = {"products": [], "cart": [],
                  "orders": [O("ord_01", [{"product_id": "p1", "name": "Nến thơm", "price": 150000, "quantity": 2}], 300000, "delivered", "2026-11-18T10:00:00+07:00", "2026-11-21T10:00:00+07:00"),
                              O("ord_02", [{"product_id": "p2", "name": "Gối ôm", "price": 220000, "quantity": 1}], 220000, "shipping", "2026-11-23T10:00:00+07:00")],
                  "returns": []}
    s.say("Tui còn đơn nào chưa nhận được không ta?",
          C(f"{A}.order_status"))
    S.append(s)

    # 34. huỷ đơn placed và đặt lại món khác rẻ hơn
    s = Sc(A, "2026-12-03T09:30", [A], 5)
    s.state[A] = {"products": [P("prod_281", "Ấm siêu tốc Philips HD9350", 650000, "Philips Store", "gia dụng"),
                               P("prod_282", "Ấm siêu tốc Sunhouse SHD1182", 230000, "Sunhouse", "gia dụng")],
                  "cart": [],
                  "orders": [O("ord_01", [{"product_id": "prod_281", "name": "Ấm siêu tốc Philips HD9350", "price": 650000, "quantity": 1}], 650000, "placed", "2026-12-03T08:00:00+07:00")],
                  "returns": []}
    s.say("Huỷ cái đơn ấm siêu tốc Philips vừa đặt, đổi qua mua cái ấm Sunhouse cho rẻ.",
          C(f"{A}.order_status"),
          C(f"{A}.cancel_order", order_id="ord_01"),
          C(f"{A}.search", query="ấm siêu tốc Sunhouse"),
          C(f"{A}.add_to_cart", product_id="prod_282", quantity=1),
          C(f"{A}.checkout"))
    S.append(s)

    # 35. [] - điều kiện sai từ history: "nếu còn hàng thì mua", history đã báo hết hàng
    s = Sc(A, "2026-11-29T14:25", [A], 6)
    s.state[A] = {"products": [P("prod_291", "Card đồ họa RTX 4070 Super", 16500000, "GearVN", "điện tử", stock=False)],
                  "cart": [], "orders": [], "returns": []}
    s.user("RTX 4070 Super còn hàng không?")
    s.bot("Card đồ họa RTX 4070 Super bên GearVN hiện đang hết hàng ạ.", C(f"{A}.search", query="RTX 4070 Super"))
    s.say("Tiếc thế. Nếu còn thì mua giúp anh, không thì thôi vậy.")
    S.append(s)

    # 36. mua 1 món, số lượng bằng chữ "nửa tá" = 6
    s = Sc(A, "2026-12-05T20:50", [A], 7)
    s.state[A] = {"products": [P("prod_301", "Ly thủy tinh Luminarc 350ml", 35000, "Luminarc", "gia dụng")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Đặt nửa tá ly thủy tinh Luminarc, giao về nhà giùm.",
          C(f"{A}.search", query="ly thủy tinh Luminarc"),
          C(f"{A}.add_to_cart", product_id="prod_301", quantity=6),
          C(f"{A}.checkout", address=s.prof["home_address"]))
    S.append(s)

    # 37. trả hàng nhưng đơn đã có yêu cầu trả rồi? -> tránh (noop). Thay: history có order_status, user yêu cầu trả hàng đơn delivered trong đó, lý do hàng lỗi
    s = Sc(A, "2026-12-06T10:05", [A], 0)
    s.state[A] = {"products": [], "cart": [],
                  "orders": [O("ord_01", [{"product_id": "p", "name": "Loa thanh Samsung HW-B550", "price": 3490000, "quantity": 1}], 3490000, "delivered", "2026-11-29T10:00:00+07:00", "2026-12-04T11:00:00+07:00")],
                  "returns": []}
    s.user("Đơn loa Samsung giao chưa em?")
    s.bot("Đơn loa thanh Samsung HW-B550 đã giao hôm 4/12 rồi ạ.", C(f"{A}.order_status"))
    s.say("Ờ, mà cái loa đó bật lên rè lắm, hư rồi, em làm trả hàng đi.",
          C(f"{A}.request_return", order_id="ord_01", reason="damaged"))
    S.append(s)

    # 38. mua và tạo sự kiện lịch nhận hàng? không tự nhiên. Thay: mua + ghi chú số tiền vào notes đã có (append)
    s = Sc(A, "2026-11-23T16:45", [A, "notes"], 1)
    s.state[A] = {"products": [P("prod_311", "Bình nước thể thao 1L Lock&Lock", 160000, "Lock&Lock Official", "thể thao")],
                  "cart": [], "orders": [], "returns": []}
    s.state["notes"] = notes(("note_01", "Chi tiêu tháng 11", "Tiền điện 850k"), ("note_02", "Ý tưởng", "..."))
    s.say("Mua cái bình nước thể thao Lock&Lock, xong ghi thêm vào ghi chú chi tiêu tháng 11 là bình nước 160k.",
          C(f"{A}.search", query="bình nước thể thao Lock&Lock"),
          C(f"{A}.add_to_cart", product_id="prod_311", quantity=1),
          C(f"{A}.checkout"),
          C("notes.list"),
          C("notes.append", note_id="note_01", content="Bình nước 160k"))
    S.append(s)

    # 39. tiếng Anh lẫn: "order cái power bank Anker 20000"
    s = Sc(A, "2026-11-27T22:30", [A], 2)
    s.state[A] = {"products": [P("prod_321", "Pin sạc dự phòng Anker PowerCore 20000mAh", 790000, "Anker VN", "phụ kiện", tags=["power bank"]),
                               P("prod_322", "Pin sạc dự phòng Anker 10000mAh", 490000, "Anker VN", "phụ kiện", tags=["power bank"])],
                  "cart": [], "orders": [], "returns": []}
    s.say("Order giúp em cái power bank Anker hai mươi nghìn mAh, thanh toán qua ví.",
          C(f"{A}.search", query="power bank Anker 20000mAh"),
          C(f"{A}.add_to_cart", product_id="prod_321", quantity=1),
          C(f"{A}.checkout", payment="ewallet"))
    S.append(s)

    # 40. read: so sánh giá hai shop -> 1 search
    s = Sc(A, "2026-11-20T09:00", [A], 3)
    s.state[A] = {"products": [P("prod_331", "Nồi áp suất điện Sunhouse 5L", 1090000, "Sunhouse", "gia dụng"),
                               P("prod_332", "Nồi áp suất điện Philips 6L", 2390000, "Philips Store", "gia dụng")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Nồi áp suất điện trên sàn có mấy loại, giá cả thế nào em?",
          C(f"{A}.search", query="nồi áp suất điện"))
    S.append(s)

    # 41. mua với địa chỉ do user đọc kèm số điện thoại trong câu (không dùng)
    s = Sc(A, "2026-12-09T08:20", [A], 4)
    s.state[A] = {"products": [P("prod_341", "Combo 3 hộp khẩu trang 4D Unicharm", 135000, "Unicharm", "sức khỏe")],
                  "cart": [], "orders": [], "returns": []}
    s.say("Đặt hai combo khẩu trang Unicharm, ship về 18 ngõ 72 Nguyễn Trãi, Thanh Xuân nhé.",
          C(f"{A}.search", query="khẩu trang Unicharm"),
          C(f"{A}.add_to_cart", product_id="prod_341", quantity=2),
          C(f"{A}.checkout", address="18 ngõ 72 Nguyễn Trãi, Thanh Xuân"))
    S.append(s)

    # 42. history: lượt trước đã đặt, lượt này hỏi "tổng bao nhiêu tiền" -> đã có trong history -> []
    s = Sc(A, "2026-12-09T08:20", [A], 4)
    s.state[A] = {"products": [P("prod_341", "Combo 3 hộp khẩu trang 4D Unicharm", 135000, "Unicharm", "sức khỏe")],
                  "cart": [], "orders": [], "returns": []}
    s.user("Đặt hai combo khẩu trang Unicharm.")
    s.bot("Đã đặt 2 combo khẩu trang 4D Unicharm, tổng 270.000đ, thanh toán khi nhận hàng ạ.",
          C(f"{A}.search", query="khẩu trang Unicharm"), C(f"{A}.add_to_cart", product_id="prod_341", quantity=2), C(f"{A}.checkout"))
    s.say("Tổng hết nhiêu tiền ấy nhỉ?")
    S.append(s)

    return S
