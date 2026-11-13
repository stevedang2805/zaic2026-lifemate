from common import *

A = "grocery"


def G(i, name, price, unit, cat, stock=True, tags=None):
    d = {"id": i, "name": name, "price": price, "unit": unit, "category": cat, "in_stock": stock}
    if tags:
        d["tags"] = tags
    return d


def build():
    S = []

    # 1. mua 1 món, số lượng bằng chữ, giao về nhà
    s = Sc(A, "2026-11-18T07:40", [A], 0)
    s.state[A] = {"products": [G("prod_01", "Trứng gà ta vỉ 10", 42000, "vỉ", "trứng"), G("prod_02", "Trứng vịt vỉ 10", 38000, "vỉ", "trứng")],
                  "cart": [], "orders": []}
    s.say("Đặt giúp chị hai vỉ trứng gà ta, giao về nhà nha.",
          C(f"{A}.search", query="trứng gà ta"),
          C(f"{A}.add_to_cart", product_id="prod_01", quantity=2),
          C(f"{A}.checkout", address=s.prof["home_address"]))
    S.append(s)

    # 2. nhiều món, giờ giao nói rõ
    s = Sc(A, "2026-11-20T06:50", [A], 1)
    s.state[A] = {"products": [G("prod_11", "Sữa tươi Vinamilk không đường 1L", 34000, "hộp", "sữa"),
                               G("prod_12", "Bánh mì sandwich Kinh Đô", 22000, "gói", "bánh"),
                               G("prod_13", "Chuối già 1kg", 25000, "kg", "trái cây")],
                  "cart": [], "orders": []}
    s.say("Mua ba hộp sữa tươi Vinamilk không đường với một ký chuối, giao lúc năm giờ chiều nay.",
          C(f"{A}.search", query="sữa tươi Vinamilk không đường"),
          C(f"{A}.add_to_cart", product_id="prod_11", quantity=3),
          C(f"{A}.search", query="chuối"),
          C(f"{A}.add_to_cart", product_id="prod_13", quantity=1),
          C(f"{A}.checkout", delivery_time=s.t(0, 17)))
    S.append(s)

    # 3. chỉ bỏ giỏ, chưa đặt
    s = Sc(A, "2026-11-22T10:15", [A], 2)
    s.state[A] = {"products": [G("prod_21", "Thịt ba chỉ heo 500g", 72000, "khay", "thịt"), G("prod_22", "Thịt bò thăn 300g", 115000, "khay", "thịt")],
                  "cart": [], "orders": []}
    s.say("Cho hai khay ba chỉ heo vô giỏ trước đi, lát em mua thêm rau rồi đặt chung.",
          C(f"{A}.search", query="ba chỉ heo"),
          C(f"{A}.add_to_cart", product_id="prod_21", quantity=2))
    S.append(s)

    # 4. giỏ đã có từ lượt trước, lượt này thêm rau + đặt
    s = Sc(A, "2026-11-22T10:15", [A], 2)
    s.state[A] = {"products": [G("prod_21", "Thịt ba chỉ heo 500g", 72000, "khay", "thịt"), G("prod_23", "Rau muống bó 500g", 12000, "bó", "rau")],
                  "cart": [], "orders": []}
    s.user("Cho hai khay ba chỉ heo vô giỏ trước đi.")
    s.bot("Đã thêm 2 khay Thịt ba chỉ heo 500g vào giỏ ạ.", C(f"{A}.search", query="ba chỉ heo"), C(f"{A}.add_to_cart", product_id="prod_21", quantity=2))
    s.say("Thêm một bó rau muống nữa rồi đặt luôn, giao về nhà.",
          C(f"{A}.search", query="rau muống"),
          C(f"{A}.add_to_cart", product_id="prod_23", quantity=1),
          C(f"{A}.checkout", address=s.prof["home_address"]))
    S.append(s)

    # 5. hết hàng -> chỉ search
    s = Sc(A, "2026-11-23T19:30", [A], 3)
    s.state[A] = {"products": [G("prod_31", "Cá hồi phi lê Na Uy 300g", 165000, "khay", "hải sản", stock=False)],
                  "cart": [], "orders": []}
    s.say("Mua một khay cá hồi phi lê Na Uy.",
          C(f"{A}.search", query="cá hồi phi lê Na Uy"))
    S.append(s)

    # 6. hai loại khớp, không rõ -> ask product_id
    s = Sc(A, "2026-11-24T08:00", [A], 4)
    s.state[A] = {"products": [G("prod_41", "Gạo ST25 túi 5kg", 185000, "túi", "gạo"), G("prod_42", "Gạo Jasmine túi 5kg", 120000, "túi", "gạo")],
                  "cart": [], "orders": []}
    s.say("Đặt một túi gạo năm ký giao về nhà giùm em.",
          C(f"{A}.search", query="gạo 5kg"),
          ASK(f"{A}.add_to_cart", "product_id"))
    S.append(s)

    # 7. số lượng thiếu
    s = Sc(A, "2026-11-25T17:20", [A], 5)
    s.state[A] = {"products": [G("prod_51", "Nước mắm Nam Ngư 750ml", 45000, "chai", "gia vị")],
                  "cart": [], "orders": []}
    s.say("Nhà hết nước mắm rồi, đặt nước mắm Nam Ngư về đi, nhiều nhiều chút.",
          C(f"{A}.search", query="nước mắm Nam Ngư"),
          ASK(f"{A}.add_to_cart", "quantity"))
    S.append(s)

    # 8. từ shopping_list: mua những món chưa tick
    s = Sc(A, "2026-11-26T18:10", [A, "shopping_list"], 6)
    s.state[A] = {"products": [G("prod_61", "Dầu ăn Neptune 1L", 58000, "chai", "gia vị"), G("prod_62", "Đường cát trắng Biên Hòa 1kg", 26000, "gói", "gia vị"),
                               G("prod_63", "Mì gói Hảo Hảo thùng 30", 115000, "thùng", "mì")],
                  "cart": [], "orders": []}
    s.state["shopping_list"] = shopping(("item_01", "dầu ăn", 1, False), ("item_02", "đường", 2, False), ("item_03", "nước rửa chén", 1, True))
    s.say("Xem danh sách đi chợ còn gì chưa mua thì đặt hết trên app đi chợ luôn, giao về nhà.",
          C("shopping_list.get"),
          C(f"{A}.search", query="dầu ăn"),
          C(f"{A}.add_to_cart", product_id="prod_61", quantity=1),
          C(f"{A}.search", query="đường"),
          C(f"{A}.add_to_cart", product_id="prod_62", quantity=2),
          C(f"{A}.checkout", address=s.prof["home_address"]))
    S.append(s)

    # 9. giao giờ "sáng mai tám giờ"
    s = Sc(A, "2026-11-27T21:05", [A], 7)
    s.state[A] = {"products": [G("prod_71", "Bún tươi 1kg", 18000, "kg", "bún phở"), G("prod_72", "Thịt bò bắp 500g", 95000, "khay", "thịt")],
                  "cart": [], "orders": []}
    s.say("Mai nhà nấu bún bò, đặt hai ký bún tươi với một khay bò bắp, giao tám giờ sáng mai.",
          C(f"{A}.search", query="bún tươi"),
          C(f"{A}.add_to_cart", product_id="prod_71", quantity=2),
          C(f"{A}.search", query="bò bắp"),
          C(f"{A}.add_to_cart", product_id="prod_72", quantity=1),
          C(f"{A}.checkout", delivery_time=s.t(1, 8)))
    S.append(s)

    # 10. [] - đổi ý
    s = Sc(A, "2026-11-28T11:00", [A], 0)
    s.state[A] = {"products": [G("prod_81", "Táo Envy New Zealand 1kg", 139000, "kg", "trái cây")], "cart": [], "orders": []}
    s.say("Mua một ký táo Envy... mà thôi, chiều đi siêu thị tiện mua luôn, khỏi đặt.")
    S.append(s)

    # 11. [] - không có app nào làm được (muốn gọi điện cho siêu thị, không cài phone)
    s = Sc(A, "2026-11-28T11:00", [A], 0)
    s.state[A] = {"products": [], "cart": [], "orders": []}
    s.say("Gọi lên tổng đài siêu thị hỏi xem mai có khuyến mãi gì không.")
    S.append(s)

    # 12. read only: hỏi giá
    s = Sc(A, "2026-11-29T09:10", [A], 1)
    s.state[A] = {"products": [G("prod_91", "Sầu riêng Ri6 1kg", 95000, "kg", "trái cây"), G("prod_92", "Sầu riêng Monthong 1kg", 125000, "kg", "trái cây")],
                  "cart": [], "orders": []}
    s.say("Sầu riêng trên app nay bao nhiêu một ký vậy?",
          C(f"{A}.search", query="sầu riêng"))
    S.append(s)

    # 13. điều kiện giá -> đúng -> mua
    s = Sc(A, "2026-11-29T09:10", [A], 1)
    s.state[A] = {"products": [G("prod_91", "Sầu riêng Ri6 1kg", 95000, "kg", "trái cây")], "cart": [], "orders": []}
    s.say("Sầu riêng Ri6 mà dưới trăm ngàn một ký thì lấy cho chị hai ký, đặt luôn.",
          C(f"{A}.search", query="sầu riêng Ri6"),
          C(f"{A}.add_to_cart", product_id="prod_91", quantity=2),
          C(f"{A}.checkout"))
    S.append(s)

    # 14. điều kiện giá -> sai -> chỉ search
    s = Sc(A, "2026-11-29T09:10", [A], 1)
    s.state[A] = {"products": [G("prod_91", "Sầu riêng Ri6 1kg", 135000, "kg", "trái cây")], "cart": [], "orders": []}
    s.say("Sầu riêng Ri6 mà dưới trăm ngàn một ký thì lấy cho chị hai ký, đặt luôn.",
          C(f"{A}.search", query="sầu riêng Ri6"))
    S.append(s)

    # 15. đặt + nhắc nhận hàng
    s = Sc(A, "2026-12-01T12:30", [A, "reminders"], 2)
    s.state[A] = {"products": [G("prod_101", "Nước suối Lavie thùng 24", 95000, "thùng", "đồ uống")], "cart": [], "orders": []}
    s.state["reminders"] = reminders()
    s.say("Đặt một thùng Lavie giao sáu giờ chiều nay, rồi nhắc tôi sáu giờ kém mười lăm xuống nhận hàng.",
          C(f"{A}.search", query="Lavie"),
          C(f"{A}.add_to_cart", product_id="prod_101", quantity=1),
          C(f"{A}.checkout", delivery_time=s.t(0, 18)),
          C("reminders.create", content="Xuống nhận thùng Lavie", time=s.t(0, 17, 45)))
    S.append(s)

    # 16. sửa lời: "một... à hai"
    s = Sc(A, "2026-12-02T07:15", [A], 3)
    s.state[A] = {"products": [G("prod_111", "Cà chua 1kg", 28000, "kg", "rau củ"), G("prod_112", "Hành tây 1kg", 24000, "kg", "rau củ")], "cart": [], "orders": []}
    s.say("Lấy cho mệ một ký cà chua, à mà hai ký đi, với một ký hành tây, đặt luôn hí.",
          C(f"{A}.search", query="cà chua"),
          C(f"{A}.add_to_cart", product_id="prod_111", quantity=2),
          C(f"{A}.search", query="hành tây"),
          C(f"{A}.add_to_cart", product_id="prod_112", quantity=1),
          C(f"{A}.checkout"))
    S.append(s)

    # 17. history đã search, lượt này chọn 1 trong 2 bằng tên
    s = Sc(A, "2026-12-03T16:40", [A], 4)
    s.state[A] = {"products": [G("prod_121", "Sữa chua Vinamilk có đường lốc 4", 26000, "lốc", "sữa"), G("prod_122", "Sữa chua TH true Yogurt lốc 4", 32000, "lốc", "sữa")],
                  "cart": [], "orders": []}
    s.user("Có sữa chua loại nào?")
    s.bot("Có 2 loại: Sữa chua Vinamilk có đường lốc 4 giá 26.000đ và Sữa chua TH true Yogurt lốc 4 giá 32.000đ ạ.", C(f"{A}.search", query="sữa chua"))
    s.say("Lấy ba lốc TH đi, đặt giao về nhà.",
          C(f"{A}.add_to_cart", product_id="prod_122", quantity=3),
          C(f"{A}.checkout", address=s.prof["home_address"]))
    S.append(s)

    # 18. giao địa chỉ công ty, giờ trưa
    s = Sc(A, "2026-12-04T09:25", [A], 5)
    s.state[A] = {"products": [G("prod_131", "Salad rau trộn hộp 300g", 39000, "hộp", "rau")], "cart": [], "orders": []}
    s.say("Đặt hai hộp salad rau trộn giao tới công ty lúc mười hai giờ trưa nay.",
          C(f"{A}.search", query="salad rau trộn"),
          C(f"{A}.add_to_cart", product_id="prod_131", quantity=2),
          C(f"{A}.checkout", address=s.prof["work_address"], delivery_time=s.t(0, 12)))
    S.append(s)

    # 19. [] - chat phiếm về nấu ăn
    s = Sc(A, "2026-12-05T18:00", [A, "recipes"], 6)
    s.state[A] = {"products": [], "cart": [], "orders": []}
    s.state["recipes"] = {"recipes": [], "saved": []}
    s.say("Nay mệt quá, chắc tối ăn mì gói cho xong, haha.")
    S.append(s)

    # 20. recipes -> grocery: mua nguyên liệu cho món (2 món thiếu nói rõ)
    s = Sc(A, "2026-12-06T09:45", [A, "recipes"], 7)
    s.state[A] = {"products": [G("prod_141", "Bí đỏ 1kg", 22000, "kg", "rau củ"), G("prod_142", "Sữa tươi không đường 1L", 34000, "hộp", "sữa")],
                  "cart": [], "orders": []}
    s.state["recipes"] = {"recipes": [{"id": "rcp_01", "name": "Súp bí đỏ kem tươi", "servings": 4, "tags": ["súp", "chay"],
                                       "ingredients": [{"name": "bí đỏ", "quantity": 500, "unit": "g"}, {"name": "sữa tươi", "quantity": 200, "unit": "ml"}],
                                       "steps": ["Hấp bí", "Xay", "Nấu với sữa"]}], "saved": []}
    s.say("Nhà hết bí đỏ với sữa tươi, mua mỗi thứ một phần trên app đi chợ để tối nấu súp bí đỏ, đặt luôn nhé.",
          C(f"{A}.search", query="bí đỏ"),
          C(f"{A}.add_to_cart", product_id="prod_141", quantity=1),
          C(f"{A}.search", query="sữa tươi"),
          C(f"{A}.add_to_cart", product_id="prod_142", quantity=1),
          C(f"{A}.checkout"))
    S.append(s)

    # 21. tiếng Anh lẫn: "order cheese với bơ"
    s = Sc(A, "2026-12-07T20:20", [A], 0)
    s.state[A] = {"products": [G("prod_151", "Phô mai Cheddar lát 200g", 68000, "gói", "sữa", tags=["cheese"]), G("prod_152", "Bơ lạt Anchor 227g", 85000, "hộp", "sữa", tags=["butter"])],
                  "cart": [], "orders": []}
    s.say("Order một gói cheese cheddar với một hộp bơ Anchor, giao về nhà.",
          C(f"{A}.search", query="cheese cheddar"),
          C(f"{A}.add_to_cart", product_id="prod_151", quantity=1),
          C(f"{A}.search", query="bơ Anchor"),
          C(f"{A}.add_to_cart", product_id="prod_152", quantity=1),
          C(f"{A}.checkout", address=s.prof["home_address"]))
    S.append(s)

    # 22. thêm vào giỏ số lượng "chục" = 10
    s = Sc(A, "2026-12-08T06:30", [A], 1)
    s.state[A] = {"products": [G("prod_161", "Trứng vịt lộn quả", 7000, "quả", "trứng")], "cart": [], "orders": []}
    s.say("Bỏ giỏ một chục trứng vịt lộn, đặt luôn.",
          C(f"{A}.search", query="trứng vịt lộn"),
          C(f"{A}.add_to_cart", product_id="prod_161", quantity=10),
          C(f"{A}.checkout"))
    S.append(s)

    # 23. [] - hỏi lại điều đã trả lời
    s = Sc(A, "2026-12-08T06:30", [A], 1)
    s.state[A] = {"products": [G("prod_161", "Trứng vịt lộn quả", 7000, "quả", "trứng")], "cart": [], "orders": []}
    s.user("Trứng vịt lộn bao nhiêu một quả?")
    s.bot("Trứng vịt lộn trên app 7.000đ một quả ạ.", C(f"{A}.search", query="trứng vịt lộn"))
    s.say("Bảy nghìn à, mắc hơn ngoài chợ nhỉ.")
    S.append(s)

    # 24. ghi vào tasks sau khi đặt
    s = Sc(A, "2026-12-09T15:10", [A, "tasks"], 2)
    s.state[A] = {"products": [G("prod_171", "Bột mì đa dụng Meizan 1kg", 32000, "gói", "bột")], "cart": [], "orders": []}
    s.state["tasks"] = tasks()
    s.say("Đặt hai gói bột mì Meizan, và thêm việc 'nướng bánh cho sinh nhật bé' hạn tám giờ tối thứ bảy này.",
          C(f"{A}.search", query="bột mì Meizan"),
          C(f"{A}.add_to_cart", product_id="prod_171", quantity=2),
          C(f"{A}.checkout"),
          C("tasks.add", title="Nướng bánh cho sinh nhật bé", due=s.t(s.next_wd(5, same_week=True), 20)))
    S.append(s)

    # 25. ask: giao khi nào? Không -> delivery_time tuỳ chọn, không hỏi. Dùng ask product_id với 2 loại nước giặt
    s = Sc(A, "2026-12-10T10:00", [A], 3)
    s.state[A] = {"products": [G("prod_181", "Nước giặt Ariel 3.2kg", 175000, "túi", "tiêu dùng"), G("prod_182", "Nước giặt OMO 3.7kg", 189000, "túi", "tiêu dùng")],
                  "cart": [], "orders": []}
    s.say("Đặt một túi nước giặt giao về nhà.",
          C(f"{A}.search", query="nước giặt"),
          ASK(f"{A}.add_to_cart", "product_id"))
    S.append(s)

    # 26. người dùng nói rõ hãng -> không ask
    s = Sc(A, "2026-12-10T10:00", [A], 3)
    s.state[A] = {"products": [G("prod_181", "Nước giặt Ariel 3.2kg", 175000, "túi", "tiêu dùng"), G("prod_182", "Nước giặt OMO 3.7kg", 189000, "túi", "tiêu dùng")],
                  "cart": [], "orders": []}
    s.say("Đặt một túi nước giặt Ariel giao về nhà.",
          C(f"{A}.search", query="nước giặt Ariel"),
          C(f"{A}.add_to_cart", product_id="prod_181", quantity=1),
          C(f"{A}.checkout", address=s.prof["home_address"]))
    S.append(s)

    # 27. mua và báo nhóm chat gia đình
    s = Sc(A, "2026-11-19T17:55", [A, "chat_ott"], 4)
    s.state[A] = {"products": [G("prod_191", "Gà ta nguyên con 1.5kg", 165000, "con", "thịt")], "cart": [], "orders": []}
    s.state["chat_ott"] = chats(("chat_01", "Gia đình", "group"), ("chat_02", "Team Marketing", "group"))
    s.say("Đặt một con gà ta giao về nhà, rồi nhắn nhóm Gia đình là tối nay có gà luộc nha.",
          C(f"{A}.search", query="gà ta"),
          C(f"{A}.add_to_cart", product_id="prod_191", quantity=1),
          C(f"{A}.checkout", address=s.prof["home_address"]),
          C("chat_ott.list_chats"),
          C("chat_ott.send_message", chat_id="chat_01", content="Tối nay có gà luộc nha"))
    S.append(s)

    # 28. giọng Bắc, giao "chiều mai tầm bốn rưỡi"
    s = Sc(A, "2026-11-21T22:00", [A], 5)
    s.state[A] = {"products": [G("prod_201", "Cam sành 1kg", 32000, "kg", "trái cây"), G("prod_202", "Cam vàng Úc 1kg", 89000, "kg", "trái cây")], "cart": [], "orders": []}
    s.say("Mua hộ tớ ba cân cam sành, giao chiều mai tầm bốn rưỡi nhé.",
          C(f"{A}.search", query="cam sành"),
          C(f"{A}.add_to_cart", product_id="prod_201", quantity=3),
          C(f"{A}.checkout", delivery_time=s.t(1, 16, 30)))
    S.append(s)

    # 29. read: có bán X không
    s = Sc(A, "2026-11-30T08:30", [A], 6)
    s.state[A] = {"products": [G("prod_211", "Nấm kim châm 150g", 12000, "gói", "rau củ")], "cart": [], "orders": []}
    s.say("App đi chợ có bán nấm kim châm không em?",
          C(f"{A}.search", query="nấm kim châm"))
    S.append(s)

    # 30. history: giỏ đã sẵn 3 món, user bảo đặt, giao "tối nay bảy giờ"
    s = Sc(A, "2026-12-11T15:30", [A], 7)
    s.state[A] = {"products": [G("prod_221", "Tôm sú 500g", 145000, "khay", "hải sản"), G("prod_222", "Rau cải ngọt 500g", 15000, "bó", "rau")], "cart": [], "orders": []}
    s.user("Bỏ vào giỏ một khay tôm sú với hai bó cải ngọt.")
    s.bot("Đã thêm 1 khay Tôm sú 500g và 2 bó Rau cải ngọt vào giỏ ạ.", C(f"{A}.search", query="tôm sú"), C(f"{A}.add_to_cart", product_id="prod_221", quantity=1),
          C(f"{A}.search", query="cải ngọt"), C(f"{A}.add_to_cart", product_id="prod_222", quantity=2))
    s.say("Rồi, chốt đơn đi, giao bảy giờ tối nay.",
          C(f"{A}.checkout", delivery_time=s.t(0, 19)))
    S.append(s)

    return S
