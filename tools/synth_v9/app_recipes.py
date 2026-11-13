from common import *

A = "recipes"


def R(i, name, servings, ings, tags=None, steps=None, time_min=30):
    return {"id": i, "name": name, "servings": servings, "tags": tags or [], "time_min": time_min,
            "ingredients": [{"name": n, "quantity": q, "unit": u} for n, q, u in ings],
            "steps": steps or ["Sơ chế nguyên liệu", "Nấu", "Nêm nếm và dọn ra đĩa"]}


def build():
    S = []

    # 1. tìm + lưu
    s = Sc(A, "2026-11-18T18:30", [A], 0)
    s.state[A] = {"recipes": [R("rcp_01", "Canh chua cá lóc", 4, [("cá lóc", 500, "g"), ("me", 50, "g"), ("cà chua", 2, "quả")], ["canh", "miền Nam"]),
                              R("rcp_02", "Cá lóc kho tộ", 4, [("cá lóc", 600, "g"), ("nước màu", 1, "muỗng")], ["kho"])], "saved": []}
    s.say("Tìm công thức canh chua cá lóc rồi lưu lại cho chị.",
          C(f"{A}.search", query="canh chua cá lóc"),
          C(f"{A}.save", recipe_id="rcp_01"))
    S.append(s)

    # 2. hỏi nguyên liệu theo số người -> servings
    s = Sc(A, "2026-11-19T10:00", [A], 1)
    s.state[A] = {"recipes": [R("rcp_01", "Phở bò", 4, [("xương bò", 1, "kg"), ("bánh phở", 800, "g"), ("thịt bò", 400, "g")], ["nước dùng"], time_min=180)], "saved": []}
    s.say("Nấu phở bò cho sáu người thì cần bao nhiêu thịt với bánh phở nhỉ?",
          C(f"{A}.search", query="phở bò", servings=6))
    S.append(s)

    # 3. xem các bước -> search rồi get
    s = Sc(A, "2026-11-20T16:45", [A], 2)
    s.state[A] = {"recipes": [R("rcp_01", "Bánh flan caramel", 6, [("trứng gà", 4, "quả"), ("sữa tươi", 500, "ml"), ("đường", 100, "g")], ["tráng miệng"],
                                 steps=["Thắng caramel", "Đánh trứng với sữa", "Hấp cách thủy 30 phút"])], "saved": []}
    s.say("Đọc cho em các bước làm bánh flan caramel.",
          C(f"{A}.search", query="bánh flan caramel"),
          C(f"{A}.get", recipe_id="rcp_01"))
    S.append(s)

    # 4. tìm theo nguyên liệu (chỉ đọc)
    s = Sc(A, "2026-11-21T11:20", [A], 3)
    s.state[A] = {"recipes": [R("rcp_01", "Gà kho gừng", 3, [("đùi gà", 500, "g"), ("gừng", 1, "củ")], ["kho"]),
                              R("rcp_02", "Gà rang muối", 4, [("gà", 1, "kg"), ("muối", 1, "muỗng")], ["chiên"]),
                              R("rcp_03", "Bò lúc lắc", 2, [("thịt bò", 300, "g")], ["xào"])], "saved": []}
    s.say("Nhà còn gà, có món gì làm từ gà không em?",
          C(f"{A}.search", query="gà"))
    S.append(s)

    # 5. history có search, lượt sau lưu món số 2 theo tên
    s = Sc(A, "2026-11-21T11:20", [A], 3)
    s.state[A] = {"recipes": [R("rcp_01", "Gà kho gừng", 3, [("đùi gà", 500, "g"), ("gừng", 1, "củ")], ["kho"]),
                              R("rcp_02", "Gà rang muối", 4, [("gà", 1, "kg"), ("muối", 1, "muỗng")], ["chiên"])], "saved": []}
    s.user("Có món gì làm từ gà không em?")
    s.bot("Có 2 món: Gà kho gừng và Gà rang muối ạ.", C(f"{A}.search", query="gà"))
    s.say("Lưu món gà rang muối lại đi.",
          C(f"{A}.save", recipe_id="rcp_02"))
    S.append(s)

    # 6. lưu 2 món
    s = Sc(A, "2026-11-22T20:00", [A], 4)
    s.state[A] = {"recipes": [R("rcp_01", "Sinh tố bơ", 2, [("bơ", 1, "quả"), ("sữa đặc", 2, "muỗng")], ["đồ uống"]),
                              R("rcp_02", "Sinh tố xoài", 2, [("xoài", 1, "quả")], ["đồ uống"]),
                              R("rcp_03", "Nước ép cam", 1, [("cam", 3, "quả")], ["đồ uống"])], "saved": []}
    s.say("Lưu giúp em công thức sinh tố bơ với sinh tố xoài.",
          C(f"{A}.search", query="sinh tố bơ"),
          C(f"{A}.save", recipe_id="rcp_01"),
          C(f"{A}.search", query="sinh tố xoài"),
          C(f"{A}.save", recipe_id="rcp_02"))
    S.append(s)

    # 7. recipes + grocery: tìm công thức, mua 1 nguyên liệu thiếu
    s = Sc(A, "2026-11-23T09:30", [A, "grocery"], 5)
    s.state[A] = {"recipes": [R("rcp_01", "Bún chả Hà Nội", 4, [("thịt ba chỉ", 500, "g"), ("bún", 1, "kg"), ("nước mắm", 100, "ml")], ["miền Bắc"])], "saved": []}
    s.state["grocery"] = {"products": [{"id": "prod_01", "name": "Thịt ba chỉ heo 500g", "price": 72000, "unit": "khay", "category": "thịt", "in_stock": True}], "cart": [], "orders": []}
    s.say("Xem công thức bún chả Hà Nội, rồi đặt một khay thịt ba chỉ trên app đi chợ, giao về nhà.",
          C(f"{A}.search", query="bún chả Hà Nội"),
          C("grocery.search", query="thịt ba chỉ"),
          C("grocery.add_to_cart", product_id="prod_01", quantity=1),
          C("grocery.checkout", address=s.prof["home_address"]))
    S.append(s)

    # 8. không tìm thấy -> search trả rỗng (vẫn ok) -> chỉ search
    s = Sc(A, "2026-11-24T12:00", [A], 6)
    s.state[A] = {"recipes": [R("rcp_01", "Cơm tấm sườn", 2, [("sườn", 2, "miếng")], ["miền Nam"])], "saved": []}
    s.say("Có công thức bánh xèo miền Tây không?",
          C(f"{A}.search", query="bánh xèo miền Tây"))
    S.append(s)

    # 9. [] - chat
    s = Sc(A, "2026-11-24T12:00", [A], 6)
    s.state[A] = {"recipes": [], "saved": []}
    s.say("Hôm qua nấu theo công thức mà mặn quá trời, chắc tại tay anh nêm hơi lố.")
    S.append(s)

    # 10. recipes + reminders: lưu rồi nhắc đi chợ
    s = Sc(A, "2026-11-25T21:30", [A, "reminders"], 7)
    s.state[A] = {"recipes": [R("rcp_01", "Lẩu Thái hải sản", 6, [("tôm", 500, "g"), ("mực", 300, "g"), ("gói gia vị lẩu Thái", 1, "gói")], ["lẩu"])], "saved": []}
    s.state["reminders"] = reminders()
    s.say("Lưu công thức lẩu Thái hải sản, mai bảy giờ sáng nhắc tôi đi chợ mua đồ nấu lẩu.",
          C(f"{A}.search", query="lẩu Thái hải sản"),
          C(f"{A}.save", recipe_id="rcp_01"),
          C("reminders.create", content="Đi chợ mua đồ nấu lẩu Thái", time=s.t(1, 7)))
    S.append(s)

    # 11. servings theo "hai vợ chồng" = 2
    s = Sc(A, "2026-11-26T17:10", [A], 0)
    s.state[A] = {"recipes": [R("rcp_01", "Mì Ý sốt bò bằm", 4, [("mì Ý", 400, "g"), ("thịt bò bằm", 300, "g"), ("sốt cà chua", 200, "g")], ["Ý"])], "saved": []}
    s.say("Mì Ý sốt bò bằm nấu cho hai vợ chồng ăn thì mỗi thứ bao nhiêu?",
          C(f"{A}.search", query="mì Ý sốt bò bằm", servings=2))
    S.append(s)

    # 12. hai món gần giống nhau, user nói rõ -> lưu đúng món
    s = Sc(A, "2026-11-27T19:50", [A], 1)
    s.state[A] = {"recipes": [R("rcp_01", "Bò kho bánh mì", 4, [("thịt bò", 800, "g")], ["kho"]),
                              R("rcp_02", "Bò kho kiểu Huế", 4, [("thịt bò", 700, "g"), ("sả", 3, "cây")], ["kho", "Huế"])], "saved": []}
    s.say("Lưu cái công thức bò kho kiểu Huế á, không phải cái ăn với bánh mì.",
          C(f"{A}.search", query="bò kho kiểu Huế"),
          C(f"{A}.save", recipe_id="rcp_02"))
    S.append(s)

    # 13. hai món gần giống, user không rõ -> ask recipe_id
    s = Sc(A, "2026-11-27T19:50", [A], 1)
    s.state[A] = {"recipes": [R("rcp_01", "Bò kho bánh mì", 4, [("thịt bò", 800, "g")], ["kho"]),
                              R("rcp_02", "Bò kho kiểu Huế", 4, [("thịt bò", 700, "g"), ("sả", 3, "cây")], ["kho", "Huế"])], "saved": []}
    s.say("Lưu công thức bò kho lại cho anh.",
          C(f"{A}.search", query="bò kho"),
          ASK(f"{A}.save", "recipe_id"))
    S.append(s)

    # 14. get để xem bước, món đã trong history
    s = Sc(A, "2026-11-28T08:40", [A], 2)
    s.state[A] = {"recipes": [R("rcp_01", "Xôi gấc", 6, [("gạo nếp", 1, "kg"), ("gấc", 1, "quả")], ["xôi"], steps=["Ngâm nếp 6 tiếng", "Trộn gấc", "Hấp 40 phút"])], "saved": []}
    s.user("Xôi gấc cần nguyên liệu gì?")
    s.bot("Xôi gấc cho 6 người cần 1 kg gạo nếp và 1 quả gấc ạ.", C(f"{A}.search", query="xôi gấc"))
    s.say("Còn cách làm thì sao, đọc các bước đi.",
          C(f"{A}.get", recipe_id="rcp_01"))
    S.append(s)

    # 15. [] - đã trả lời trong history
    s = Sc(A, "2026-11-28T08:40", [A], 2)
    s.state[A] = {"recipes": [R("rcp_01", "Xôi gấc", 6, [("gạo nếp", 1, "kg"), ("gấc", 1, "quả")], ["xôi"])], "saved": []}
    s.user("Xôi gấc cần nguyên liệu gì?")
    s.bot("Xôi gấc cho 6 người cần 1 kg gạo nếp và 1 quả gấc ạ.", C(f"{A}.search", query="xôi gấc"))
    s.say("Một ký nếp thôi hả, tưởng nhiều hơn chứ.")
    S.append(s)

    # 16. recipes + notes: ghi nguyên liệu vào note
    s = Sc(A, "2026-11-29T15:00", [A, "notes"], 3)
    s.state[A] = {"recipes": [R("rcp_01", "Chè đậu xanh", 4, [("đậu xanh", 200, "g"), ("đường", 150, "g"), ("nước cốt dừa", 100, "ml")], ["chè"])], "saved": []}
    s.state["notes"] = notes()
    s.say("Tìm công thức chè đậu xanh, rồi tạo ghi chú tên 'Đồ nấu chè' ghi là đậu xanh, đường, nước cốt dừa.",
          C(f"{A}.search", query="chè đậu xanh"),
          C("notes.create", title="Đồ nấu chè", content="đậu xanh, đường, nước cốt dừa"))
    S.append(s)

    # 17. tiếng Anh lẫn: "recipe pancake"
    s = Sc(A, "2026-11-30T07:20", [A], 4)
    s.state[A] = {"recipes": [R("rcp_01", "Pancake bơ sữa", 4, [("bột mì", 200, "g"), ("sữa tươi", 300, "ml"), ("trứng", 1, "quả")], ["bữa sáng", "pancake"])], "saved": []}
    s.say("Tìm recipe pancake cho bữa sáng, lưu luôn nha.",
          C(f"{A}.search", query="pancake"),
          C(f"{A}.save", recipe_id="rcp_01"))
    S.append(s)

    # 18. recipes + calendar: lên lịch nấu
    s = Sc(A, "2026-12-01T20:10", [A, "calendar"], 5)
    s.state[A] = {"recipes": [R("rcp_01", "Gà nướng mật ong", 4, [("gà", 1, "con"), ("mật ong", 3, "muỗng")], ["nướng"], time_min=90)], "saved": []}
    s.state["calendar"] = events()
    wd = s.next_wd(6)  # chủ nhật
    s.say(f"Lưu công thức gà nướng mật ong, với tạo lịch 'Nướng gà đãi bạn' lúc năm giờ chiều chủ nhật.",
          C(f"{A}.search", query="gà nướng mật ong"),
          C(f"{A}.save", recipe_id="rcp_01"),
          C("calendar.create_event", title="Nướng gà đãi bạn", start=s.t(wd, 17), end=s.t(wd, 18)))
    S.append(s)

    # 19. read-only với servings "mười người"
    s = Sc(A, "2026-12-02T10:30", [A], 6)
    s.state[A] = {"recipes": [R("rcp_01", "Gỏi cuốn tôm thịt", 4, [("tôm", 200, "g"), ("thịt ba chỉ", 200, "g"), ("bánh tráng", 20, "cái")], ["khai vị"])], "saved": []}
    s.say("Cuối tuần làm gỏi cuốn cho mười người thì cần bao nhiêu tôm với bánh tráng?",
          C(f"{A}.search", query="gỏi cuốn", servings=10))
    S.append(s)

    # 20. [] - không app nào làm được: muốn đặt món ăn giao tận nơi (không cài food_delivery)
    s = Sc(A, "2026-12-02T10:30", [A], 6)
    s.state[A] = {"recipes": [], "saved": []}
    s.say("Lười nấu quá, đặt một phần cơm gà giao tới nhà đi.")
    S.append(s)

    # 21. lưu món đang xem trong history (get)
    s = Sc(A, "2026-12-03T19:00", [A], 7)
    s.state[A] = {"recipes": [R("rcp_01", "Cà ri gà", 4, [("gà", 800, "g"), ("khoai tây", 2, "củ"), ("bột cà ri", 2, "muỗng")], ["cà ri"])], "saved": []}
    s.user("Xem công thức cà ri gà.")
    s.bot("Cà ri gà cho 4 người: 800 g gà, 2 củ khoai tây, 2 muỗng bột cà ri. Các bước: sơ chế, xào, ninh 30 phút.", C(f"{A}.search", query="cà ri gà"), C(f"{A}.get", recipe_id="rcp_01"))
    s.say("Ngon đó, lưu lại dùm.",
          C(f"{A}.save", recipe_id="rcp_01"))
    S.append(s)

    # 22. tìm món chay (tag)
    s = Sc(A, "2026-12-04T11:45", [A], 0)
    s.state[A] = {"recipes": [R("rcp_01", "Đậu hũ sốt cà", 2, [("đậu hũ", 2, "miếng")], ["chay"]),
                              R("rcp_02", "Nấm kho tiêu", 2, [("nấm", 200, "g")], ["chay"]),
                              R("rcp_03", "Thịt kho trứng", 4, [("thịt", 500, "g")], ["mặn"])], "saved": []}
    s.say("Rằm rồi, có món chay nào không em?",
          C(f"{A}.search", query="chay"))
    S.append(s)

    # 23. lưu + nhắn chat gửi tên món cho bạn
    s = Sc(A, "2026-12-05T14:20", [A, "chat_ott"], 1)
    s.state[A] = {"recipes": [R("rcp_01", "Tiramisu không lò nướng", 6, [("bánh ladyfinger", 200, "g"), ("mascarpone", 250, "g")], ["tráng miệng"])], "saved": []}
    s.state["chat_ott"] = chats(("chat_01", "Hương", "direct"), ("chat_02", "Hội bếp", "group"))
    s.say("Lưu công thức tiramisu không lò nướng, rồi nhắn cho Hương là 'tối nay tao làm tiramisu, qua ăn'.",
          C(f"{A}.search", query="tiramisu không lò nướng"),
          C(f"{A}.save", recipe_id="rcp_01"),
          C("chat_ott.list_chats"),
          C("chat_ott.send_message", chat_id="chat_01", content="tối nay tao làm tiramisu, qua ăn"))
    S.append(s)

    # 24. [] - đổi ý
    s = Sc(A, "2026-12-06T09:00", [A], 2)
    s.state[A] = {"recipes": [R("rcp_01", "Bánh mì nướng bơ tỏi", 2, [("bánh mì", 1, "ổ")], [])], "saved": []}
    s.say("Lưu công thức bánh mì bơ tỏi... thôi khỏi, món này dễ mình nhớ rồi.")
    S.append(s)

    # 25. search có servings + save
    s = Sc(A, "2026-12-07T16:30", [A], 3)
    s.state[A] = {"recipes": [R("rcp_01", "Bún riêu cua", 4, [("cua đồng", 500, "g"), ("bún", 1, "kg"), ("cà chua", 4, "quả")], ["bún"])], "saved": []}
    s.say("Coi bún riêu cua nấu cho tám người cần bao nhiêu cua, rồi lưu công thức đó lại.",
          C(f"{A}.search", query="bún riêu cua", servings=8),
          C(f"{A}.save", recipe_id="rcp_01"))
    S.append(s)

    return S
