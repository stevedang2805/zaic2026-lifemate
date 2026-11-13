"""Helpers for hand-written synthetic specs (format of lifemate/synth_build.py).

Every scenario is written by hand (utterance, state, gold); these helpers only keep dates/ISO strings consistent with
current_time so a spoken "thứ sáu tuần sau" and the gold timestamp can never disagree.
"""
from __future__ import annotations

import datetime as dt
import json

TZ = "+07:00"
WD = ["thứ hai", "thứ ba", "thứ tư", "thứ năm", "thứ sáu", "thứ bảy", "chủ nhật"]

CITIES = {
    "Hà Nội": (21.0285, 105.8542), "TP.HCM": (10.7769, 106.7009), "Đà Nẵng": (16.0544, 108.2022),
    "Huế": (16.4637, 107.5909), "Cần Thơ": (10.0452, 105.7469), "Hải Phòng": (20.8449, 106.6881),
}

PROFILES = [
    {"name": "Minh Anh", "home_address": "45 Lê Thánh Tôn, Quận 1, TP.HCM", "work_address": "12 Nguyễn Huệ, Quận 1, TP.HCM", "city": "TP.HCM"},
    {"name": "Quốc Bảo", "home_address": "27 Láng Hạ, Đống Đa, Hà Nội", "work_address": "Tòa nhà Keangnam, Phạm Hùng, Hà Nội", "city": "Hà Nội"},
    {"name": "Thu Hà", "home_address": "88 Trần Phú, Hải Châu, Đà Nẵng", "work_address": "Khu công nghệ cao Đà Nẵng, Hoà Liên", "city": "Đà Nẵng"},
    {"name": "Hoàng Nam", "home_address": "15 Nguyễn Sinh Cung, TP Huế", "work_address": "Đại học Huế, 3 Lê Lợi", "city": "Huế"},
    {"name": "Ngọc Lan", "home_address": "120 Nguyễn Văn Cừ, Ninh Kiều, Cần Thơ", "work_address": "Bệnh viện Đa khoa Trung ương Cần Thơ", "city": "Cần Thơ"},
    {"name": "Đức Thịnh", "home_address": "9 Hoàng Hoa Thám, Ba Đình, Hà Nội", "work_address": "FPT Tower, 10 Phạm Văn Bạch, Hà Nội", "city": "Hà Nội"},
    {"name": "Phương Linh", "home_address": "212 Võ Văn Tần, Quận 3, TP.HCM", "work_address": "Bitexco, 2 Hải Triều, Quận 1, TP.HCM", "city": "TP.HCM"},
    {"name": "Văn Toàn", "home_address": "56 Lạch Tray, Ngô Quyền, Hải Phòng", "work_address": "Cảng Hải Phòng, 8A Trần Phú", "city": "Hải Phòng"},
]


def C(_tool, **args):
    return {"name": _tool, "arguments": args}


def ASK(tool, param):
    return C("sys.ask_missing_info", tool_name=tool, params=[param])


