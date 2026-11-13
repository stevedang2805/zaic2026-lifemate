from common import *

A = "pantry"


def I(i, name, stock, unit):
    return {"id": i, "name": name, "stock": stock, "unit": unit}


def build():
    S = []

    # 1. dùng 2 quả trứng
    s = Sc(A, "2026-11-18T07:10", [A], 0)
    s.state[A] = {"items": [I("item_01", "trứng gà", 8, "quả"), I("item_02", "sữa tươi", 2, "hộp"), I("item_03", "gạo", 5, "kg")]}
    s.say("Sáng nay em lấy hai quả trứng chiên rồi, trừ trong tủ bếp giúp em.",
          C(f"{A}.list_items"),
          C(f"{A}.consume", item_id="item_01", quantity=2))
    S.append(s)

    # 2. dùng hết -> quantity = stock
    s = Sc(A, "2026-11-19T19:00", [A], 1)
    s.state[A] = {"items": [I("item_01", "mì gói", 3, "gói"), I("item_02", "dầu ăn", 1, "chai")]}
    s.say("Tối nay nấu hết chỗ mì gói còn lại rồi, cập nhật tủ bếp đi.",
          C(f"{A}.list_items"),
          C(f"{A}.consume", item_id="item_01", quantity=3))
    S.append(s)

    # 3. hai món một lúc
    s = Sc(A, "2026-11-20T12:30", [A], 2)
    s.state[A] = {"items": [I("item_01", "cà chua", 6, "quả"), I("item_02", "hành tây", 3, "củ"), I("item_03", "thịt bò", 500, "g")]}
    s.say("Vừa nấu xong, dùng ba quả cà chua với một củ hành tây, ghi nhận lại nhé.",
          C(f"{A}.list_items"),
          C(f"{A}.consume", item_id="item_01", quantity=3),
          C(f"{A}.consume", item_id="item_02", quantity=1))
    S.append(s)

    # 4. số lượng theo gram
    s = Sc(A, "2026-11-21T18:45", [A], 3)
    s.state[A] = {"items": [I("item_01", "thịt heo xay", 800, "g"), I("item_02", "bún khô", 1000, "g")]}
    s.say("Lấy ba trăm gam thịt heo xay làm chả rồi, trừ đi.",
          C(f"{A}.list_items"),
          C(f"{A}.consume", item_id="item_01", quantity=300))
    S.append(s)

    # 5. chỉ hỏi còn gì (read)
    s = Sc(A, "2026-11-22T09:00", [A], 4)
    s.state[A] = {"items": [I("item_01", "gạo", 2, "kg"), I("item_02", "nước mắm", 1, "chai"), I("item_03", "đường", 0, "kg")]}
    s.say("Trong bếp còn những gì rồi, đọc chị nghe coi.",
          C(f"{A}.list_items"))
    S.append(s)

    # 6. thiếu số lượng -> ask quantity
    s = Sc(A, "2026-11-23T20:10", [A], 5)
    s.state[A] = {"items": [I("item_01", "bột mì", 2000, "g"), I("item_02", "đường", 1000, "g")]}
    s.say("Hồi chiều làm bánh có dùng bột mì, em trừ bớt trong tủ bếp giúp anh.",
          C(f"{A}.list_items"),
          ASK(f"{A}.consume", "quantity"))
    S.append(s)

    # 7. không đủ -> không consume (báo lại) - chỉ list
    s = Sc(A, "2026-11-24T17:30", [A], 6)
    s.state[A] = {"items": [I("item_01", "trứng gà", 2, "quả")]}
    s.say("Trừ bốn quả trứng trong tủ bếp nha, nãy làm bánh flan.",
          C(f"{A}.list_items"))
    S.append(s)

    # 8. history đã list, lượt sau consume không đọc lại
    s = Sc(A, "2026-11-25T11:20", [A], 7)
    s.state[A] = {"items": [I("item_01", "cá hộp", 4, "hộp"), I("item_02", "bánh mì", 2, "ổ")]}
    s.user("Bếp còn gì ăn trưa không?")
    s.bot("Tủ bếp còn 4 hộp cá hộp và 2 ổ bánh mì ạ.", C(f"{A}.list_items"))
    s.say("Vậy ăn một hộp cá với một ổ bánh mì, trừ luôn giúp mình.",
          C(f"{A}.consume", item_id="item_01", quantity=1),
          C(f"{A}.consume", item_id="item_02", quantity=1))
    S.append(s)

    # 9. pantry + grocery: hết thì mua
    s = Sc(A, "2026-11-26T08:15", [A, "grocery"], 0)
    s.state[A] = {"items": [I("item_01", "sữa tươi", 0, "hộp"), I("item_02", "trứng gà", 5, "quả")]}
    s.state["grocery"] = {"products": [{"id": "prod_01", "name": "Sữa tươi Vinamilk 1L", "price": 34000, "unit": "hộp", "category": "sữa", "in_stock": True}], "cart": [], "orders": []}
    s.say("Coi tủ bếp còn sữa tươi không, hết rồi thì đặt bốn hộp trên app đi chợ giao về nhà.",
          C(f"{A}.list_items"),
          C("grocery.search", query="sữa tươi"),
          C("grocery.add_to_cart", product_id="prod_01", quantity=4),
          C("grocery.checkout", address=s.prof["home_address"]))
    S.append(s)

    # 10. pantry + grocery: còn -> không mua
    s = Sc(A, "2026-11-26T08:15", [A, "grocery"], 0)
    s.state[A] = {"items": [I("item_01", "sữa tươi", 3, "hộp"), I("item_02", "trứng gà", 5, "quả")]}
    s.state["grocery"] = {"products": [{"id": "prod_01", "name": "Sữa tươi Vinamilk 1L", "price": 34000, "unit": "hộp", "category": "sữa", "in_stock": True}], "cart": [], "orders": []}
    s.say("Coi tủ bếp còn sữa tươi không, hết rồi thì đặt bốn hộp trên app đi chợ giao về nhà.",
          C(f"{A}.list_items"))
    S.append(s)

    # 11. pantry + shopping_list: cái nào sắp hết thì thêm vào danh sách đi chợ
    s = Sc(A, "2026-11-27T21:00", [A, "shopping_list"], 1)
    s.state[A] = {"items": [I("item_01", "nước mắm", 0, "chai"), I("item_02", "gạo", 10, "kg"), I("item_03", "dầu ăn", 0, "chai")]}
    s.state["shopping_list"] = shopping()
    s.say("Xem trong bếp món nào hết sạch rồi thì thêm vào danh sách đi chợ giúp em.",
          C(f"{A}.list_items"),
          C("shopping_list.add", name="nước mắm"),
          C("shopping_list.add", name="dầu ăn"))
    S.append(s)

    # 12. [] - chat
    s = Sc(A, "2026-11-28T13:00", [A], 2)
    s.state[A] = {"items": [I("item_01", "gạo", 3, "kg")]}
    s.say("Nhà mình ăn gạo nhanh thật, mới mua tuần trước mà.")
    S.append(s)

    # 13. [] - huỷ
    s = Sc(A, "2026-11-28T13:00", [A], 2)
    s.state[A] = {"items": [I("item_01", "gạo", 3, "kg")]}
    s.say("Trừ một ký gạo... ờ mà thôi khỏi, tí mình tự cân lại rồi ghi.")
    S.append(s)

    # 14. tên gần giống: "sữa đặc" vs "sữa tươi"
    s = Sc(A, "2026-11-29T07:30", [A], 3)
    s.state[A] = {"items": [I("item_01", "sữa tươi", 4, "hộp"), I("item_02", "sữa đặc", 2, "lon")]}
    s.say("Pha cà phê hết một lon sữa đặc rồi, trừ đi nghen.",
          C(f"{A}.list_items"),
          C(f"{A}.consume", item_id="item_02", quantity=1))
    S.append(s)

    # 15. nhiều món + nhắc mua lại
    s = Sc(A, "2026-11-30T19:40", [A, "reminders"], 4)
    s.state[A] = {"items": [I("item_01", "dầu ăn", 1, "chai"), I("item_02", "muối", 1, "gói")]}
    s.state["reminders"] = reminders()
    s.say("Dùng hết chai dầu ăn cuối rồi, trừ đi và nhắc tôi tám giờ sáng mai mua dầu ăn.",
          C(f"{A}.list_items"),
          C(f"{A}.consume", item_id="item_01", quantity=1),
          C("reminders.create", content="Mua dầu ăn", time=s.t(1, 8)))
    S.append(s)

    # 16. pantry + recipes: nấu món theo công thức, trừ nguyên liệu đã dùng (số nói rõ)
    s = Sc(A, "2026-12-01T18:20", [A, "recipes"], 5)
    s.state[A] = {"items": [I("item_01", "trứng gà", 10, "quả"), I("item_02", "cà chua", 5, "quả")]}
    s.state["recipes"] = {"recipes": [{"id": "rcp_01", "name": "Trứng chiên cà chua", "servings": 2, "tags": ["nhanh"],
                                       "ingredients": [{"name": "trứng gà", "quantity": 3, "unit": "quả"}, {"name": "cà chua", "quantity": 2, "unit": "quả"}],
                                       "steps": ["Đánh trứng", "Xào cà chua", "Đổ trứng"]}], "saved": []}
    s.say("Vừa làm món trứng chiên cà chua xong, ba quả trứng hai quả cà chua, trừ khỏi tủ bếp giúp chị.",
          C(f"{A}.list_items"),
          C(f"{A}.consume", item_id="item_01", quantity=3),
          C(f"{A}.consume", item_id="item_02", quantity=2))
    S.append(s)

    # 17. không rõ món nào: "lấy hai hộp sữa" mà có 2 loại sữa hộp -> ask item_id
    s = Sc(A, "2026-12-02T08:05", [A], 6)
    s.state[A] = {"items": [I("item_01", "sữa tươi", 6, "hộp"), I("item_02", "sữa hạt óc chó", 4, "hộp")]}
    s.say("Hai đứa nhỏ uống hai hộp sữa rồi, trừ đi.",
          C(f"{A}.list_items"),
          ASK(f"{A}.consume", "item_id"))
    S.append(s)

    # 18. read: còn bao nhiêu trứng
    s = Sc(A, "2026-12-03T06:50", [A], 7)
    s.state[A] = {"items": [I("item_01", "trứng gà", 7, "quả")]}
    s.say("Còn mấy quả trứng trong bếp vậy?",
          C(f"{A}.list_items"))
    S.append(s)

    # 19. history: đã hỏi còn gì; lượt sau yêu cầu trừ 1 món có trong kết quả
    s = Sc(A, "2026-12-04T12:10", [A], 0)
    s.state[A] = {"items": [I("item_01", "bánh tráng", 2, "xấp"), I("item_02", "xúc xích", 6, "cây")]}
    s.user("Trong bếp còn gì ăn vặt?")
    s.bot("Còn 2 xấp bánh tráng và 6 cây xúc xích ạ.", C(f"{A}.list_items"))
    s.say("Ăn hai cây xúc xích thôi, trừ đi.",
          C(f"{A}.consume", item_id="item_02", quantity=2))
    S.append(s)

    # 20. [] - đã trả lời
    s = Sc(A, "2026-12-04T12:10", [A], 0)
    s.state[A] = {"items": [I("item_01", "bánh tráng", 2, "xấp"), I("item_02", "xúc xích", 6, "cây")]}
    s.user("Trong bếp còn gì ăn vặt?")
    s.bot("Còn 2 xấp bánh tráng và 6 cây xúc xích ạ.", C(f"{A}.list_items"))
    s.say("Xúc xích còn sáu cây lận hả? Nhiều ha.")
    S.append(s)

    # 21. đơn vị ký: "nửa ký" với stock theo g -> 500
    s = Sc(A, "2026-12-05T17:00", [A], 1)
    s.state[A] = {"items": [I("item_01", "thịt bò", 1200, "g")]}
    s.say("Nay nấu phở dùng nửa ký thịt bò, cập nhật tủ bếp.",
          C(f"{A}.list_items"),
          C(f"{A}.consume", item_id="item_01", quantity=500))
    S.append(s)

    # 22. giọng Nam, hai món
    s = Sc(A, "2026-12-06T19:15", [A], 2)
    s.state[A] = {"items": [I("item_01", "tôm khô", 300, "g"), I("item_02", "củ kiệu", 2, "hũ"), I("item_03", "nước tương", 1, "chai")]}
    s.say("Hồi trưa lấy một trăm gam tôm khô với một hũ củ kiệu ăn rồi đó, trừ dùm.",
          C(f"{A}.list_items"),
          C(f"{A}.consume", item_id="item_01", quantity=100),
          C(f"{A}.consume", item_id="item_02", quantity=1))
    S.append(s)

    # 23. [] - không app nào làm được: muốn đặt giao gạo nhưng chỉ cài pantry
    s = Sc(A, "2026-12-07T09:30", [A], 3)
    s.state[A] = {"items": [I("item_01", "gạo", 1, "kg")]}
    s.say("Gạo sắp hết, đặt giao mười ký gạo ST25 về nhà đi.")
    S.append(s)

    # 24. pantry + notes: ghi chú món sắp hết
    s = Sc(A, "2026-12-08T21:40", [A, "notes"], 4)
    s.state[A] = {"items": [I("item_01", "cà phê", 1, "gói"), I("item_02", "đường", 2, "kg")]}
    s.state["notes"] = notes()
    s.say("Lấy gói cà phê cuối cùng ra pha rồi, trừ đi và ghi chú lại là cần mua cà phê.",
          C(f"{A}.list_items"),
          C(f"{A}.consume", item_id="item_01", quantity=1),
          C("notes.create", content="Cần mua cà phê"))
    S.append(s)

    return S
