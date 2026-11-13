from common import *

A = "translator"


def D(*rows):
    """rows: (text, to_lang, translation)"""
    return {"dictionary": [{"text": t, "to_lang": l, "translation": tr} for t, l, tr in rows]}


def build():
    S = []

    # 1. dịch sang tiếng Anh
    s = Sc(A, "2026-11-18T09:00", [A], 0)
    s.state[A] = D(("Tôi muốn đặt bàn cho hai người lúc bảy giờ tối", "en", "I'd like to book a table for two at 7 pm"))
    s.say("Dịch sang tiếng Anh giúp em câu: tôi muốn đặt bàn cho hai người lúc bảy giờ tối.",
          C(f"{A}.translate", text="Tôi muốn đặt bàn cho hai người lúc bảy giờ tối", to_lang="en"))
    S.append(s)

    # 2. dịch sang tiếng Nhật
    s = Sc(A, "2026-11-19T15:30", [A], 1)
    s.state[A] = D(("Cảm ơn anh đã giúp đỡ", "ja", "手伝ってくれてありがとうございます"))
    s.say("Câu 'cảm ơn anh đã giúp đỡ' tiếng Nhật nói sao?",
          C(f"{A}.translate", text="Cảm ơn anh đã giúp đỡ", to_lang="ja"))
    S.append(s)

    # 3. dịch + gửi SMS cho số điện thoại
    s = Sc(A, "2026-11-20T11:10", [A, "sms", "contacts"], 2)
    s.state[A] = D(("Tôi sẽ đến trễ 15 phút", "en", "I will be 15 minutes late"))
    s.state["contacts"] = contacts(("c_01", "John", "khách hàng", "0901234567"), ("c_02", "Mẹ", "mẹ", "0912000111"))
    s.state["sms"] = {"messages": []}
    s.say("Dịch 'tôi sẽ đến trễ 15 phút' sang tiếng Anh rồi nhắn tin cho John.",
          C(f"{A}.translate", text="Tôi sẽ đến trễ 15 phút", to_lang="en"),
          C("contacts.search", query="John"),
          C("sms.send", contact_id="c_01", content="I will be 15 minutes late"))
    S.append(s)

    # 4. thiếu ngôn ngữ đích -> ask to_lang
    s = Sc(A, "2026-11-21T08:45", [A], 3)
    s.state[A] = D()
    s.say("Dịch giúp tôi câu 'xin lỗi, tôi không hiểu'.",
          ASK(f"{A}.translate", "to_lang"))
    S.append(s)

    # 5. dịch tiếng Anh sang tiếng Việt (to_lang vi)
    s = Sc(A, "2026-11-22T20:00", [A], 4)
    s.state[A] = D(("Could you please send me the invoice by Friday", "vi", "Bạn có thể gửi hóa đơn cho tôi trước thứ Sáu được không"))
    s.say("Could you please send me the invoice by Friday, câu này nghĩa là gì vậy?",
          C(f"{A}.translate", text="Could you please send me the invoice by Friday", to_lang="vi"))
    S.append(s)

    # 6. dịch sang tiếng Hàn + lưu note
    s = Sc(A, "2026-11-23T13:20", [A, "notes"], 5)
    s.state[A] = D(("Nhà vệ sinh ở đâu", "ko", "화장실이 어디예요"))
    s.state["notes"] = notes()
    s.say("Dịch 'nhà vệ sinh ở đâu' sang tiếng Hàn rồi ghi chú lại cho tôi.",
          C(f"{A}.translate", text="Nhà vệ sinh ở đâu", to_lang="ko"),
          C("notes.create", content="Nhà vệ sinh ở đâu: 화장실이 어디예요"))
    S.append(s)

    # 7. dịch + gửi chat
    s = Sc(A, "2026-11-24T17:00", [A, "chat_ott"], 6)
    s.state[A] = D(("Chúc mừng sinh nhật, chúc bạn mọi điều tốt đẹp", "en", "Happy birthday, wishing you all the best"))
    s.state["chat_ott"] = chats(("chat_01", "Anna", "direct"), ("chat_02", "Family", "group"))
    s.say("Dịch sang tiếng Anh câu 'chúc mừng sinh nhật, chúc bạn mọi điều tốt đẹp' rồi gửi cho Anna qua chat.",
          C(f"{A}.translate", text="Chúc mừng sinh nhật, chúc bạn mọi điều tốt đẹp", to_lang="en"),
          C("chat_ott.list_chats"),
          C("chat_ott.send_message", chat_id="chat_01", content="Happy birthday, wishing you all the best"))
    S.append(s)

    # 8. [] - chat
    s = Sc(A, "2026-11-25T10:00", [A], 7)
    s.state[A] = D()
    s.say("Tiếng Anh của mình dạo này xuống dốc quá, nói chuyện với khách cứ ấp úng.")
    S.append(s)

    # 9. dịch sang tiếng Trung
    s = Sc(A, "2026-11-26T09:30", [A], 0)
    s.state[A] = D(("Cái này giá bao nhiêu", "zh", "这个多少钱"))
    s.say("'Cái này giá bao nhiêu' tiếng Trung nói thế nào?",
          C(f"{A}.translate", text="Cái này giá bao nhiêu", to_lang="zh"))
    S.append(s)

    # 10. dịch sang tiếng Pháp
    s = Sc(A, "2026-11-27T14:15", [A], 1)
    s.state[A] = D(("Tôi bị dị ứng hải sản", "fr", "Je suis allergique aux fruits de mer"))
    s.say("Dịch qua tiếng Pháp: tôi bị dị ứng hải sản.",
          C(f"{A}.translate", text="Tôi bị dị ứng hải sản", to_lang="fr"))
    S.append(s)

    # 11. history đã dịch; lượt sau nhắn câu đó cho người (không dịch lại)
    s = Sc(A, "2026-11-28T16:40", [A, "chat_ott"], 2)
    s.state[A] = D(("Hẹn gặp lại bạn vào tuần sau", "en", "See you next week"))
    s.state["chat_ott"] = chats(("chat_01", "David", "direct"))
    s.user("'Hẹn gặp lại bạn vào tuần sau' tiếng Anh là gì?")
    s.bot("Là 'See you next week' ạ.", C(f"{A}.translate", text="Hẹn gặp lại bạn vào tuần sau", to_lang="en"))
    s.say("Gửi câu đó cho David đi.",
          C("chat_ott.list_chats"),
          C("chat_ott.send_message", chat_id="chat_01", content="See you next week"))
    S.append(s)

    # 12. [] - đã trả lời
    s = Sc(A, "2026-11-28T16:40", [A], 2)
    s.state[A] = D(("Hẹn gặp lại bạn vào tuần sau", "en", "See you next week"))
    s.user("'Hẹn gặp lại bạn vào tuần sau' tiếng Anh là gì?")
    s.bot("Là 'See you next week' ạ.", C(f"{A}.translate", text="Hẹn gặp lại bạn vào tuần sau", to_lang="en"))
    s.say("À đơn giản vậy thôi hả.")
    S.append(s)

    # 13. dịch nhiều câu? dịch 2 câu riêng
    s = Sc(A, "2026-11-29T08:00", [A], 3)
    s.state[A] = D(("Xin chào", "th", "สวัสดี"), ("Cảm ơn", "th", "ขอบคุณ"))
    s.say("Sắp đi Thái, dịch giúp tôi 'xin chào' với 'cảm ơn' sang tiếng Thái.",
          C(f"{A}.translate", text="Xin chào", to_lang="th"),
          C(f"{A}.translate", text="Cảm ơn", to_lang="th"))
    S.append(s)

    # 14. dịch + sms theo số đọc
    s = Sc(A, "2026-11-30T19:25", [A, "sms"], 4)
    s.state[A] = D(("Phòng của bạn đã sẵn sàng, vui lòng nhận phòng tại quầy lễ tân", "en", "Your room is ready, please check in at the reception"))
    s.state["sms"] = {"messages": []}
    s.say("Dịch sang tiếng Anh 'phòng của bạn đã sẵn sàng, vui lòng nhận phòng tại quầy lễ tân' rồi nhắn tới số không chín không tám, một hai ba, bốn năm sáu.",
          C(f"{A}.translate", text="Phòng của bạn đã sẵn sàng, vui lòng nhận phòng tại quầy lễ tân", to_lang="en"),
          C("sms.send", phone_number="0908123456", content="Your room is ready, please check in at the reception"))
    S.append(s)

    # 15. dịch sang tiếng Đức
    s = Sc(A, "2026-12-01T12:00", [A], 5)
    s.state[A] = D(("Tôi đến từ Việt Nam", "de", "Ich komme aus Vietnam"))
    s.say("Tiếng Đức 'tôi đến từ Việt Nam' nói sao em?",
          C(f"{A}.translate", text="Tôi đến từ Việt Nam", to_lang="de"))
    S.append(s)

    # 16. [] - không app nào làm được: muốn phiên dịch trực tiếp cuộc gọi
    s = Sc(A, "2026-12-01T12:00", [A], 5)
    s.state[A] = D()
    s.say("Gọi cho khách sạn bên Đức rồi phiên dịch trực tiếp giúp tôi nhé.")
    S.append(s)

    # 17. tiếng Nhật sang Việt
    s = Sc(A, "2026-12-02T21:30", [A], 6)
    s.state[A] = D(("お疲れ様でした", "vi", "Bạn đã vất vả rồi"))
    s.say("Sếp nhắn otsukaresama deshita, dịch ra tiếng Việt là gì vậy?",
          C(f"{A}.translate", text="otsukaresama deshita", to_lang="vi"))
    S.append(s)

    # 18. dịch + ghi vào note có sẵn (append)
    s = Sc(A, "2026-12-03T10:10", [A, "notes"], 7)
    s.state[A] = D(("Làm ơn cho tôi hóa đơn", "en", "Please give me the bill"))
    s.state["notes"] = notes(("note_01", "Câu tiếng Anh đi du lịch", "Where is the station: Nhà ga ở đâu"))
    s.say("Dịch 'làm ơn cho tôi hóa đơn' sang tiếng Anh rồi thêm vào ghi chú câu tiếng Anh đi du lịch.",
          C(f"{A}.translate", text="Làm ơn cho tôi hóa đơn", to_lang="en"),
          C("notes.list"),
          C("notes.append", note_id="note_01", content="Please give me the bill: Làm ơn cho tôi hóa đơn"))
    S.append(s)

    # 19. [] - huỷ
    s = Sc(A, "2026-12-04T09:00", [A], 0)
    s.state[A] = D()
    s.say("Dịch câu này sang tiếng Anh... thôi khỏi, em tự tra từ điển.")
    S.append(s)

    # 20. dịch sang tiếng Anh với giọng Nam
    s = Sc(A, "2026-12-05T15:45", [A], 1)
    s.state[A] = D(("Cho tôi hỏi đường ra bến xe", "en", "Could you tell me the way to the bus station"))
    s.say("Dịch dùm tui 'cho tôi hỏi đường ra bến xe' qua tiếng Anh.",
          C(f"{A}.translate", text="Cho tôi hỏi đường ra bến xe", to_lang="en"))
    S.append(s)

    # 21. dịch rồi gửi email (to đọc)
    s = Sc(A, "2026-12-06T08:30", [A, "email"], 2)
    s.state[A] = D(("Chúng tôi xác nhận đơn hàng của bạn sẽ được giao vào thứ Hai", "en", "We confirm that your order will be delivered on Monday"))
    s.state["email"] = {"emails": [], "sent": [], "drafts": []}
    s.say("Dịch sang tiếng Anh 'chúng tôi xác nhận đơn hàng của bạn sẽ được giao vào thứ Hai', rồi gửi email tới mark@example.test, tiêu đề Order confirmation.",
          C(f"{A}.translate", text="Chúng tôi xác nhận đơn hàng của bạn sẽ được giao vào thứ Hai", to_lang="en"),
          C("email.send", to=["mark@example.test"], subject="Order confirmation", body="We confirm that your order will be delivered on Monday"))
    S.append(s)

    # 22. dịch sang tiếng Anh, nguồn nói rõ là tiếng Việt -> from_lang? Chỉ truyền khi nói rõ -> ở đây có nói "từ tiếng Việt"
    s = Sc(A, "2026-12-07T11:00", [A], 3)
    s.state[A] = D(("Hôm nay trời đẹp quá", "en", "The weather is so nice today"))
    s.say("Dịch từ tiếng Việt sang tiếng Anh: hôm nay trời đẹp quá.",
          C(f"{A}.translate", text="Hôm nay trời đẹp quá", to_lang="en", from_lang="vi"))
    S.append(s)

    return S
