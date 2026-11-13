from common import *

A = "habit_tracker"


def H(i, name, streak, last, freq="daily"):
    return {"id": i, "name": name, "frequency": freq, "streak": streak, "last_logged": last}


def build():
    S = []

    # 1. tick hôm nay
    s = Sc(A, "2026-11-18T21:30", [A], 0)
    s.state[A] = {"habits": [H("habit_01", "Chạy bộ 30 phút", 5, s.d(-1)), H("habit_02", "Đọc sách 20 trang", 12, s.d(-1))], "logs": []}
    s.say("Nay chạy bộ xong rồi, tick cho anh cái.",
          C(f"{A}.list_habits"),
          C(f"{A}.log", habit_id="habit_01", date=s.d(0)))
    S.append(s)

    # 2. tick hôm qua (quên)
    s = Sc(A, "2026-11-19T08:10", [A], 1)
    s.state[A] = {"habits": [H("habit_01", "Thiền 10 phút", 3, s.d(-2)), H("habit_02", "Uống 2 lít nước", 7, s.d(-1))], "logs": []}
    s.say("Hôm qua chị có thiền mà quên đánh dấu, ghi bù giúp chị nha.",
          C(f"{A}.list_habits"),
          C(f"{A}.log", habit_id="habit_01", date=s.d(-1)))
    S.append(s)

    # 3. hai thói quen cùng lúc
    s = Sc(A, "2026-11-20T22:00", [A], 2)
    s.state[A] = {"habits": [H("habit_01", "Tập gym", 2, s.d(-1)), H("habit_02", "Học tiếng Anh", 20, s.d(-1)), H("habit_03", "Không ăn khuya", 1, s.d(-1))], "logs": []}
    s.say("Hôm nay em đi gym với học tiếng Anh rồi, tick hai cái đó.",
          C(f"{A}.list_habits"),
          C(f"{A}.log", habit_id="habit_01", date=s.d(0)),
          C(f"{A}.log", habit_id="habit_02", date=s.d(0)))
    S.append(s)

    # 4. chỉ hỏi streak (read)
    s = Sc(A, "2026-11-21T07:00", [A], 3)
    s.state[A] = {"habits": [H("habit_01", "Dậy sớm 5h30", 14, s.d(-1))], "logs": []}
    s.say("Chuỗi dậy sớm của tui được mấy ngày rồi?",
          C(f"{A}.list_habits"))
    S.append(s)

    # 5. không rõ thói quen nào -> ask habit_id
    s = Sc(A, "2026-11-22T20:30", [A], 4)
    s.state[A] = {"habits": [H("habit_01", "Đọc sách", 4, s.d(-1)), H("habit_02", "Viết nhật ký", 9, s.d(-1))], "logs": []}
    s.say("Xong rồi, đánh dấu hôm nay giúp mình.",
          C(f"{A}.list_habits"),
          ASK(f"{A}.log", "habit_id"))
    S.append(s)

    # 6. tick "tất cả" hôm nay (3 thói quen)
    s = Sc(A, "2026-11-23T23:10", [A], 5)
    s.state[A] = {"habits": [H("habit_01", "Uống vitamin", 30, s.d(-1)), H("habit_02", "Giãn cơ", 30, s.d(-1)), H("habit_03", "Ngủ trước 11h", 2, s.d(-1))], "logs": []}
    s.say("Hôm nay làm đủ hết các thói quen, tick hết cho tôi.",
          C(f"{A}.list_habits"),
          C(f"{A}.log", habit_id="habit_01", date=s.d(0)),
          C(f"{A}.log", habit_id="habit_02", date=s.d(0)),
          C(f"{A}.log", habit_id="habit_03", date=s.d(0)))
    S.append(s)

    # 7. history đã list; tick một cái không đọc lại
    s = Sc(A, "2026-11-24T21:00", [A], 6)
    s.state[A] = {"habits": [H("habit_01", "Chạy bộ", 6, s.d(-1)), H("habit_02", "Đọc sách", 2, s.d(-3))], "logs": []}
    s.user("Streak mấy thói quen của anh sao rồi?")
    s.bot("Chạy bộ đang chuỗi 6 ngày, Đọc sách chuỗi 2 ngày nhưng 3 ngày rồi chưa ghi ạ.", C(f"{A}.list_habits"))
    s.say("Ờ nay có đọc, tick đọc sách đi.",
          C(f"{A}.log", habit_id="habit_02", date=s.d(0)))
    S.append(s)

    # 8. tick hôm nay + nhắc mai
    s = Sc(A, "2026-11-25T19:40", [A, "reminders"], 7)
    s.state[A] = {"habits": [H("habit_01", "Học piano 20 phút", 11, s.d(-1))], "logs": []}
    s.state["reminders"] = reminders()
    s.say("Tập piano xong rồi, tick, với nhắc em bảy rưỡi tối mai tập tiếp.",
          C(f"{A}.list_habits"),
          C(f"{A}.log", habit_id="habit_01", date=s.d(0)),
          C("reminders.create", content="Tập piano", time=s.t(1, 19, 30)))
    S.append(s)

    # 9. [] - chat
    s = Sc(A, "2026-11-26T06:30", [A], 0)
    s.state[A] = {"habits": [H("habit_01", "Chạy bộ", 0, None)], "logs": []}
    s.say("Lập thói quen khó thật, cứ được ba bữa lại bỏ.")
    S.append(s)

    # 10. tick ngày cụ thể "thứ bảy vừa rồi" -> quá khứ
    s = Sc(A, "2026-11-30T09:15", [A], 1)  # thứ hai
    s.state[A] = {"habits": [H("habit_01", "Bơi", 1, s.d(-4))], "logs": []}
    s.say("Thứ bảy vừa rồi anh có đi bơi, ghi nhận lại nhé.",
          C(f"{A}.list_habits"),
          C(f"{A}.log", habit_id="habit_01", date=s.d(-2)))
    S.append(s)

    # 11. [] - điều kiện sai từ history: đã tick rồi
    s = Sc(A, "2026-11-27T22:30", [A], 2)
    s.state[A] = {"habits": [H("habit_01", "Thiền", 8, s.d(-1))], "logs": []}
    s.user("Thiền xong rồi, tick đi.")
    s.bot("Đã ghi nhận Thiền hôm nay, chuỗi 9 ngày ạ.", C(f"{A}.list_habits"), C(f"{A}.log", habit_id="habit_01", date=s.d(0)))
    s.say("À nếu nãy chưa tick thì tick giùm nha.")
    S.append(s)

    # 12. tick + đánh dấu task xong
    s = Sc(A, "2026-11-28T18:00", [A, "tasks"], 3)
    s.state[A] = {"habits": [H("habit_01", "Học từ vựng tiếng Nhật", 15, s.d(-1))], "logs": []}
    s.state["tasks"] = tasks(("task_01", "Ôn bài N3 chương 5", "", "normal", False))
    s.say("Học xong chương 5 rồi, tick thói quen tiếng Nhật với hoàn thành việc ôn bài N3 luôn.",
          C(f"{A}.list_habits"),
          C(f"{A}.log", habit_id="habit_01", date=s.d(0)),
          C("tasks.list"),
          C("tasks.complete", task_id="task_01"))
    S.append(s)

    # 13. giọng miền Trung
    s = Sc(A, "2026-11-29T21:45", [A], 3)
    s.state[A] = {"habits": [H("habit_01", "Đi bộ 10 nghìn bước", 4, s.d(-1)), H("habit_02", "Không uống trà sữa", 10, s.d(-1))], "logs": []}
    s.say("Bữa ni đi bộ đủ mười nghìn bước rồi đó, tick cho mệ.",
          C(f"{A}.list_habits"),
          C(f"{A}.log", habit_id="habit_01", date=s.d(0)))
    S.append(s)

    # 14. hỏi "hôm nay còn gì chưa làm" -> list
    s = Sc(A, "2026-12-01T20:00", [A], 4)
    s.state[A] = {"habits": [H("habit_01", "Đọc sách", 3, s.d(0)), H("habit_02", "Chạy bộ", 3, s.d(-1))], "logs": []}
    s.say("Hôm nay còn thói quen nào chưa tick không?",
          C(f"{A}.list_habits"))
    S.append(s)

    # 15. history list -> tick cái còn thiếu
    s = Sc(A, "2026-12-01T20:00", [A], 4)
    s.state[A] = {"habits": [H("habit_01", "Đọc sách", 3, s.d(0)), H("habit_02", "Chạy bộ", 3, s.d(-1))], "logs": []}
    s.user("Hôm nay còn thói quen nào chưa tick không?")
    s.bot("Còn Chạy bộ chưa ghi hôm nay ạ, Đọc sách đã tick rồi.", C(f"{A}.list_habits"))
    s.say("À có chạy rồi, tick luôn.",
          C(f"{A}.log", habit_id="habit_02", date=s.d(0)))
    S.append(s)

    # 16. [] - không app nào: muốn tạo thói quen mới (không có tool tạo)
    s = Sc(A, "2026-12-02T08:00", [A], 5)
    s.state[A] = {"habits": [H("habit_01", "Chạy bộ", 3, s.d(-1))], "logs": []}
    s.say("Tạo thêm cho mình thói quen mới là uống đủ hai lít nước mỗi ngày.")
    S.append(s)

    # 17. tick hôm qua và hôm nay
    s = Sc(A, "2026-12-03T22:20", [A], 6)
    s.state[A] = {"habits": [H("habit_01", "Viết blog", 2, s.d(-2))], "logs": []}
    s.say("Hôm qua với hôm nay đều viết blog mà chưa đánh dấu, ghi cả hai ngày nhé.",
          C(f"{A}.list_habits"),
          C(f"{A}.log", habit_id="habit_01", date=s.d(-1)),
          C(f"{A}.log", habit_id="habit_01", date=s.d(0)))
    S.append(s)

    # 18. tiếng Anh lẫn: "check in habit workout"
    s = Sc(A, "2026-12-04T19:30", [A], 7)
    s.state[A] = {"habits": [H("habit_01", "Workout", 21, s.d(-1)), H("habit_02", "Meditation", 5, s.d(-1))], "logs": []}
    s.say("Check in cái habit workout hôm nay giúp em.",
          C(f"{A}.list_habits"),
          C(f"{A}.log", habit_id="habit_01", date=s.d(0)))
    S.append(s)

    # 19. tick + nhắn nhóm khoe streak
    s = Sc(A, "2026-12-05T06:45", [A, "chat_ott"], 0)
    s.state[A] = {"habits": [H("habit_01", "Dậy sớm", 29, s.d(-1))], "logs": []}
    s.state["chat_ott"] = chats(("chat_01", "Hội dậy sớm", "group"))
    s.say("Tick dậy sớm hôm nay, rồi nhắn vào nhóm Hội dậy sớm là 'ngày 30 rồi nha anh em'.",
          C(f"{A}.list_habits"),
          C(f"{A}.log", habit_id="habit_01", date=s.d(0)),
          C("chat_ott.list_chats"),
          C("chat_ott.send_message", chat_id="chat_01", content="ngày 30 rồi nha anh em"))
    S.append(s)

    # 20. [] - huỷ
    s = Sc(A, "2026-12-06T21:00", [A], 1)
    s.state[A] = {"habits": [H("habit_01", "Đọc sách", 4, s.d(-1))], "logs": []}
    s.say("Tick đọc sách... à khoan, nay mới đọc được 5 trang, chưa tính, thôi đừng tick.")
    S.append(s)

    # 21. ngày hôm kia
    s = Sc(A, "2026-12-07T10:00", [A], 2)
    s.state[A] = {"habits": [H("habit_01", "Tập yoga", 1, s.d(-3))], "logs": []}
    s.say("Hôm kia có tập yoga, quên ghi, bổ sung giúp chị.",
          C(f"{A}.list_habits"),
          C(f"{A}.log", habit_id="habit_01", date=s.d(-2)))
    S.append(s)

    return S