class Sc:
    """One scenario. now = 'YYYY-MM-DDTHH:MM' (local). apps = installed app ids (first = main app)."""
    counter: dict[str, int] = {}

    def __init__(self, app: str, now: str, apps: list[str] | tuple[str, ...], profile: int = 0):
        Sc.counter[app] = Sc.counter.get(app, 0) + 1
        self.app = app
        self.id = f"claude_{app}_{Sc.counter[app]:04d}"
        self.now = dt.datetime.fromisoformat(now)
        self.apps = list(apps)
        self.prof = PROFILES[profile % len(PROFILES)]
        self.city = self.prof["city"]
        self.state: dict = {a: {} for a in self.apps}
        self.history: list = []
        self.text = ""
        self.gold: list = []

    # ---- time helpers (relative to current_time) ---------------------------------------------------------------
    def t(self, dd: int, h: int, m: int = 0) -> str:
        d = self.now.date() + dt.timedelta(days=dd)
        return f"{d.isoformat()}T{h:02d}:{m:02d}:00{TZ}"

    def d(self, dd: int) -> str:
        return (self.now.date() + dt.timedelta(days=dd)).isoformat()

    def wd(self, dd: int) -> str:
        return WD[(self.now.date() + dt.timedelta(days=dd)).weekday()]

    def dm(self, dd: int) -> str:
        d = self.now.date() + dt.timedelta(days=dd)
        return f"{d.day}/{d.month}"

    def next_wd(self, weekday: int, same_week: bool = False, next_week: bool = False) -> int:
        """day offset of 'thứ X' (next occurrence after today), 'thứ X này' (this Mon-Sun week) or 'thứ X tuần sau'."""
        today = self.now.date()
        mon = today - dt.timedelta(days=today.weekday())
        if same_week:
            return (mon + dt.timedelta(days=weekday) - today).days
        if next_week:
            return (mon + dt.timedelta(days=7 + weekday) - today).days
        k = (weekday - today.weekday()) % 7
        return 7 if k == 0 else k

    def now_iso(self) -> str:
        return self.now.strftime("%Y-%m-%dT%H:%M:%S") + TZ

    # ---- dialogue ---------------------------------------------------------------------------------------------
    def user(self, text):
        self.history.append({"role": "user", "audio_text": text})
        return self

    def bot(self, text, *calls):
        h = {"role": "assistant", "text": text}
        if calls:
            h["tool_calls"] = list(calls)
        self.history.append(h)
        return self

    def say(self, text, *gold):
        self.text = text
        self.gold = list(gold)
        return self

    # ---- output -----------------------------------------------------------------------------------------------
    def spec(self) -> dict:
        lat, lng = CITIES[self.city]
        return {
            "id": self.id,
            "context": {"current_time": self.now_iso(), "timezone": "Asia/Ho_Chi_Minh",
                        "location": {"lat": lat, "lng": lng}, "user_profile": dict(self.prof),
                        "installed_apps": self.apps},
            "state": self.state, "history": self.history, "audio_text": self.text, "gold": self.gold,
        }


# ---- reusable mix-app states ------------------------------------------------------------------------------------
def contacts(*people):
    """people: (id, name, relation, phone)"""
    return {"contacts": [{"id": i, "name": n, "relation": r, "phone": p} for i, n, r, p in people]}


def chats(*rows):
    """rows: (id, name, type)"""
    return {"chats": [{"id": i, "name": n, "type": t, "members": [n] if t == "direct" else [], "messages": []} for i, n, t in rows]}


def reminders(*rows):
    """rows: (id, content, time, done)"""
    return {"reminders": [{"id": i, "content": c, "time": t, "repeat": "once", "done": d} for i, c, t, d in rows]}


def events(*rows):
    """rows: (id, title, start, end, location)"""
    return {"events": [{"id": i, "title": t, "start": s, "end": e, "location": l, "status": "confirmed"} for i, t, s, e, l in rows]}


def notes(*rows):
    return {"notes": [{"id": i, "title": t, "content": c} for i, t, c in rows]}


def tasks(*rows):
    """rows: (id, title, due, priority, done)"""
    return {"tasks": [{"id": i, "title": t, "due": d, "priority": p, "done": x} for i, t, d, p, x in rows]}


def alarms(*rows):
    """rows: (id, time, label, repeat, enabled)"""
    return {"alarms": [{"id": i, "time": t, "label": l, "repeat": r, "enabled": e} for i, t, l, r, e in rows]}


def ewallet(balance):
    return {"balance": balance, "transactions": []}


def shopping(*rows):
    """rows: (id, name, quantity, checked)"""
    return {"items": [{"id": i, "name": n, "quantity": q, "checked": c} for i, n, q, c in rows]}


def weather(city, forecast):
    """forecast: {date: (condition, temp_min, temp_max, rain_prob)}"""
    return {"current": [{"location": city, "condition": "có mây", "temp_c": 29, "humidity": 70}],
            "forecast": [{"location": city, "date": d, "condition": c, "temp_min": a, "temp_max": b, "rain_prob": r}
                         for d, (c, a, b, r) in forecast.items()]}


def dump(specs, path):
    with open(path, "w", encoding="utf-8") as f:
        for s in specs:
            f.write(json.dumps(s.spec(), ensure_ascii=False) + "\n")
    return len(specs)
