"""Programmatic synthetic specs for the 11 apps that appear only in public test (no train samples).

python -m lifemate.synth_gen --out synth_specs --n 40 --seed 0
python -m lifemate.synth_build --root DATA --tools-from public_test --specs "synth_specs/gen_*.jsonl"

Every spec is built from a randomised state, a spoken-style Vietnamese request and a gold call list computed from that
state with the conventions measured on train (README): read before using an ID, list reads with {}, no re-read of a
fresh history result, resolve IDs first then ask for the one missing value, optional args only when said, [] for
chit-chat / cancelled / impossible requests / conditions known to be false. synth_build then replays every gold list on
the organisers' simulator and rejects anything that fails.

Uses only the public catalog and the zaic_tools source (never public_test.jsonl or public_test_environment/).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
from pathlib import Path

R = random.Random(0)
WD = ["thứ hai", "thứ ba", "thứ tư", "thứ năm", "thứ sáu", "thứ bảy", "chủ nhật"]
DIG = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
TZ = "+07:00"


# ----------------------------------------------------------------------------------------------- spoken numbers / time
def vi_small(n: int) -> str:
    if n < 10:
        return DIG[n]
    if n < 20:
        u = n % 10
        return "mười" + ("" if u == 0 else " " + ("lăm" if u == 5 else DIG[u]))
    if n < 100:
        t, u = divmod(n, 10)
        s = DIG[t] + " mươi"
        if u == 0:
            return s
        return s + " " + {1: "mốt", 5: "lăm", 4: R.choice(["tư", "bốn"])}.get(u, DIG[u])
    h, r = divmod(n, 100)
    s = DIG[h] + " trăm"
    if r == 0:
        return s
    if r < 10:
        return s + " lẻ " + DIG[r]
    return s + " " + vi_small(r)


def qty_phrase(n: int) -> str:
    return vi_small(n) if (n <= 20 and R.random() < 0.7) else str(n)


def money_phrase(n: int) -> str:
    """n in VND; n is a multiple of 1000 (< 1M) or of 100k (>= 1M)."""
    if n >= 1_000_000:
        m, r = divmod(n, 1_000_000)
        k = r // 100_000
        opts = [f"{m} triệu" + (f" {k}" if k else ""), vi_small(m) + " triệu" + (" " + DIG[k] if k else "")]
        if k == 5:
            opts += [vi_small(m) + " triệu rưỡi", f"{m} triệu rưỡi"]
        if k:
            opts.append(vi_small(m) + " triệu " + vi_small(k) + " trăm nghìn")
        return R.choice(opts)
    th = n // 1000
    opts = [vi_small(th) + " nghìn", f"{th} nghìn", f"{th}k", vi_small(th) + R.choice([" ngàn", " nghìn"])]
    if th % 100 == 50 and th >= 150:
        opts.append(DIG[th // 100] + " trăm rưỡi" if th >= 200 else "trăm rưỡi")
    return R.choice(opts)


def price_phrase(n: int) -> str:
    """stock price, multiple of 100 VND, e.g. 98500 -> 'chín mươi tám nghìn rưỡi' / '98 nghìn 5' / '98.500'."""
    th, r = divmod(n, 1000)
    h = r // 100
    opts: list[str] = []
    if h == 0:
        opts += [vi_small(th) + " nghìn", f"{th} nghìn"]
    else:
        opts += [f"{th} nghìn {h}", vi_small(th) + " nghìn " + DIG[h]]
        if h == 5:
            opts += [vi_small(th) + " nghìn rưỡi", f"{th} nghìn rưỡi"]
    opts.append(f"{th}.{r:03d} đồng")
    return R.choice(opts)


def part_of_day(h: int) -> str:
    return "sáng" if h < 11 else ("trưa" if h < 13 else ("chiều" if h < 18 else "tối"))


def time_phrase(h: int, m: int) -> str:
    h12 = h if h <= 12 else h - 12
    hw = vi_small(h12) if R.random() < 0.6 else str(h12)
    if m == 0:
        core = f"{hw} giờ"
    elif m == 30:
        core = f"{hw} giờ rưỡi" if R.random() < 0.7 else f"{hw} giờ ba mươi"
    elif m in (45, 50) and R.random() < 0.5:
        nh = (h + 1) if h < 23 else 0
        nh12 = nh if nh <= 12 else nh - 12
        core = f"{vi_small(nh12)} giờ kém {vi_small(60 - m)}"
        return f"{core} {part_of_day(nh)}"
    else:
        core = f"{hw} giờ {vi_small(m) if R.random() < 0.6 else m}"
    return f"{core} {part_of_day(h)}"


def iso(d: dt.date, h: int, m: int) -> str:
    return f"{d.isoformat()}T{h:02d}:{m:02d}:00{TZ}"


def date_phrase(now: dt.datetime, allow_today=True) -> tuple[str, dt.date]:
    d0 = now.date()
    kinds = (["today"] if allow_today else []) + ["tomorrow", "after", "weekday", "nextweek", "dom"]
    k = R.choice(kinds)
    if k == "today":
        return R.choice(["hôm nay", "nay", "bữa nay"]), d0
    if k == "tomorrow":
        return R.choice(["mai", "ngày mai", "sáng mai" if False else "mai"]), d0 + dt.timedelta(days=1)
    if k == "after":
        return R.choice(["ngày kia", "ngày mốt", "mốt"]), d0 + dt.timedelta(days=2)
    if k == "weekday":
        off = R.randint(2, 6)
        d = d0 + dt.timedelta(days=off)
        return WD[d.weekday()] + R.choice(["", " này"]) if (d - (d0 - dt.timedelta(days=d0.weekday()))).days < 7 else WD[d.weekday()], d
    if k == "nextweek":
        mon = d0 - dt.timedelta(days=d0.weekday()) + dt.timedelta(days=7)
        i = R.randint(0, 6)
        return f"{WD[i]} tuần sau" if R.random() < 0.7 else f"{WD[i]} tuần tới", mon + dt.timedelta(days=i)
    off = R.randint(3, 20)
    d = d0 + dt.timedelta(days=off)
    return (f"ngày {d.day}" if d.month == d0.month else f"ngày {d.day} tháng {d.month}"), d


PARTICLES = ("nha", "nhé", "nghen", "giùm", "giúp", "với", "đi", "luôn", "hỉ", "thôi", "mình", "em", "không")


def style(text: str) -> str:
    """Spoken-style wrapper: optional opener, optional sentence-final particle (never stacked), ASR-like casing."""
    q = text.endswith("?")
    body = text.rstrip(".?!")
    opener = R.choice(["", "", "", "", "ờ ", "ê ", "trợ lý ơi, ", "em ơi, ", "à ", "ừm ", "này, "])
    if opener and body[:1].isupper() and not body.split()[0][1:].isupper():  # keep acronyms / proper nouns like "FPT"
        first = body.split()[0]
        if first.lower() in {"đặt", "mua", "huỷ", "hủy", "tìm", "lấy", "thêm", "bỏ", "đi", "nạp", "giữ", "dịch", "lưu", "chỉ", "xem",
                             "coi", "ghi", "trừ", "đánh", "báo", "bán", "nấu", "gửi", "kết", "mình", "tủ", "hôm", "chuỗi", "sắp", "đơn",
                             "nếu", "danh", "giá", "mã", "từ", "chuyến", "gần", "ok", "ừ", "vậy", "thôi", "tạo", "xoá", "trả", "gọi",
                             "rút", "mở", "đổi", "chat", "phiên", "bật", "cảm", "chúc", "nhà", "món", "hẹn", "tôi", "ngày", "mai", "tổng",
                             "kiểm", "thứ", "nấu", "uống", "dạo", "có", "trên", "ờ", "à"}:
            body = body[0].lower() + body[1:]
    last = body.split()[-1].lower() if body.split() else ""
    ending = "" if last in PARTICLES else R.choice(["", "", "", " nha", " nhé", " nghen", " giùm mình", " với", " hỉ"])
    out = opener + body + ending
    out = out[0].upper() + out[1:]
    return out + ("?" if q else R.choice([".", ".", ""]))


def vnd(n: int) -> str:
    return f"{n:,}".replace(",", ".") + "đ"


def rid(prefix: str) -> str:
    return f"{prefix}_{R.randint(100, 9999)}"


# ----------------------------------------------------------------------------------------------- context & shared apps
CITIES = {
    "Hà Nội": dict(lat=21.0285, lng=105.8542, homes=["25 Láng Hạ, Đống Đa, Hà Nội", "18 Hoàng Quốc Việt, Cầu Giấy, Hà Nội", "56 Kim Mã, Ba Đình, Hà Nội"],
                   works=["Toà nhà Keangnam, Nam Từ Liêm, Hà Nội", "35 Hai Bà Trưng, Hoàn Kiếm, Hà Nội"]),
    "TP.HCM": dict(lat=10.7769, lng=106.7009, homes=["123 Trần Hưng Đạo, Quận 5, TP.HCM", "45 Nguyễn Thị Minh Khai, Quận 3, TP.HCM", "88 Phan Xích Long, Phú Nhuận, TP.HCM"],
                   works=["227 Nguyễn Văn Cừ, Quận 5, TP.HCM", "Bitexco, 2 Hải Triều, Quận 1, TP.HCM"]),
    "Đà Nẵng": dict(lat=16.0544, lng=108.2022, homes=["12 Lê Duẩn, Hải Châu, Đà Nẵng", "40 Võ Văn Kiệt, Sơn Trà, Đà Nẵng"],
                    works=["Công viên phần mềm, Hải Châu, Đà Nẵng"]),
    "Huế": dict(lat=16.4637, lng=107.5909, homes=["20 Lê Lợi, TP Huế", "8 Nguyễn Huệ, TP Huế"], works=["Bệnh viện Trung ương Huế, 16 Lê Lợi, TP Huế"]),
}
NAMES = ["Minh Anh", "Quốc Bảo", "Thu Hà", "Văn Hùng", "Ngọc Lan", "Đức Thịnh", "Phương Thảo", "Hoàng Nam", "Bảo Châu", "Thanh Tùng"]
PEOPLE = [("Minh", "bạn"), ("Lan", "vợ"), ("Tuấn", "anh trai"), ("Hương", "bạn"), ("Sếp Dũng", "sếp"), ("Mẹ", "mẹ"), ("Bố", "bố"),
          ("Chị Yến", "đồng nghiệp"), ("Hoa", "em gái"), ("Nam", "bạn thân"), ("Cô Thảo", "cô giáo"), ("Bác Ba", "hàng xóm"),
          ("Quang", "đồng nghiệp"), ("Vy", "bạn")]


def make_context(apps: list[str], now: dt.datetime | None = None, city: str | None = None) -> tuple[dict, dt.datetime]:
    city = city or R.choice(list(CITIES))
    c = CITIES[city]
    if now is None:
        d = dt.date(2026, 9, 1) + dt.timedelta(days=R.randint(0, 110))
        now = dt.datetime(d.year, d.month, d.day, R.randint(7, 20), R.choice(range(0, 60, 5)))
    ctx = {"current_time": now.strftime("%Y-%m-%dT%H:%M:00") + TZ, "timezone": "Asia/Ho_Chi_Minh",
           "location": {"lat": round(c["lat"] + R.uniform(-0.02, 0.02), 4), "lng": round(c["lng"] + R.uniform(-0.02, 0.02), 4)},
           "user_profile": {"name": R.choice(NAMES), "home_address": R.choice(c["homes"]), "work_address": R.choice(c["works"]), "city": city},
           "installed_apps": apps}
    return ctx, now


def contacts_state(k: int = 8, must: list[str] = ()) -> dict:
    pool = [p for p in PEOPLE if p[0] not in must]
    chosen = [p for p in PEOPLE if p[0] in must] + R.sample(pool, k - len(must))
    R.shuffle(chosen)
    return {"contacts": [{"id": rid("c"), "name": n, "relation": rel, "phone": "09" + "".join(str(R.randint(0, 9)) for _ in range(9))}
                         for n, rel in chosen]}


def chats_state(names: list[str]) -> dict:
    chats = [{"id": rid("chat"), "name": n, "type": "direct", "members": [n], "messages": []} for n in names]
    chats.append({"id": rid("chat"), "name": "Gia đình", "type": "group", "members": ["Mẹ", "Bố", "Hoa"], "messages": []})
    R.shuffle(chats)
    return {"chats": chats}


def find_by(items, key, val):
    return next(x for x in items if x[key] == val)


class Spec:
    def __init__(self, app: str, idx: int, apps: list[str], now=None, city=None):
        self.id = f"synth_{app}_{idx:04d}"
        self.ctx, self.now = make_context(apps, now, city)
        self.state: dict = {}
        self.history: list = []
        self.text = ""
        self.gold: list = []

    def user(self, text):
        self.history.append({"role": "user", "audio_text": text})

    def bot(self, text, calls=()):
        h = {"role": "assistant", "text": text}
        if calls:
            h["tool_calls"] = list(calls)
        self.history.append(h)

    def dump(self) -> dict:
        return {"id": self.id, "context": self.ctx, "state": self.state, "history": self.history, "audio_text": self.text, "gold": self.gold}


def C(_tool, **args):
    return {"name": _tool, "arguments": args}


def ASK(tool, param):
    return C("sys.ask_missing_info", tool_name=tool, params=[param])


# ------------------------------------------------------------------------------------------------------------ apps
# Each generator: gen_<app>(idx) -> Spec. Scenario chosen by idx so the mix is controlled.

ECOM_CATALOG = {
    "tai nghe bluetooth": [("Tai nghe Bluetooth Sony WH-CH520", 990000, "Sony Official", 4.7), ("Tai nghe Bluetooth Xiaomi Buds 4", 590000, "Xiaomi Store", 4.5),
                           ("Tai nghe Bluetooth JBL Tune 520", 1190000, "JBL Việt Nam", 4.8), ("Tai nghe Bluetooth Baseus WM01", 290000, "Baseus", 4.3)],
    "sạc dự phòng": [("Sạc dự phòng Anker 10000mAh", 450000, "Anker", 4.8), ("Sạc dự phòng Xiaomi 20000mAh", 520000, "Xiaomi Store", 4.6),
                     ("Sạc dự phòng Baseus 10000mAh", 350000, "Baseus", 4.4)],
    "chuột không dây": [("Chuột không dây Logitech M331", 320000, "Logitech", 4.8), ("Chuột không dây Rapoo M100", 180000, "Rapoo", 4.4),
                        ("Chuột không dây Xiaomi Silent", 250000, "Xiaomi Store", 4.5)],
    "bình giữ nhiệt": [("Bình giữ nhiệt Lock&Lock 500ml", 290000, "Lock&Lock", 4.7), ("Bình giữ nhiệt Elmich 750ml", 350000, "Elmich", 4.6)],
    "nồi chiên không dầu": [("Nồi chiên không dầu Philips 4.1L", 2190000, "Philips", 4.8), ("Nồi chiên không dầu Lock&Lock 5.2L", 1590000, "Lock&Lock", 4.6),
                            ("Nồi chiên không dầu Sunhouse 6L", 1190000, "Sunhouse", 4.4)],
    "bàn phím cơ": [("Bàn phím cơ Akko 3087", 1290000, "Akko", 4.8), ("Bàn phím cơ E-Dra EK387", 690000, "E-Dra", 4.5)],
    "ốp lưng iPhone 15": [("Ốp lưng iPhone 15 silicon", 120000, "Phụ kiện 24h", 4.3), ("Ốp lưng iPhone 15 trong suốt", 90000, "Phụ kiện 24h", 4.2)],
    "balo laptop": [("Balo laptop Mikkor 15.6 inch", 650000, "Mikkor", 4.7), ("Balo laptop Tomtoc 14 inch", 890000, "Tomtoc", 4.8)],
}


def ecom_products():
    prods = []
    for q, lst in ECOM_CATALOG.items():
        for name, price, seller, rating in lst:
            prods.append({"id": rid("p"), "name": name, "price": price, "seller": seller, "category": q, "rating": rating,
                          "in_stock": R.random() > 0.15})
    return prods


def ecom_orders(prods, now):
    orders = []
    for st in R.sample(["placed", "shipping", "delivered", "delivered", "cancelled"], 4):
        p = R.choice(prods)
        q = R.randint(1, 2)
        placed = now - dt.timedelta(days=R.randint(1, 9), hours=R.randint(0, 10))
        o = {"id": rid("ord"), "items": [{"product_id": p["id"], "name": p["name"], "price": p["price"], "quantity": q}],
             "total": p["price"] * q, "status": st, "placed_at": placed.strftime("%Y-%m-%dT%H:%M:00") + TZ}
        if st == "delivered":
            o["delivered_at"] = (placed + dt.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:00") + TZ
        orders.append(o)
    return orders


def gen_ecommerce(idx: int) -> Spec:
    kind = ["buy", "buy", "buy_cheapest", "buy_rating", "cart_only", "pay", "cancel", "return", "return_ask", "status",
            "hist_pick", "oos", "cancel_ambig", "buy_remind"][idx % 14]
    apps = ["ecommerce", "contacts", "reminders"] if kind != "buy_remind" else ["ecommerce", "reminders", "calendar"]
    s = Spec("ecommerce", idx, apps)
    prods = ecom_products()
    s.state = {"ecommerce": {"products": prods, "cart": [], "orders": [], "returns": []}, "contacts": contacts_state(), "reminders": {"reminders": []}}
    if "calendar" in apps:
        s.state["calendar"] = {"events": []}
    s.state["ecommerce"]["orders"] = ecom_orders(prods, s.now)
    q = R.choice(list(ECOM_CATALOG))
    cands = [p for p in prods if p["category"] == q]
    instock = [p for p in cands if p["in_stock"]] or cands
    for p in cands:
        if p is instock[0]:
            p["in_stock"] = True
    instock = [p for p in cands if p["in_stock"]]
    n = R.randint(1, 3)
    if kind in ("buy", "buy_remind", "pay", "cart_only"):
        p = R.choice(instock)
        brand = p["name"].split()[len(q.split()):][0] if len(p["name"].split()) > len(q.split()) else ""
        say_q = q
        if kind == "cart_only":
            s.text = style(f"Thêm {qty_phrase(n)} cái {q} {brand} vào giỏ hàng")
            s.gold = [C("ecommerce.search", query=say_q), C("ecommerce.add_to_cart", product_id=p["id"], quantity=n)]
        else:
            pay = {"pay": R.choice([("ewallet", "trả bằng ví điện tử"), ("bank", "thanh toán chuyển khoản")])}.get(kind)
            extra = f", {pay[1]}" if pay else ""
            s.text = style(f"Mua {qty_phrase(n)} cái {q} {brand} rồi đặt hàng luôn{extra}")
            co = C("ecommerce.checkout", payment=pay[0]) if pay else C("ecommerce.checkout")
            s.gold = [C("ecommerce.search", query=say_q), C("ecommerce.add_to_cart", product_id=p["id"], quantity=n), co]
            if kind == "buy_remind":
                dp, d = date_phrase(s.now, allow_today=False)
                h = R.choice([8, 9, 18, 19])
                s.text = style(f"Đặt mua {qty_phrase(n)} {q} {brand}, xong nhắc mình {time_phrase(h, 0)} {dp} ra nhận hàng")
                s.gold.append(C("reminders.create", content="ra nhận hàng", time=iso(d, h, 0)))
    elif kind in ("buy_cheapest", "buy_rating"):
        if kind == "buy_cheapest":
            p = min(instock, key=lambda x: x["price"])
            crit = R.choice(["loại rẻ nhất còn hàng", "cái nào rẻ nhất mà còn hàng"])
        else:
            best = max(x["rating"] for x in instock)
            if sum(1 for x in instock if x["rating"] == best) > 1:
                instock[0]["rating"] = round(best + 0.1, 1)
            p = max(instock, key=lambda x: x["rating"])
            crit = R.choice(["loại đánh giá cao nhất còn hàng", "cái nào được đánh giá tốt nhất"])
        maxp = R.choice([None, None, ((max(x["price"] for x in cands) // 100000) + 1) * 100000])
        mp = f" dưới {money_phrase(maxp)}" if maxp else ""
        s.text = style(f"Tìm {q}{mp}, lấy {crit}, mua {qty_phrase(n)} cái rồi đặt luôn")
        sa = {"query": q, **({"max_price": maxp} if maxp else {})}
        s.gold = [C("ecommerce.search", **sa), C("ecommerce.add_to_cart", product_id=p["id"], quantity=n), C("ecommerce.checkout")]
    elif kind in ("cancel", "cancel_ambig", "return", "return_ask", "status"):
        orders = s.state["ecommerce"]["orders"]
        want = {"cancel": ("placed", "shipping"), "cancel_ambig": ("placed", "shipping"), "return": ("delivered",), "return_ask": ("delivered",),
                "status": ("placed", "shipping", "delivered")}[kind]
        o = next((x for x in orders if x["status"] in want), None)
        if o is None:
            o = orders[0]
            o["status"] = want[0]
        item = o["items"][0]["name"]
        short = " ".join(item.split()[:3])
        say_short = short[0].lower() + short[1:]
        # make the target order the only one whose item starts with what the user says (the ambiguous case adds a twin below)
        fillers = [p for p in prods if not p["name"].startswith(short)]
        for x in orders:
            if x is not o and x["items"][0]["name"].startswith(short):
                f = R.choice(fillers)
                x["items"][0].update(product_id=f["id"], name=f["name"], price=f["price"])
                x["total"] = f["price"] * x["items"][0]["quantity"]
        if kind == "cancel_ambig":
            twin = json.loads(json.dumps(o))
            twin["id"] = rid("ord")
            twin["status"] = R.choice(["placed", "shipping"])
            orders.append(twin)
            s.text = style(f"Huỷ giùm mình đơn {say_short} đi")
            s.gold = [C("ecommerce.order_status"), ASK("ecommerce.cancel_order", "order_id")]
        elif kind == "cancel":
            s.text = style(R.choice([f"Huỷ cái đơn {say_short} mình mới đặt", f"Mình không lấy {say_short} nữa, huỷ đơn đó đi"]))
            s.gold = [C("ecommerce.order_status"), C("ecommerce.cancel_order", order_id=o["id"])]
        elif kind == "return":
            reason, say = R.choice([("damaged", "bị vỡ"), ("damaged", "bị hỏng không lên"), ("wrong_item", "giao sai màu"),
                                    ("wrong_item", "giao nhầm hàng"), ("changed_mind", "mình không cần nữa")])
            s.text = style(f"Đơn {say_short} {say}, làm yêu cầu trả hàng cho mình")
            s.gold = [C("ecommerce.order_status"), C("ecommerce.request_return", order_id=o["id"], reason=reason)]
        elif kind == "return_ask":
            s.text = style(f"Mình muốn trả lại đơn {say_short}")
            s.gold = [C("ecommerce.order_status"), ASK("ecommerce.request_return", "reason")]
        else:
            s.text = style(R.choice([f"Đơn {say_short} giao tới đâu rồi?", f"Kiểm tra giúp đơn {say_short} của mình"]))
            s.gold = [C("ecommerce.order_status")]
    elif kind == "hist_pick":
        p_list = instock[:3]
        s.user(style(f"Tìm {q} cho mình"))
        names = "; ".join(f"{i + 1}. {x['name']} giá {vnd(x['price'])}" for i, x in enumerate(p_list))
        s.bot(f"Có các sản phẩm: {names}.", [C("ecommerce.search", query=q)])
        i = R.randrange(len(p_list))
        ordw = ["đầu tiên", "thứ hai", "thứ ba"][i]
        s.text = style(f"Lấy cái {ordw}, {qty_phrase(n)} cái, đặt luôn")
        s.gold = [C("ecommerce.add_to_cart", product_id=p_list[i]["id"], quantity=n), C("ecommerce.checkout")]
    else:  # oos
        v = R.randrange(3)
        if v == 0:
            s.text = style("Đánh giá năm sao cho shop bán tai nghe hôm trước")
        elif v == 1:
            s.user(style(f"Tìm {q} giúp mình"))
            s.bot("Mình tìm được vài mẫu, bạn muốn lấy mẫu nào?", [C("ecommerce.search", query=q)])
            s.text = style(R.choice(["Thôi khỏi, để cuối tháng có lương rồi tính", "À thôi không mua nữa"]))
        else:
            s.text = style("Chat với người bán hỏi còn màu đen không")
        s.gold = []
    return s


GROCERY = {
    "trứng gà": [("Trứng gà ta hộp 10 quả", 42000, "hộp"), ("Trứng gà công nghiệp hộp 10 quả", 32000, "hộp")],
    "sữa tươi": [("Sữa tươi không đường Vinamilk 1L", 36000, "hộp"), ("Sữa tươi TH True Milk 1L", 38000, "hộp")],
    "thịt ba chỉ": [("Thịt ba chỉ heo 500g", 85000, "khay")], "cá basa": [("Cá basa phi lê 500g", 65000, "khay")],
    "gạo ST25": [("Gạo ST25 túi 5kg", 185000, "túi")], "rau cải ngọt": [("Rau cải ngọt 500g", 18000, "bó")],
    "chuối": [("Chuối già Nam Mỹ 1kg", 32000, "kg")], "dầu ăn": [("Dầu ăn Neptune 1L", 58000, "chai"), ("Dầu ăn Simply 1L", 62000, "chai")],
    "nước mắm": [("Nước mắm Nam Ngư 750ml", 39000, "chai")], "bánh mì sandwich": [("Bánh mì sandwich Kinh Đô", 25000, "gói")],
    "cà chua": [("Cà chua Đà Lạt 500g", 22000, "khay")], "thịt bò": [("Thịt bò úc thăn 300g", 145000, "khay")],
}


def gen_grocery(idx: int) -> Spec:
    kind = ["one", "one", "two", "cart_only", "deliver", "oos_stock", "ask_qty", "pantry_cond", "pantry_cond_false",
            "hist", "oos", "two", "recipe_combo"][idx % 13]
    apps = ["grocery", "reminders"] + (["pantry"] if kind.startswith("pantry") else []) + (["recipes"] if kind == "recipe_combo" else [])
    s = Spec("grocery", idx, apps)
    prods = []
    for cat, lst in GROCERY.items():
        for name, price, unit in lst:
            prods.append({"id": rid("gp"), "name": name, "price": price, "unit": unit, "category": cat, "in_stock": True})
    s.state = {"grocery": {"products": prods, "cart": [], "orders": []}, "reminders": {"reminders": []}}
    cats = [c for c in GROCERY if len(GROCERY[c]) == 1]
    q1, q2 = R.sample(cats, 2)
    p1, p2 = find_by(prods, "category", q1), find_by(prods, "category", q2)
    n1, n2 = R.randint(1, 3), R.randint(1, 3)
    unit1, unit2 = p1["unit"], p2["unit"]
    if kind == "one":
        s.text = style(f"Đi chợ online mua {qty_phrase(n1)} {unit1} {q1} rồi đặt hàng luôn")
        s.gold = [C("grocery.search", query=q1), C("grocery.add_to_cart", product_id=p1["id"], quantity=n1), C("grocery.checkout")]
    elif kind == "two":
        s.text = style(f"Mua {qty_phrase(n1)} {unit1} {q1} với {qty_phrase(n2)} {unit2} {q2}, đặt luôn nhé")
        s.gold = [C("grocery.search", query=q1), C("grocery.add_to_cart", product_id=p1["id"], quantity=n1),
                  C("grocery.search", query=q2), C("grocery.add_to_cart", product_id=p2["id"], quantity=n2), C("grocery.checkout")]
    elif kind == "cart_only":
        s.text = style(f"Bỏ {qty_phrase(n1)} {unit1} {q1} vào giỏ đi chợ, chưa đặt vội")
        s.gold = [C("grocery.search", query=q1), C("grocery.add_to_cart", product_id=p1["id"], quantity=n1)]
    elif kind == "deliver":
        dp, d = date_phrase(s.now, allow_today=False)
        h, m = R.choice([(7, 0), (8, 30), (17, 0), (18, 0), (19, 30)])
        s.text = style(f"Mua {qty_phrase(n1)} {unit1} {q1}, giao lúc {time_phrase(h, m)} {dp}")
        s.gold = [C("grocery.search", query=q1), C("grocery.add_to_cart", product_id=p1["id"], quantity=n1),
                  C("grocery.checkout", delivery_time=iso(d, h, m))]
    elif kind == "oos_stock":
        cat = R.choice([c for c in GROCERY if len(GROCERY[c]) == 2])
        a, b = [x for x in prods if x["category"] == cat]
        a["in_stock"] = False
        s.text = style(f"Mua {qty_phrase(n1)} {a['unit']} {cat}, loại nào còn hàng thì lấy, đặt luôn")
        s.gold = [C("grocery.search", query=cat), C("grocery.add_to_cart", product_id=b["id"], quantity=n1), C("grocery.checkout")]
    elif kind == "ask_qty":
        s.text = style(f"Mua {q1} trên app đi chợ cho mình")
        s.gold = [C("grocery.search", query=q1), ASK("grocery.add_to_cart", "quantity")]
    elif kind in ("pantry_cond", "pantry_cond_false"):
        item = R.choice([("trứng gà", "trứng", "quả", 10, "hộp"), ("sữa tươi", "sữa", "hộp", 3, "hộp"), ("gạo ST25", "gạo", "kg", 5, "túi")])
        cat, short, unit, thr, gunit = item
        stock = R.randint(0, thr - 1) if kind == "pantry_cond" else R.randint(thr + 1, thr * 3)
        s.state["pantry"] = {"items": [{"id": rid("pi"), "name": short, "stock": stock, "unit": unit},
                                       {"id": rid("pi"), "name": "mì gói", "stock": R.randint(2, 20), "unit": "gói"},
                                       {"id": rid("pi"), "name": "nước mắm", "stock": 1, "unit": "chai"}]}
        p = find_by(prods, "category", cat)
        s.text = style(f"Coi tủ bếp còn {short} không, còn dưới {qty_phrase(thr)} {unit} thì đặt mua thêm {qty_phrase(n1)} {gunit} {cat}")
        s.gold = [C("pantry.list_items")]
        if kind == "pantry_cond":
            s.gold += [C("grocery.search", query=cat), C("grocery.add_to_cart", product_id=p["id"], quantity=n1), C("grocery.checkout")]
    elif kind == "hist":
        s.user(style(f"Trên app đi chợ có {q1} không?"))
        s.bot(f"Có {p1['name']} giá {vnd(p1['price'])} một {unit1}.", [C("grocery.search", query=q1)])
        s.text = style(f"Ừ lấy {qty_phrase(n1)} {unit1} rồi đặt luôn")
        s.gold = [C("grocery.add_to_cart", product_id=p1["id"], quantity=n1), C("grocery.checkout")]
    elif kind == "recipe_combo":
        rec = {"id": rid("rc"), "name": "Canh chua cá basa", "tags": ["canh", "cá"], "servings": 4, "time_min": 40,
               "ingredients": [{"name": "cá basa", "quantity": 500, "unit": "g"}, {"name": "cà chua", "quantity": 2, "unit": "quả"}],
               "steps": ["Sơ chế cá", "Nấu nước dùng", "Cho cá vào"]}
        s.state["recipes"] = {"recipes": [rec], "saved": []}
        pc = find_by(prods, "category", "cá basa")
        s.text = style("Lưu công thức canh chua cá basa, rồi mua một khay cá basa luôn")
        s.gold = [C("recipes.search", query="canh chua cá basa"), C("recipes.save", recipe_id=rec["id"]),
                  C("grocery.search", query="cá basa"), C("grocery.add_to_cart", product_id=pc["id"], quantity=1)]
    else:
        s.text = style(R.choice(["Huỷ cái đơn đi chợ hôm qua giùm mình", "Đổi địa chỉ giao đơn đi chợ hôm trước sang công ty"]))
        s.gold = []
    return s


PANTRY_ITEMS = [("gạo", "kg"), ("trứng", "quả"), ("sữa tươi", "hộp"), ("mì gói", "gói"), ("dầu ăn", "chai"), ("đường", "kg"),
                ("cà phê", "gói"), ("bột mì", "kg"), ("nước mắm", "chai"), ("hành tím", "củ")]


def gen_pantry(idx: int) -> Spec:
    kind = ["one", "one", "two", "all", "read", "ask", "cond_list", "cond_false", "hist", "oos", "correct", "remind"][idx % 12]
    apps = ["pantry"] + (["shopping_list"] if kind.startswith("cond") else []) + (["reminders"] if kind == "remind" else [])
    s = Spec("pantry", idx, apps)
    items = [{"id": rid("pi"), "name": n, "stock": R.randint(3, 30), "unit": u} for n, u in R.sample(PANTRY_ITEMS, 6)]
    s.state = {"pantry": {"items": items}}
    if "shopping_list" in apps:
        s.state["shopping_list"] = {"items": []}
    if "reminders" in apps:
        s.state["reminders"] = {"reminders": []}
    a, b = items[0], items[1]
    na, nb = R.randint(1, min(3, a["stock"])), R.randint(1, min(3, b["stock"]))
    if kind == "one":
        s.text = style(R.choice([f"Mình vừa dùng {qty_phrase(na)} {a['unit']} {a['name']}, trừ trong tủ bếp đi",
                                 f"Ghi là đã lấy {qty_phrase(na)} {a['unit']} {a['name']} ra nấu"]))
        s.gold = [C("pantry.list_items"), C("pantry.consume", item_id=a["id"], quantity=na)]
    elif kind == "two":
        s.text = style(f"Nấu xong rồi, trừ {qty_phrase(na)} {a['unit']} {a['name']} với {qty_phrase(nb)} {b['unit']} {b['name']} trong tủ bếp")
        s.gold = [C("pantry.list_items"), C("pantry.consume", item_id=a["id"], quantity=na), C("pantry.consume", item_id=b["id"], quantity=nb)]
    elif kind == "all":
        s.text = style(f"{a['name'].capitalize()} trong tủ mình dùng hết sạch rồi, cập nhật giùm")
        s.gold = [C("pantry.list_items"), C("pantry.consume", item_id=a["id"], quantity=a["stock"])]
    elif kind == "read":
        s.text = style(f"Tủ bếp còn bao nhiêu {a['name']} vậy?")
        s.gold = [C("pantry.list_items")]
    elif kind == "ask":
        s.text = style(f"Mình mới lấy ít {a['name']} ra dùng, trừ trong tủ đi")
        s.gold = [C("pantry.list_items"), ASK("pantry.consume", "quantity")]
    elif kind in ("cond_list", "cond_false"):
        thr = R.choice([3, 5])
        a["stock"] = R.randint(0, thr - 1) if kind == "cond_list" else R.randint(thr + 2, thr + 10)
        buy = R.randint(1, 3)
        s.text = style(f"Xem {a['name']} còn không, dưới {qty_phrase(thr)} {a['unit']} thì ghi vào danh sách đi chợ mua {qty_phrase(buy)} {a['unit']}")
        s.gold = [C("pantry.list_items")] + ([C("shopping_list.add", name=a["name"], quantity=buy)] if kind == "cond_list" else [])
    elif kind == "hist":
        s.user(style("Tủ bếp nhà mình còn những gì?"))
        lst = ", ".join(f"{x['name']} {x['stock']} {x['unit']}" for x in items)
        s.bot(f"Trong tủ bếp còn: {lst}.", [C("pantry.list_items")])
        s.text = style(f"Ok, vậy trừ {qty_phrase(na)} {a['unit']} {a['name']} nhé, mình vừa dùng")
        s.gold = [C("pantry.consume", item_id=a["id"], quantity=na)]
    elif kind == "correct":
        wrong = na + 1
        s.text = style(f"Trừ {qty_phrase(wrong)} {a['unit']} {a['name']}, à không, {qty_phrase(na)} {a['unit']} thôi")
        s.gold = [C("pantry.list_items"), C("pantry.consume", item_id=a["id"], quantity=na)]
    elif kind == "remind":
        dp, d = date_phrase(s.now, allow_today=False)
        s.text = style(f"Trừ {qty_phrase(na)} {a['unit']} {a['name']} trong tủ, rồi nhắc mình {time_phrase(17, 30)} {dp} mua thêm {a['name']}")
        s.gold = [C("pantry.list_items"), C("pantry.consume", item_id=a["id"], quantity=na),
                  C("reminders.create", content=f"mua thêm {a['name']}", time=iso(d, 17, 30))]
    else:
        s.text = style(R.choice(["Tủ lạnh đang để mấy độ vậy?", "Thêm món mới vào tủ bếp: hai ký khoai tây"]))
        s.gold = []
    return s


RECIPES = [("Phở bò", ["phở", "bò"], [("bánh phở", 500, "g"), ("thịt bò", 300, "g"), ("hành lá", 2, "nhánh")]),
           ("Canh chua cá lóc", ["canh", "cá"], [("cá lóc", 500, "g"), ("me chua", 50, "g"), ("cà chua", 2, "quả")]),
           ("Gà kho gừng", ["gà", "kho"], [("thịt gà", 600, "g"), ("gừng", 1, "củ")]),
           ("Súp bí đỏ", ["súp", "bí đỏ"], [("bí đỏ", 400, "g"), ("sữa tươi", 200, "ml")]),
           ("Bún chả Hà Nội", ["bún", "chả"], [("bún", 500, "g"), ("thịt ba chỉ", 400, "g")]),
           ("Trứng chiên cà chua", ["trứng"], [("trứng", 4, "quả"), ("cà chua", 2, "quả")]),
           ("Bánh flan", ["tráng miệng", "trứng"], [("trứng", 4, "quả"), ("sữa tươi", 400, "ml"), ("đường", 80, "g")]),
           ("Cơm chiên dương châu", ["cơm", "chiên"], [("cơm nguội", 2, "chén"), ("trứng", 2, "quả"), ("lạp xưởng", 1, "cây")])]


def gen_recipes(idx: int) -> Spec:
    kind = ["save", "save", "servings", "steps", "hist_save", "oos", "note", "servings", "save_send", "hist_steps"][idx % 10]
    apps = ["recipes"] + (["notes"] if kind == "note" else []) + (["chat_ott"] if kind == "save_send" else [])
    s = Spec("recipes", idx, apps)
    recs = []
    for name, tags, ings in R.sample(RECIPES, 5):
        base = R.choice([2, 4])
        recs.append({"id": rid("rc"), "name": name, "tags": tags, "servings": base, "time_min": R.choice([20, 30, 45, 60]),
                     "ingredients": [{"name": n, "quantity": q, "unit": u} for n, q, u in ings],
                     "steps": ["Sơ chế nguyên liệu", "Nấu theo công thức", "Nêm nếm vừa ăn"]})
    s.state = {"recipes": {"recipes": recs, "saved": []}}
    r = recs[0]
    q = r["name"].lower()
    if kind == "save":
        s.text = style(R.choice([f"Lưu công thức {q} lại cho mình", f"Tìm cách nấu {q} rồi lưu vào mục đã lưu"]))
        s.gold = [C("recipes.search", query=q), C("recipes.save", recipe_id=r["id"])]
    elif kind == "servings":
        n = R.choice([3, 5, 6, 8])
        s.text = style(f"Nấu {q} cho {qty_phrase(n)} người thì cần bao nhiêu nguyên liệu?")
        s.gold = [C("recipes.search", query=q, servings=n)]
    elif kind == "steps":
        s.text = style(f"Chỉ mình các bước làm {q}")
        s.gold = [C("recipes.search", query=q), C("recipes.get", recipe_id=r["id"])]
    elif kind in ("hist_save", "hist_steps"):
        tag = r["tags"][0]
        hits = [x for x in recs if tag in x["tags"] or tag in x["name"].lower()]
        s.user(style(f"Có món nào nấu với {tag} không?"))
        s.bot("Có: " + ", ".join(x["name"] for x in hits) + ".", [C("recipes.search", query=tag)])
        if kind == "hist_save":
            s.text = style(f"Lưu món {r['name'][0].lower() + r['name'][1:]} lại")
            s.gold = [C("recipes.save", recipe_id=r["id"])]
        else:
            s.text = style(f"Món {r['name'][0].lower() + r['name'][1:]} làm sao, chỉ chi tiết các bước")
            s.gold = [C("recipes.get", recipe_id=r["id"])]
    elif kind == "note":
        s.text = style(f"Tìm công thức {q} rồi ghi nguyên liệu vào ghi chú cho mình")
        content = ", ".join(f"{i['name']} {i['quantity']} {i['unit']}" for i in r["ingredients"])
        s.state["notes"] = {"notes": []}
        s.gold = [C("recipes.search", query=q), C("notes.create", title=f"Nguyên liệu {q}", content=content)]
    elif kind == "save_send":
        name = R.choice(["Lan", "Hương", "Mẹ"])
        s.state["chat_ott"] = chats_state([name, "Minh", "Tuấn"])
        chat = find_by(s.state["chat_ott"]["chats"], "name", name)
        s.text = style(f"Lưu công thức {q}, rồi nhắn Zalo cho {name} là tối nay mình nấu {q}")
        s.gold = [C("recipes.search", query=q), C("recipes.save", recipe_id=r["id"]), C("chat_ott.list_chats"),
                  C("chat_ott.send_message", chat_id=chat["id"], content=f"tối nay mình nấu {q}")]
    else:
        s.text = style(R.choice(["Bật nồi cơm điện nấu cơm giùm mình", "Đặt giao một phần phở bò về nhà"]))
        s.gold = []
    return s


HABITS = ["Chạy bộ", "Uống đủ 2 lít nước", "Đọc sách 30 phút", "Thiền 10 phút", "Học tiếng Anh", "Ngủ trước 11 giờ", "Tập yoga", "Đi bộ mười nghìn bước"]


def gen_habit_tracker(idx: int) -> Spec:
    kind = ["today", "today", "yesterday", "two", "read", "ambig", "hist", "oos", "remind", "daybefore"][idx % 10]
    apps = ["habit_tracker"] + (["reminders"] if kind == "remind" else [])
    s = Spec("habit_tracker", idx, apps)
    today = s.now.date()
    names = R.sample(HABITS, 5)
    if kind == "ambig":
        names[1] = "Chạy bộ buổi sáng"
        names[2] = "Chạy bộ buổi tối"
        names[0] = "Thiền 10 phút"
    habits = []
    for n in names:
        last = today - dt.timedelta(days=R.choice([1, 1, 2, 3]))
        habits.append({"id": rid("hb"), "name": n, "streak": R.randint(1, 20), "last_logged": last.isoformat()})
    s.state = {"habit_tracker": {"habits": habits, "logs": []}}
    if "reminders" in apps:
        s.state["reminders"] = {"reminders": []}
    h, h2 = habits[0], habits[1]
    short = h["name"].lower()
    if kind == "today":
        s.text = style(R.choice([f"Đánh dấu hôm nay mình đã {short}", f"Hôm nay {short} xong rồi, ghi lại giùm"]))
        s.gold = [C("habit_tracker.list_habits"), C("habit_tracker.log", habit_id=h["id"], date=today.isoformat())]
    elif kind in ("yesterday", "daybefore"):
        off = 1 if kind == "yesterday" else 2
        h["last_logged"] = (today - dt.timedelta(days=off + 1)).isoformat()
        say = "hôm qua" if off == 1 else R.choice(["hôm kia", "hai hôm trước"])
        s.text = style(f"{say.capitalize()} mình có {short} mà quên đánh dấu, ghi bù giùm")
        s.gold = [C("habit_tracker.list_habits"), C("habit_tracker.log", habit_id=h["id"], date=(today - dt.timedelta(days=off)).isoformat())]
    elif kind == "two":
        s.text = style(f"Hôm nay mình {short} với {h2['name'].lower()} rồi, đánh dấu cả hai")
        s.gold = [C("habit_tracker.list_habits"), C("habit_tracker.log", habit_id=h["id"], date=today.isoformat()),
                  C("habit_tracker.log", habit_id=h2["id"], date=today.isoformat())]
    elif kind == "read":
        s.text = style(f"Chuỗi {short} của mình đang được mấy ngày rồi?")
        s.gold = [C("habit_tracker.list_habits")]
    elif kind == "ambig":
        s.text = style("Hôm nay mình chạy bộ rồi, đánh dấu đi")
        s.gold = [C("habit_tracker.list_habits"), ASK("habit_tracker.log", "habit_id")]
    elif kind == "hist":
        s.user(style("Mình đang theo dõi những thói quen nào?"))
        s.bot("Bạn đang theo dõi: " + ", ".join(f"{x['name']} (chuỗi {x['streak']} ngày)" for x in habits) + ".", [C("habit_tracker.list_habits")])
        s.text = style(f"Đánh dấu {short} hôm nay luôn")
        s.gold = [C("habit_tracker.log", habit_id=h["id"], date=today.isoformat())]
    elif kind == "remind":
        s.text = style(f"Ghi là hôm nay mình đã {short}, rồi nhắc mình {time_phrase(21, 0)} mai {h2['name'].lower()}")
        s.gold = [C("habit_tracker.list_habits"), C("habit_tracker.log", habit_id=h["id"], date=today.isoformat()),
                  C("reminders.create", content=h2["name"].lower(), time=iso(today + dt.timedelta(days=1), 21, 0))]
    else:
        s.text = style(R.choice(["Tạo thói quen mới là tập hít đất mỗi sáng", "Xoá thói quen tập yoga đi"]))
        s.gold = []
    return s


STOCKS = [("FPT", "FPT Corp", ["FPT", "ép pê tê"]), ("VNM", "Vinamilk", ["Vinamilk", "VNM"]), ("VCB", "Vietcombank", ["Vietcombank", "VCB"]),
          ("HPG", "Hòa Phát", ["Hòa Phát", "HPG"]), ("MWG", "Thế Giới Di Động", ["Thế Giới Di Động", "MWG"]), ("TCB", "Techcombank", ["Techcombank", "TCB"]),
          ("SSI", "Chứng khoán SSI", ["SSI"]), ("MSN", "Masan", ["Masan", "MSN"]), ("ACB", "Ngân hàng ACB", ["ACB"])]


def gen_stocks(idx: int) -> Spec:
    kind = ["quote", "buy", "buy_limit", "sell", "alert", "ask_qty", "cond_hist_true", "cond_hist_false", "cond_read", "portfolio",
            "sell_all", "oos", "alert_below"][idx % 13]
    s = Spec("stocks", idx, ["stocks", "reminders"])
    picks = R.sample(STOCKS, 6)
    quotes, holds = [], []
    for sym, name, _ in picks:
        price = R.randint(150, 1300) * 100
        quotes.append({"symbol": sym, "name": name, "price": price, "change_pct": round(R.uniform(-3, 3), 2)})
    for q in quotes[:3]:
        holds.append({"symbol": q["symbol"], "name": q["name"], "quantity": R.choice([100, 200, 300, 500, 1000]),
                      "avg_price": q["price"] + R.randint(-50, 50) * 100, "price": q["price"]})
    s.state = {"stocks": {"holdings": holds, "orders": [], "alerts": [], "quotes": quotes}, "reminders": {"reminders": []}}
    q = quotes[0]
    say = R.choice(find_by([dict(sym=a, names=c) for a, _, c in picks], "sym", q["symbol"])["names"])
    n = R.choice([100, 200, 500, 1000, 50])
    if kind == "quote":
        s.text = style(R.choice([f"Giá cổ phiếu {say} hôm nay bao nhiêu?", f"Mã {say} đang giá mấy?"]))
        s.gold = [C("stocks.get_quote", symbol=q["symbol"])]
    elif kind == "buy":
        s.text = style(f"Đặt mua {qty_phrase(n) if n < 100 else n} cổ phiếu {say} giá thị trường")
        s.gold = [C("stocks.place_order", symbol=q["symbol"], side="buy", quantity=n)]
    elif kind == "buy_limit":
        p = q["price"] - R.randint(1, 10) * 100
        s.text = style(f"Đặt lệnh mua {n} cổ {say} giá {price_phrase(p)}")
        s.gold = [C("stocks.place_order", symbol=q["symbol"], side="buy", quantity=n, price=p)]
    elif kind == "sell":
        hq = holds[0]
        m = min(hq["quantity"], R.choice([100, 200]))
        s.text = style(f"Bán {m} cổ phiếu {say}")
        s.gold = [C("stocks.place_order", symbol=q["symbol"], side="sell", quantity=m)]
    elif kind == "sell_all":
        hq = holds[0]
        s.text = style(f"Bán hết số cổ phiếu {say} mình đang có")
        s.gold = [C("stocks.get_portfolio"), C("stocks.place_order", symbol=q["symbol"], side="sell", quantity=hq["quantity"])]
    elif kind in ("alert", "alert_below"):
        up = kind == "alert"
        p = (q["price"] // 1000 + (R.randint(2, 8) if up else -R.randint(2, 8))) * 1000
        s.text = style(f"Báo mình khi {say} {'lên trên' if up else 'xuống dưới'} {price_phrase(p)}")
        s.gold = [C("stocks.set_price_alert", symbol=q["symbol"], price=p, direction="above" if up else "below")]
    elif kind == "ask_qty":
        s.text = style(f"Mua cổ phiếu {say} cho mình")
        s.gold = [ASK("stocks.place_order", "quantity")]
    elif kind in ("cond_hist_true", "cond_hist_false"):
        s.user(style(f"{say} giá bao nhiêu rồi?"))
        s.bot(f"{q['symbol']} đang ở {vnd(q['price'])}.", [C("stocks.get_quote", symbol=q["symbol"])])
        thr = (q["price"] // 1000 + (2 if kind == "cond_hist_true" else -2)) * 1000
        s.text = style(f"Nếu dưới {price_phrase(thr)} thì mua {n} cổ, không thì thôi")
        s.gold = [C("stocks.place_order", symbol=q["symbol"], side="buy", quantity=n)] if kind == "cond_hist_true" else []
    elif kind == "cond_read":
        true = R.random() < 0.5
        thr = (q["price"] // 1000 + (3 if true else -3)) * 1000
        s.text = style(f"Xem giá {say}, nếu thấp hơn {price_phrase(thr)} thì đặt mua {n} cổ phiếu")
        s.gold = [C("stocks.get_quote", symbol=q["symbol"])] + ([C("stocks.place_order", symbol=q["symbol"], side="buy", quantity=n)] if true else [])
    elif kind == "portfolio":
        s.text = style(R.choice(["Danh mục của mình đang có những mã nào?", "Tổng giá trị cổ phiếu mình đang giữ là bao nhiêu?"]))
        s.gold = [C("stocks.get_portfolio")]
    else:
        s.text = style(R.choice(["Rút tiền từ tài khoản chứng khoán về ngân hàng", "Mở tài khoản chứng khoán mới cho vợ mình"]))
        s.gold = []
    return s


EVENTS = [("Liveshow Mỹ Tâm Tri Âm", "ca nhạc", "Nhà hát Hòa Bình"), ("Kịch Bỉ vỏ", "kịch", "Sân khấu IDECAF"),
          ("Triển lãm tranh Đông Hồ", "triển lãm", "Bảo tàng Mỹ thuật"), ("Hòa nhạc Giao hưởng mùa thu", "hòa nhạc", "Nhà hát Lớn"),
          ("Chung kết bóng chuyền nữ", "thể thao", "Nhà thi đấu Phú Thọ"), ("Đêm nhạc Trịnh Công Sơn", "ca nhạc", "Phòng trà Bến Thành"),
          ("Hài kịch Ngày xửa ngày xưa", "kịch", "Sân khấu Thanh Niên"), ("Lễ hội ẩm thực đường phố", "lễ hội", "Công viên 23/9")]


def gen_event_tickets(idx: int) -> Spec:
    kind = ["book", "book", "book_cal", "book_sms", "ask_qty", "read", "hist", "oos", "correct", "book_cal"][idx % 10]
    apps = ["event_tickets"] + (["calendar"] if kind == "book_cal" else []) + (["contacts", "sms"] if kind == "book_sms" else [])
    s = Spec("event_tickets", idx, apps)
    evs = []
    for name, cat, venue in R.sample(EVENTS, 5):
        d = s.now.date() + dt.timedelta(days=R.randint(2, 25))
        evs.append({"id": rid("ev"), "name": name, "category": cat, "date": d.isoformat(), "time": R.choice(["19:30", "20:00", "18:00", "09:00"]),
                    "venue": venue, "price": R.choice([150000, 250000, 300000, 450000, 600000]), "available": R.randint(6, 80)})
    s.state = {"event_tickets": {"events": evs, "bookings": []}}
    e = evs[0]
    q = " ".join(e["name"].split()[:3])
    n = R.randint(1, 4)
    hh, mm = map(int, e["time"].split(":"))
    if kind == "book":
        s.text = style(R.choice([f"Đặt {qty_phrase(n)} vé {e['name']}", f"Mua cho mình {qty_phrase(n)} vé xem {q}"]))
        s.gold = [C("event_tickets.search", query=q if q in e["name"] else e["name"]), C("event_tickets.book", event_id=e["id"], quantity=n)]
        s.gold[0]["arguments"]["query"] = q
    elif kind == "book_cal":
        s.state["calendar"] = {"events": []}
        s.text = style(f"Đặt {qty_phrase(n)} vé {q} rồi thêm vào lịch giúp mình")
        d = dt.date.fromisoformat(e["date"])
        s.gold = [C("event_tickets.search", query=q), C("event_tickets.book", event_id=e["id"], quantity=n),
                  C("calendar.create_event", title=e["name"], start=iso(d, hh, mm), end=iso(d, hh + 1, mm), location=e["venue"])]
    elif kind == "book_sms":
        who = R.choice(["Minh", "Hương", "Lan", "Nam"])
        s.state["contacts"] = contacts_state(8, must=[who])
        s.state["sms"] = {"messages": []}
        c = find_by(s.state["contacts"]["contacts"], "name", who)
        s.text = style(f"Đặt {qty_phrase(n)} vé {q}, xong nhắn tin cho {who} là đã có vé rồi")
        s.gold = [C("event_tickets.search", query=q), C("event_tickets.book", event_id=e["id"], quantity=n),
                  C("contacts.search", query=who), C("sms.send", contact_id=c["id"], content="đã có vé rồi")]
    elif kind == "ask_qty":
        s.text = style(f"Đặt vé {q} cho mình")
        s.gold = [C("event_tickets.search", query=q), ASK("event_tickets.book", "quantity")]
    elif kind == "read":
        cat = e["category"]
        s.text = style(R.choice([f"Sắp tới có {cat} gì không?", f"Tìm giúp mấy sự kiện {cat} sắp diễn ra"]))
        s.gold = [C("event_tickets.search", query=cat)]
    elif kind == "hist":
        cat = e["category"]
        hits = [x for x in evs if x["category"] == cat]
        s.user(style(f"Dạo này có {cat} gì hay không?"))
        s.bot("Có: " + "; ".join(f"{x['name']} ngày {x['date']} tại {x['venue']}" for x in hits) + ".", [C("event_tickets.search", query=cat)])
        s.text = style(f"Lấy {qty_phrase(n)} vé {e['name'][0].lower() + e['name'][1:]} nhé")
        s.gold = [C("event_tickets.book", event_id=e["id"], quantity=n)]
    elif kind == "correct":
        s.text = style(f"Đặt {qty_phrase(n + 1)} vé {q}, à nhầm, {qty_phrase(n)} vé thôi")
        s.gold = [C("event_tickets.search", query=q), C("event_tickets.book", event_id=e["id"], quantity=n)]
    else:
        s.text = style(R.choice(["Huỷ vé xem kịch tuần trước giúp mình", "Đổi chỗ ngồi vé ca nhạc lên hàng đầu"]))
        s.gold = []
    return s


ROUTES = [("Hà Nội", "Hải Phòng"), ("Hà Nội", "Huế"), ("Hà Nội", "Đà Nẵng"), ("TP.HCM", "Nha Trang"), ("TP.HCM", "Đà Lạt"),
          ("TP.HCM", "Vũng Tàu"), ("Đà Nẵng", "Huế"), ("Huế", "Đà Nẵng"), ("Đà Nẵng", "Hà Nội"), ("TP.HCM", "Đà Nẵng")]


def gen_train_bus_tickets(idx: int) -> Spec:
    kind = ["book_early", "book_cheap", "book_evening", "cancel", "read", "ask_date", "hist", "oos", "cancel_ambig", "book_cal",
            "book_type"][idx % 11]
    apps = ["train_bus_tickets"] + (["calendar"] if kind == "book_cal" else [])
    o, d_ = R.choice(ROUTES)
    s = Spec("train_bus_tickets", idx, apps, city=o if o in CITIES else None)
    dp, day = date_phrase(s.now, allow_today=False)
    trips = []
    dep_hours = R.sample([6, 7, 8, 9, 13, 14, 19, 20, 21, 22], R.randint(4, 6))
    for dep_h in dep_hours:
        typ = R.choice(["train", "bus"])
        dur = R.randint(2, 12)
        trips.append({"id": rid("trip"), "type": typ, "operator": R.choice(["Đường sắt VN", "SE"]) if typ == "train" else R.choice(["Phương Trang", "Hoàng Long", "Kumho"]),
                      "origin": o, "destination": d_, "date": day.isoformat(), "depart": f"{dep_h:02d}:{R.choice(['00', '30'])}",
                      "arrive": f"{(dep_h + dur) % 24:02d}:00", "price": R.choice([180000, 250000, 320000, 450000, 520000, 690000]),
                      "seats_left": R.randint(3, 30)})
    # distinct departure times and prices so "sớm nhất / rẻ nhất / tối" are unambiguous
    for i, t in enumerate(sorted(trips, key=lambda x: x["depart"])):
        t["price"] += i * 10000
    trips.sort(key=lambda x: R.random())
    s.state = {"train_bus_tickets": {"trips": trips, "bookings": []}}
    n = R.randint(1, 3)
    sa = {"origin": o, "destination": d_, "date": day.isoformat()}
    if kind == "book_early":
        t = min(trips, key=lambda x: x["depart"])
        s.text = style(f"Đặt {qty_phrase(n)} vé chuyến sớm nhất từ {o} đi {d_} {dp}")
        s.gold = [C("train_bus_tickets.search", **sa), C("train_bus_tickets.book", trip_id=t["id"], seats=n)]
    elif kind == "book_cheap":
        t = min(trips, key=lambda x: x["price"])
        s.text = style(f"{dp.capitalize()} mình đi {d_} từ {o}, đặt {qty_phrase(n)} vé chuyến rẻ nhất")
        s.gold = [C("train_bus_tickets.search", **sa), C("train_bus_tickets.book", trip_id=t["id"], seats=n)]
    elif kind == "book_type":
        typ = R.choice(["train", "bus"])
        for t in trips[:1]:
            t["type"] = typ
        same = [t for t in trips if t["type"] == typ]
        t = min(same, key=lambda x: x["depart"])
        word = "tàu" if typ == "train" else "xe khách"
        s.text = style(f"Đặt {qty_phrase(n)} vé {word} {o} đi {d_} {dp}, chuyến sớm nhất")
        s.gold = [C("train_bus_tickets.search", **sa, type=typ), C("train_bus_tickets.book", trip_id=t["id"], seats=n)]
    elif kind == "book_evening":
        ev = [t for t in trips if int(t["depart"][:2]) >= 18]
        if not ev:
            trips[0]["depart"] = "20:00"
            ev = [trips[0]]
        t = min(ev, key=lambda x: x["depart"])
        s.text = style(f"Tìm vé {o} đi {d_} {dp}, lấy chuyến tối sớm nhất, {qty_phrase(n)} vé")
        s.gold = [C("train_bus_tickets.search", **sa), C("train_bus_tickets.book", trip_id=t["id"], seats=n)]
    elif kind == "book_cal":
        t = min(trips, key=lambda x: x["depart"])
        s.state["calendar"] = {"events": []}
        h, m = map(int, t["depart"].split(":"))
        s.text = style(f"Đặt {qty_phrase(n)} vé chuyến sớm nhất {o} đi {d_} {dp} rồi ghi lịch giờ khởi hành cho mình")
        s.gold = [C("train_bus_tickets.search", **sa), C("train_bus_tickets.book", trip_id=t["id"], seats=n),
                  C("calendar.create_event", title=f"Đi {d_}", start=iso(day, h, m), end=iso(day, h + 1, m) if h < 23 else None)]
        if s.gold[-1]["arguments"]["end"] is None:
            del s.gold[-1]["arguments"]["end"]
    elif kind in ("cancel", "cancel_ambig"):
        t = trips[0]
        b = {"id": rid("tk"), "trip_id": t["id"], "seats": 2, "total": t["price"] * 2, "status": "confirmed"}
        t["seats_left"] -= 2
        other = trips[1]
        b2 = {"id": rid("tk"), "trip_id": other["id"], "seats": 1, "total": other["price"], "status": "confirmed"}
        other["seats_left"] -= 1
        s.state["train_bus_tickets"]["bookings"] = [b, b2]
        if kind == "cancel":
            other["destination"] = R.choice([x for x in ("Vinh", "Quy Nhơn", "Cần Thơ") if x != d_])
            s.text = style(f"Huỷ vé đi {d_} mình đã đặt")
            s.gold = [C("train_bus_tickets.my_bookings"), C("train_bus_tickets.cancel", booking_id=b["id"])]
        else:
            s.text = style(f"Huỷ giúp mình vé đi {d_}")
            s.gold = [C("train_bus_tickets.my_bookings"), ASK("train_bus_tickets.cancel", "booking_id")]
    elif kind == "read":
        s.text = style(f"{dp.capitalize()} có chuyến nào từ {o} đi {d_} không?")
        s.gold = [C("train_bus_tickets.search", **sa)]
    elif kind == "ask_date":
        s.text = style(f"Đặt vé từ {o} đi {d_} cho mình")
        s.gold = [ASK("train_bus_tickets.search", "date")]
    elif kind == "hist":
        s.user(style(f"Tìm vé {o} đi {d_} {dp}"))
        lst = sorted(trips, key=lambda x: x["depart"])
        s.bot("Có các chuyến: " + "; ".join(f"{x['depart']} ({'tàu' if x['type'] == 'train' else 'xe khách'} {x['operator']}) giá {vnd(x['price'])}"
                                            for x in lst) + ".", [C("train_bus_tickets.search", **sa)])
        t = lst[R.randrange(len(lst))]
        h = int(t["depart"][:2])
        s.text = style(f"Lấy chuyến {time_phrase(h, int(t['depart'][3:]))}, {qty_phrase(n)} vé")
        s.gold = [C("train_bus_tickets.book", trip_id=t["id"], seats=n)]
    else:
        s.text = style(R.choice([f"Đặt vé máy bay đi {d_} {dp}", "Đổi vé xe hôm trước sang ngày khác"]))
        s.gold = []
    return s


TRANSIT = {
    "Hà Nội": [("r32", "Tuyến 32", "bus", ["Nhổn", "Cầu Giấy", "Kim Mã", "Giáp Bát"]), ("r09", "Tuyến 09", "bus", ["Bờ Hồ", "Hàng Bài", "Bách Khoa", "Kim Liên"]),
               ("m2a", "Metro 2A", "metro", ["Cát Linh", "La Thành", "Thái Hà", "Láng", "Thượng Đình", "Hà Đông"])],
    "TP.HCM": [("m1", "Metro số 1", "metro", ["Bến Thành", "Nhà hát Thành phố", "Ba Son", "Thảo Điền", "Suối Tiên"]),
               ("r19", "Tuyến 19", "bus", ["Bến Thành", "Đại học Quốc gia", "Khu Công nghệ cao"]), ("r56", "Tuyến 56", "bus", ["Chợ Lớn", "Đại học Bách khoa", "Bến xe Miền Đông"])],
}


def gen_public_transit(idx: int) -> Spec:
    kind = ["route", "depart", "depart_route", "topup", "ask_amount", "remind", "hist_topup", "oos", "topup", "route"][idx % 10]
    city = R.choice(list(TRANSIT))
    apps = ["public_transit"] + (["reminders"] if kind == "remind" else [])
    s = Spec("public_transit", idx, apps, city=city)
    routes = [{"id": i, "name": n, "type": t, "stops": st, "fare": 7000 if t == "bus" else 15000, "duration_min": len(st) * 6,
               "headway_min": R.choice([10, 15, 20])} for i, n, t, st in TRANSIT[city]]
    deps = []
    base = s.now
    for r in routes:
        for stop in r["stops"]:
            for k in range(2):
                tm = base + dt.timedelta(minutes=R.randint(15, 40) + 30 * k)
                deps.append({"stop": stop, "route": r["id"], "time": tm.strftime("%H:%M")})
    s.state = {"public_transit": {"card_balance": R.randint(1, 30) * 5000, "routes": routes, "departures": deps, "topups": []}}
    r = R.choice(routes)
    a, b = R.sample(r["stops"], 2)
    amt = R.choice([50000, 100000, 150000, 200000])
    if kind == "route":
        s.text = style(R.choice([f"Từ {a} đi {b} thì đi tuyến nào?", f"Đi xe công cộng từ {a} tới {b} thế nào"]))
        s.gold = [C("public_transit.find_routes", origin=a, destination=b)]
    elif kind == "depart":
        s.text = style(f"Chuyến kế tiếp ở trạm {a} mấy giờ?")
        s.gold = [C("public_transit.next_departures", stop=a)]
    elif kind == "depart_route":
        num = r["name"].split()[-1] if r["type"] == "bus" else r["name"]
        s.text = style(f"{r['name']} ở trạm {a} mấy giờ có chuyến tiếp theo?")
        s.gold = [C("public_transit.next_departures", stop=a, route=num if r["type"] == "bus" else r["name"])]
    elif kind == "topup":
        s.text = style(R.choice([f"Nạp {money_phrase(amt)} vào thẻ xe buýt", f"Nạp thêm {money_phrase(amt)} vô thẻ đi metro"]))
        s.gold = [C("public_transit.topup_card", amount=amt)]
    elif kind == "ask_amount":
        s.text = style("Nạp tiền vào thẻ đi xe giùm mình")
        s.gold = [ASK("public_transit.topup_card", "amount")]
    elif kind == "remind":
        stop = a
        nxt = sorted([x for x in deps if x["stop"] == stop], key=lambda x: x["time"])[0]
        h, m = map(int, nxt["time"].split(":"))
        rem = dt.datetime(2026, 1, 1, h, m) - dt.timedelta(minutes=10)
        s.state["reminders"] = {"reminders": []}
        s.text = style(f"Xem chuyến tiếp theo ở trạm {stop}, rồi nhắc mình ra trạm trước giờ đó mười phút")
        s.gold = [C("public_transit.next_departures", stop=stop),
                  C("reminders.create", content=f"ra trạm {stop}", time=iso(s.now.date(), rem.hour, rem.minute))]
    elif kind == "hist_topup":
        s.user(style(f"Đi từ {a} đến {b} bằng gì?"))
        s.bot(f"Bạn đi {r['name']}, lên ở {a} xuống ở {b}, giá vé {vnd(r['fare'])}.", [C("public_transit.find_routes", origin=a, destination=b)])
        s.text = style(f"Vậy nạp sẵn {money_phrase(amt)} vào thẻ cho mình")
        s.gold = [C("public_transit.topup_card", amount=amt)]
    else:
        s.text = style(R.choice(["Gọi taxi đưa mình ra ga", "Mua vé tháng xe buýt cho con mình"]))
        s.gold = []
    return s


LOTS = {
    "Hà Nội": [("Bãi xe Tràng Tiền Plaza", "24 Hai Bà Trưng, Hoàn Kiếm", "Hoàn Kiếm"), ("Bãi xe Vincom Bà Triệu", "191 Bà Triệu, Hai Bà Trưng", "Hai Bà Trưng"),
               ("Bãi xe Lotte Center", "54 Liễu Giai, Ba Đình", "Ba Đình"), ("Bãi xe Hồ Gươm", "Đinh Tiên Hoàng, Hoàn Kiếm", "Hoàn Kiếm")],
    "TP.HCM": [("Bãi xe Vincom Đồng Khởi", "72 Lê Thánh Tôn, Quận 1", "Quận 1"), ("Bãi xe chợ Bến Thành", "Lê Lai, Quận 1", "Quận 1"),
               ("Bãi xe Crescent Mall", "101 Tôn Dật Tiên, Quận 7", "Quận 7"), ("Bãi xe Landmark 81", "720A Điện Biên Phủ, Bình Thạnh", "Bình Thạnh")],
    "Đà Nẵng": [("Bãi xe cầu Rồng", "Trần Hưng Đạo, Sơn Trà", "Sơn Trà"), ("Bãi xe Vincom Ngô Quyền", "910A Ngô Quyền, Sơn Trà", "Sơn Trà"),
                ("Bãi xe chợ Hàn", "119 Trần Phú, Hải Châu", "Hải Châu")],
}


def gen_parking(idx: int) -> Spec:
    kind = ["reserve", "reserve", "reserve_until", "end", "ask_time", "ask_hours", "read", "cal", "oos", "hist", "reserve_now"][idx % 11]
    city = R.choice(list(LOTS))
    apps = ["parking"] + (["calendar"] if kind == "cal" else [])
    s = Spec("parking", idx, apps, city=city)
    lots = [{"id": rid("lot"), "name": n, "address": ad, "area": ar, "price_per_hour": R.choice([15000, 20000, 25000, 30000]),
             "available_spots": R.randint(3, 40)} for n, ad, ar in LOTS[city]]
    s.state = {"parking": {"lots": lots, "sessions": []}}
    l = lots[0]
    near = l["name"].replace("Bãi xe ", "")
    hours = R.randint(1, 4)
    today = s.now.date()
    if kind == "reserve":
        dp, d = date_phrase(s.now)
        h, m = R.choice([(8, 0), (9, 30), (14, 0), (18, 30), (19, 0)])
        if d == today and h <= s.now.hour:
            h = min(22, s.now.hour + 2)
        s.text = style(f"Đặt chỗ đỗ xe ở {near} từ {time_phrase(h, m)} {dp}, gửi {qty_phrase(hours)} tiếng")
        s.gold = [C("parking.find", near=near), C("parking.reserve", lot_id=l["id"], from_time=iso(d, h, m), hours=hours)]
    elif kind == "reserve_until":
        if s.now.hour < 18:
            day, word, h = today, "hôm nay", s.now.hour + 1
        else:
            day, word, h = today + dt.timedelta(days=1), "mai", R.choice([8, 9, 14])
        end = h + hours
        s.text = style(f"Giữ chỗ đỗ ở {near} {word} từ {time_phrase(h, 0)} tới {time_phrase(end, 0)}")
        s.gold = [C("parking.find", near=near), C("parking.reserve", lot_id=l["id"], from_time=iso(day, h, 0), hours=hours)]
    elif kind == "reserve_now":
        s.text = style(f"Đặt chỗ đỗ ở {near} từ bây giờ, {qty_phrase(hours)} tiếng")
        s.gold = [C("parking.find", near=near), C("parking.reserve", lot_id=l["id"], from_time=s.ctx["current_time"], hours=hours)]
    elif kind == "end":
        st = s.now - dt.timedelta(hours=R.randint(1, 3))
        sess = {"id": rid("park"), "lot_id": l["id"], "from_time": st.strftime("%Y-%m-%dT%H:00:00") + TZ, "hours": 3,
                "end_time": (st + dt.timedelta(hours=3)).strftime("%Y-%m-%dT%H:00:00") + TZ, "total": l["price_per_hour"] * 3, "status": "reserved"}
        l["available_spots"] -= 1
        s.state["parking"]["sessions"] = [sess]
        s.text = style(R.choice(["Mình lấy xe rồi, kết thúc phiên đỗ xe đi", f"Kết thúc phiên gửi xe ở {near} giúp mình"]))
        s.gold = [C("parking.list_sessions"), C("parking.end_session", session_id=sess["id"])]
    elif kind == "ask_time":
        dp, _d = date_phrase(s.now, allow_today=False)
        s.text = style(f"Đặt trước chỗ đỗ ở {near} cho {dp}, gửi {qty_phrase(hours)} tiếng")
        s.gold = [C("parking.find", near=near), ASK("parking.reserve", "from_time")]
    elif kind == "ask_hours":
        dp, d = date_phrase(s.now, allow_today=False)
        s.text = style(f"Đặt chỗ đỗ xe ở {near} lúc {time_phrase(9, 0)} {dp}")
        s.gold = [C("parking.find", near=near), ASK("parking.reserve", "hours")]
    elif kind == "read":
        s.text = style(f"Gần {l['area']} có bãi đỗ nào còn chỗ không?")
        s.gold = [C("parking.find", near=l["area"])]
    elif kind == "cal":
        d = today + dt.timedelta(days=R.randint(1, 5))
        h = R.choice([9, 14, 15])
        dur = R.choice([1, 2])
        ev = {"id": rid("evt"), "title": R.choice(["Họp khách hàng", "Gặp đối tác", "Khám răng"]), "start": iso(d, h, 0), "end": iso(d, h + dur, 0),
              "location": l["name"].replace("Bãi xe ", ""), "status": "confirmed"}
        s.state["calendar"] = {"events": [ev]}
        s.user(style(f"{WD[d.weekday()].capitalize()} này mình có lịch gì?"))
        s.bot(f"Bạn có {ev['title']} lúc {h} giờ đến {h + dur} giờ tại {ev['location']}.",
              [C("calendar.list_events", date_from=d.isoformat(), date_to=d.isoformat())])
        s.text = style("Đặt chỗ đỗ xe ở đó từ lúc bắt đầu tới lúc xong luôn")
        s.gold = [C("parking.find", near=ev["location"]), C("parking.reserve", lot_id=l["id"], from_time=ev["start"], hours=dur)]
    elif kind == "hist":
        s.user(style(f"Gần {near} có bãi đỗ không?"))
        s.bot(f"Có {l['name']} ở {l['address']}, {vnd(l['price_per_hour'])} một giờ, còn {l['available_spots']} chỗ.",
              [C("parking.find", near=near)])
        dp, d = date_phrase(s.now, allow_today=False)
        s.text = style(f"Đặt chỗ ở đó {time_phrase(8, 0)} {dp}, {qty_phrase(hours)} tiếng")
        s.gold = [C("parking.reserve", lot_id=l["id"], from_time=iso(d, 8, 0), hours=hours)]
    else:
        s.text = style(R.choice(["Trả phí gửi xe tháng này giùm mình", "Gọi bảo vệ bãi xe mở cổng"]))
        s.gold = []
    return s


TRANSL = [("Cảm ơn bạn rất nhiều", {"en": "Thank you very much", "ja": "本当にありがとうございます", "ko": "정말 감사합니다", "zh": "非常感谢你", "fr": "Merci beaucoup"}),
          ("Chúc mừng sinh nhật", {"en": "Happy birthday", "ja": "お誕生日おめでとう", "ko": "생일 축하해요", "zh": "生日快乐", "fr": "Joyeux anniversaire"}),
          ("Nhà vệ sinh ở đâu", {"en": "Where is the restroom", "ja": "トイレはどこですか", "ko": "화장실이 어디예요", "zh": "洗手间在哪里", "fr": "Où sont les toilettes"}),
          ("Hẹn gặp lại bạn ngày mai", {"en": "See you tomorrow", "ja": "また明日会いましょう", "ko": "내일 봐요", "zh": "明天见", "fr": "À demain"}),
          ("Món này giá bao nhiêu", {"en": "How much is this dish", "ja": "この料理はいくらですか", "ko": "이 요리는 얼마예요", "zh": "这道菜多少钱", "fr": "Combien coûte ce plat"}),
          ("Tôi bị dị ứng hải sản", {"en": "I am allergic to seafood", "ja": "私は海鮮アレルギーです", "ko": "해산물 알레르기가 있어요", "zh": "我对海鲜过敏", "fr": "Je suis allergique aux fruits de mer"})]
LANGS = {"en": ["tiếng Anh"], "ja": ["tiếng Nhật"], "ko": ["tiếng Hàn"], "zh": ["tiếng Trung", "tiếng Hoa"], "fr": ["tiếng Pháp"]}


def gen_translator(idx: int) -> Spec:
    kind = ["read", "read", "send_chat", "note", "ask_lang", "oos", "read", "send_chat", "hist_send"][idx % 9]
    apps = ["translator"] + (["chat_ott"] if kind in ("send_chat", "hist_send") else []) + (["notes"] if kind == "note" else [])
    s = Spec("translator", idx, apps)
    dictionary = [{"text": vi, "to_lang": lg, "translation": tr} for vi, m in TRANSL for lg, tr in m.items()]
    s.state = {"translator": {"dictionary": dictionary}}
    vi, m = R.choice(TRANSL)
    lg = R.choice(list(m))
    lname = R.choice(LANGS[lg])
    if kind == "read":
        s.text = style(R.choice([f"Dịch câu {vi.lower()} sang {lname}", f"{vi} tiếng {lname.split()[-1]} nói sao?"]))
        s.gold = [C("translator.translate", text=vi, to_lang=lg)]
    elif kind in ("send_chat", "hist_send"):
        who = R.choice(["Minh", "Lan", "Hương", "Tuấn"])
        s.state["chat_ott"] = chats_state([who, "Nam", "Vy"])
        chat = find_by(s.state["chat_ott"]["chats"], "name", who)
        if kind == "send_chat":
            s.text = style(f"Dịch câu {vi.lower()} sang {lname} rồi gửi Zalo cho {who}")
            s.gold = [C("translator.translate", text=vi, to_lang=lg), C("chat_ott.list_chats"), C("chat_ott.send_message", chat_id=chat["id"], content=m[lg])]
        else:
            s.user(style(f"Dịch câu {vi.lower()} sang {lname}"))
            s.bot(f"Câu đó trong {lname} là: {m[lg]}", [C("translator.translate", text=vi, to_lang=lg)])
            s.text = style(f"Gửi câu đó qua Zalo cho {who} giùm mình")
            s.gold = [C("chat_ott.list_chats"), C("chat_ott.send_message", chat_id=chat["id"], content=m[lg])]
    elif kind == "note":
        s.state["notes"] = {"notes": []}
        s.text = style(f"Dịch câu {vi.lower()} sang {lname} rồi lưu vào ghi chú")
        s.gold = [C("translator.translate", text=vi, to_lang=lg), C("notes.create", content=f"{vi}: {m[lg]}")]
    elif kind == "ask_lang":
        s.text = style(f"Dịch giúp mình câu {vi.lower()}")
        s.gold = [ASK("translator.translate", "to_lang")]
    else:
        s.text = style(R.choice(["Dịch giùm cái biển hiệu trong ảnh mình vừa chụp", "Phiên dịch trực tiếp cuộc gọi này sang tiếng Anh"]))
        s.gold = []
    return s


def chit_chat(s: Spec) -> list[dict]:
    """An unrelated, tool-free earlier exchange (66% of public samples carry history): teaches the model that only the
    LAST request is acted on, and that earlier turns without tool calls change nothing."""
    d = s.now.date()
    pairs = [("Hôm nay thứ mấy vậy?", f"Hôm nay là {WD[d.weekday()]}, ngày {d.day} tháng {d.month}."),
             ("Mấy giờ rồi em?", f"Bây giờ là {s.now.hour} giờ {s.now.minute:02d} phút."),
             ("Cảm ơn nha.", "Dạ không có gì ạ."),
             ("Chào buổi sáng!" if s.now.hour < 11 else "Chào em!", "Chào bạn, mình có thể giúp gì?"),
             ("Bạn làm được những gì?", "Mình có thể giúp bạn thao tác trên các ứng dụng đã cài đặt."),
             ("Hôm nay ngày mấy âm lịch?", "Xin lỗi, mình chưa tra được lịch âm.")]
    u, a = R.choice(pairs)
    return [{"role": "user", "audio_text": u}, {"role": "assistant", "text": a}]


GENERATORS = {"ecommerce": gen_ecommerce, "grocery": gen_grocery, "pantry": gen_pantry, "recipes": gen_recipes, "habit_tracker": gen_habit_tracker,
              "stocks": gen_stocks, "event_tickets": gen_event_tickets, "train_bus_tickets": gen_train_bus_tickets,
              "public_transit": gen_public_transit, "parking": gen_parking, "translator": gen_translator}


def main():
    global R
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="synth_specs")
    ap.add_argument("--n", type=int, default=40, help="samples per app")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--apps", nargs="*", default=list(GENERATORS))
    ap.add_argument("--chitchat", type=float, default=0.45, help="share of history-less samples that get an unrelated earlier exchange")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for app in a.apps:
        R = random.Random(f"{a.seed}-{app}")
        with open(out / f"gen_{app}.jsonl", "w", encoding="utf-8") as f:
            for i in range(1, a.n + 1):
                sp = GENERATORS[app](i)
                if not sp.history and R.random() < a.chitchat:
                    sp.history = chit_chat(sp)
                f.write(json.dumps(sp.dump(), ensure_ascii=False) + "\n")
        print(f"{app}: {a.n} specs -> {out / f'gen_{app}.jsonl'}")


if __name__ == "__main__":
    main()
