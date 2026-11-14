#!/usr/bin/env python3
"""
SubFinder  (v6)
--------------------
Telegram subtitle bot — bilingual (বাংলা / English), library + online sources.

USER   : language system, smart/fuzzy search, favorites, history, XP + levels + streak,
         daily quota, invite & earn, redeem codes, premium, feedback, request tracking,
         subtitle tools (sync shift, SRT->VTT), trending, leaderboard, settings.
ADMIN  : /admin control center — live dashboard, analytics, user manager (ban / premium /
         credits / DM), broadcast (any media, audience filter, preview), redeem-code
         generator, library manager, request manager (auto-notify), API sources,
         channel gate, bot settings, multi-admin, backup & export.

Files: token.txt (or BOT_TOKEN env), config.json {"admin_id": 123},
       settings.json / users.json / stats.json / requests.json (auto-created).
"""

import hashlib
import html
import io
import json
import os
import re
import secrets
import shutil
import sys
import threading
import time
import zipfile
from collections import Counter, OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher

try:
    import requests
except ImportError:
    print("requests lage:  pip install requests")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n import ADD_RANKS, LANGS, T  # noqa: E402
from opensubs import OpenSubs  # noqa: E402
from subdl import SubDL  # noqa: E402
import subtools  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
CACHE_DIR = os.path.join(BASE, "cache")
TOOLS_DIR = os.path.join(CACHE_DIR, "tools")
CATALOG_FILE = os.path.join(BASE, "catalog.json")
CONFIG_FILE = os.path.join(BASE, "config.json")
SETTINGS_FILE = os.path.join(BASE, "settings.json")
USERS_FILE = os.path.join(BASE, "users.json")
STATS_FILE = os.path.join(BASE, "stats.json")
REQS_FILE = os.path.join(BASE, "requests.json")
OLD_LOG_FILE = os.path.join(BASE, "search-log.txt")

PAGE_SIZE = 8
START_TIME = time.time()
LOCK = threading.RLock()


# ================================================================ storage
def load_json(path, default):
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            pass
    return default


def save_json(path, obj):
    for _ in range(3):
        try:
            with LOCK:
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(obj, f, ensure_ascii=False, indent=1)
                os.replace(tmp, path)
            return
        except RuntimeError:      # dict changed size during iteration
            time.sleep(0.05)
        except Exception as e:
            print("save error:", path, e)
            return


def load_token():
    tok = os.environ.get("BOT_TOKEN", "").strip()
    if tok:
        return tok
    p = os.path.join(BASE, "token.txt")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().strip()
    return ""


TOKEN = load_token()
API = f"https://api.telegram.org/bot{TOKEN}"

def _env_bootstrap():
    """Cloud (Render) mode: env var theke config/settings/library sajano (file na thakle)."""
    try:
        if os.environ.get("ADMIN_ID") and not os.path.exists(CONFIG_FILE):
            save_json(CONFIG_FILE, {"admin_id": int(os.environ["ADMIN_ID"])})
        if os.environ.get("OS_API_KEY") and not os.path.exists(SETTINGS_FILE):
            save_json(SETTINGS_FILE, {"sources": [{"name": "opensubtitles", "type": "opensubtitles",
                        "api_key": os.environ["OS_API_KEY"],
                        "username": os.environ.get("OS_USERNAME", ""),
                        "password": os.environ.get("OS_PASSWORD", ""), "enabled": True}]})
        lib = os.path.join(BASE, "library.zip")
        if os.path.exists(lib) and not os.path.isdir(os.path.join(BASE, "data")):
            import zipfile
            with zipfile.ZipFile(lib) as z:
                z.extractall(BASE)
        # Season pack na thakle episode file gula diye baniye neya (repo te binary rakha lage na)
        import zipfile as _zf
        _dd = os.path.join(BASE, "data")
        if os.path.isdir(_dd):
            for _folder in os.listdir(_dd):
                _fd = os.path.join(_dd, _folder)
                if not os.path.isdir(_fd):
                    continue
                _srts = [f for f in sorted(os.listdir(_fd)) if f.lower().endswith(".srt")]
                _has_zip = any(f.lower().endswith(".zip") for f in os.listdir(_fd))
                if _srts and not _has_zip:
                    with _zf.ZipFile(os.path.join(_fd, "full-pack.zip"), "w", _zf.ZIP_DEFLATED) as _z:
                        for _f in _srts:
                            _z.write(os.path.join(_fd, _f), _f)
    except Exception as e:
        print("env bootstrap error:", e)


_env_bootstrap()
CFG = load_json(CONFIG_FILE, {})
ADMIN_ID = CFG.get("admin_id")
BOT_USERNAME = ""
SESSION = requests.Session()

DEFAULT_SETTINGS = {
    "join_gate": False, "gate_all_downloads": False, "channels": [], "sources": [],
    "admins": [], "daily_limit": 10, "referral_bonus": 3,
    "maintenance": False, "online_premium_only": False, "codes": {},
}
SETTINGS = {**DEFAULT_SETTINGS, **load_json(SETTINGS_FILE, {})}

if not SETTINGS["sources"] and CFG.get("opensubtitles", {}).get("api_key"):
    oc = CFG["opensubtitles"]
    SETTINGS["sources"].append({"name": "opensubtitles", "type": "opensubtitles",
                                "api_key": oc.get("api_key", ""), "username": oc.get("username", ""),
                                "password": oc.get("password", ""), "enabled": True})
    save_json(SETTINGS_FILE, SETTINGS)

USERS = load_json(USERS_FILE, {})
STATS = load_json(STATS_FILE, {})
STATS.setdefault("days", {}); STATS.setdefault("queries", {}); STATS.setdefault("dl_titles", {})
REQS = load_json(REQS_FILE, [])

_dirty = set()
FILES = {"users": (USERS_FILE, USERS), "stats": (STATS_FILE, STATS), "reqs": (REQS_FILE, REQS)}


def mark(name):
    _dirty.add(name)


def flush():
    for name in list(_dirty):
        _dirty.discard(name)
        path, obj = FILES[name]
        save_json(path, obj)


def flusher():
    while True:
        time.sleep(3)
        try:
            for d in sorted(STATS["days"])[:-30]:
                STATS["days"].pop(d, None)
            if len(STATS["queries"]) > 1500:
                STATS["queries"] = dict(Counter(STATS["queries"]).most_common(600))
            flush()
        except Exception as e:
            print("flush error:", e)


def save_settings():
    save_json(SETTINGS_FILE, SETTINGS)


# ================================================================ sources
SOURCE_OBJS = {}


def rebuild_sources():
    SOURCE_OBJS.clear()
    for s in SETTINGS["sources"]:
        if not s.get("enabled", True):
            continue
        try:
            if s["type"] == "opensubtitles":
                SOURCE_OBJS[s["name"]] = OpenSubs(s["api_key"], s.get("username", ""), s.get("password", ""))
            elif s["type"] == "subdl":
                SOURCE_OBJS[s["name"]] = SubDL(s["api_key"])
        except Exception as e:
            print("source build fail:", s.get("name"), e)


rebuild_sources()


# ================================================================ helpers / users / stats
def esc(s):
    return html.escape(str(s), quote=False)


def today():
    return time.strftime("%Y-%m-%d")


def fdate(ts):
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def B(text, data):
    return {"text": text, "callback_data": data}


def kb(*rows):
    return {"inline_keyboard": [list(r) for r in rows if r]}


def bar(v, total, w=10):
    if total <= 0:
        return "▱" * w
    f = int(round(w * min(max(v, 0), total) / total))
    return "▰" * f + "▱" * (w - f)


def is_owner(uid):
    return ADMIN_ID is not None and uid == ADMIN_ID


def is_admin(uid):
    return is_owner(uid) or uid in SETTINGS.get("admins", [])


def admin_ids():
    ids = set(SETTINGS.get("admins", []))
    if ADMIN_ID is not None:
        ids.add(ADMIN_ID)
    return ids


USER_DEFAULTS = {
    "name": "", "username": "", "lang": None, "tg_lang": "en", "searches": 0, "downloads": 0,
    "first_seen": "", "last_seen": "", "last_day": "", "streak": 0, "xp": 0, "banned": False,
    "premium_until": 0, "bonus": 0, "used_day": "", "used_today": 0, "favs": [], "history": [],
    "ref_by": None, "refs": 0, "notify": True, "blocked": False,
}


def day_stats():
    with LOCK:
        return STATS["days"].setdefault(today(), {"searches": 0, "downloads": 0, "new": 0, "active": []})


def bump(field, n=1):
    d = day_stats()
    d[field] = d.get(field, 0) + n
    mark("stats")


def add_xp(rec, n):
    rec["xp"] = rec.get("xp", 0) + n


def touch_user(u):
    uid = str(u["id"])
    now = today()
    with LOCK:
        rec = USERS.get(uid)
        new = rec is None
        if new:
            rec = {}
            USERS[uid] = rec
        for k, v in USER_DEFAULTS.items():
            rec.setdefault(k, list(v) if isinstance(v, list) else v)
        rec["name"] = u.get("first_name", "") or rec["name"]
        rec["username"] = u.get("username", "") or ""
        if new:
            rec["first_seen"] = now
            rec["tg_lang"] = "bn" if str(u.get("language_code", "")).startswith("bn") else "en"
            bump("new")
        if rec["last_day"] != now:
            yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
            rec["streak"] = rec["streak"] + 1 if rec["last_day"] == yesterday else 1
            if not new:
                add_xp(rec, 2)
            rec["last_day"] = now
        rec["last_seen"] = now
        d = day_stats()
        if uid not in d["active"]:
            d["active"].append(uid)
        mark("users")
    return rec, new


def ulang(uid):
    rec = USERS.get(str(uid))
    if rec:
        return rec.get("lang") or rec.get("tg_lang") or "en"
    return "en"


def t(_u, _k, **kw):
    return T(ulang(_u), _k, **kw)


def level_info(xp):
    lvl = int((xp / 25) ** 0.5) + 1
    cur, nxt = 25 * (lvl - 1) ** 2, 25 * lvl ** 2
    rank = ADD_RANKS[min(lvl - 1, len(ADD_RANKS) - 1)]
    return lvl, cur, nxt, rank


def is_premium(uid):
    rec = USERS.get(str(uid))
    return bool(rec and rec.get("premium_until", 0) > time.time())


def has_perks(uid):
    return is_admin(uid) or is_premium(uid)


def grant_premium(rec, days):
    base = max(time.time(), rec.get("premium_until", 0))
    rec["premium_until"] = base + days * 86400
    mark("users")
    return fdate(rec["premium_until"])


def fmt_uptime():
    s = int(time.time() - START_TIME)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, _ = divmod(s, 60)
    return f"{d}d {h}h {m}m" if d else f"{h}h {m}m"


# ================================================================ telegram helpers
def api_post(method, data=None, files=None, timeout=60):
    for attempt in range(2):
        try:
            r = SESSION.post(f"{API}/{method}", data=data or {}, files=files, timeout=timeout)
            j = r.json()
            if not j.get("ok") and j.get("error_code") == 429 and attempt == 0:
                time.sleep(min(j.get("parameters", {}).get("retry_after", 2), 10))
                continue
            return j
        except Exception as e:
            print("API error:", method, e)
            return {}
    return {}


def send_message(chat_id, text, markup=None):
    data = {"chat_id": chat_id, "text": text[:4000], "parse_mode": "HTML",
            "disable_web_page_preview": True}
    if markup:
        data["reply_markup"] = json.dumps(markup)
    return api_post("sendMessage", data)


def edit_message(chat_id, message_id, text, markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text[:4000],
            "parse_mode": "HTML", "disable_web_page_preview": True}
    if markup:
        data["reply_markup"] = json.dumps(markup)
    return api_post("editMessageText", data)


def edit_markup(chat_id, message_id, markup):
    return api_post("editMessageReplyMarkup", {"chat_id": chat_id, "message_id": message_id,
                                               "reply_markup": json.dumps(markup)})


def show(chat_id, text, markup=None, mid=None):
    """mid thakle message edit kore (smooth menu), na hole notun message."""
    if mid:
        r = edit_message(chat_id, mid, text, markup)
        if r.get("ok") or "not modified" in str(r.get("description", "")):
            return r
    return send_message(chat_id, text, markup)


def send_document(chat_id, path, caption, markup=None):
    data = {"chat_id": chat_id, "caption": caption[:1000], "parse_mode": "HTML"}
    if markup:
        data["reply_markup"] = json.dumps(markup)
    with open(path, "rb") as f:
        return api_post("sendDocument", data=data,
                        files={"document": (os.path.basename(path), f)}, timeout=120)


def answer_callback(cb_id, text="", alert=False):
    return api_post("answerCallbackQuery", {"callback_query_id": cb_id, "text": text,
                                            "show_alert": "true" if alert else "false"})


def chat_action(chat_id, action="typing"):
    api_post("sendChatAction", {"chat_id": chat_id, "action": action}, timeout=10)


def download_tg_file(file_id):
    r = api_post("getFile", {"file_id": file_id})
    fp = r.get("result", {}).get("file_path")
    if not fp:
        return None
    resp = SESSION.get(f"https://api.telegram.org/file/bot{TOKEN}/{fp}", timeout=120)
    return resp.content if resp.status_code == 200 else None


# ================================================================ keyboards / menus
def reply_kb(uid):
    return {"keyboard": [
        [t(uid, "btn_search"), t(uid, "btn_library")],
        [t(uid, "btn_trending"), t(uid, "btn_favs")],
        [t(uid, "btn_profile"), t(uid, "btn_premium")],
        [t(uid, "btn_request"), t(uid, "btn_settings")]],
        "resize_keyboard": True, "is_persistent": True}


LABELS = {}
for _lg in LANGS:
    for _key, _act in (("btn_search", "search"), ("btn_library", "library"), ("btn_trending", "trending"),
                       ("btn_favs", "favs"), ("btn_profile", "profile"), ("btn_premium", "premium"),
                       ("btn_request", "request"), ("btn_settings", "settings")):
        LABELS[T(_lg, _key)] = _act


def main_menu_kb(uid):
    return kb([B(t(uid, "btn_library"), "mn:library"), B(t(uid, "btn_trending"), "mn:trending")],
              [B(t(uid, "btn_favs"), "mn:favs"), B(t(uid, "btn_history"), "mn:history")],
              [B(t(uid, "btn_profile"), "mn:profile"), B(t(uid, "btn_invite"), "mn:invite")],
              [B(t(uid, "btn_premium"), "mn:premium"), B(t(uid, "btn_settings"), "mn:settings")],
              [B(t(uid, "btn_help"), "mn:help")])


def home_row(uid):
    return [B(t(uid, "btn_home"), "mn:home")]


def lang_picker_kb(suffix=""):
    return kb([B(name, f"lg:{code}{suffix}") for code, name in LANGS.items()])


# ================================================================ catalog + search
def norm(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")
    return s or "subtitle"


def load_catalog():
    meta = load_json(CATALOG_FILE, {})
    catalog = {}
    if not os.path.isdir(DATA_DIR):
        return catalog
    for folder in sorted(os.listdir(DATA_DIR)):
        fdir = os.path.join(DATA_DIR, folder)
        if not os.path.isdir(fdir):
            continue
        episodes, zip_path = {}, None
        for fn in sorted(os.listdir(fdir)):
            m = re.search(r"e(\d+)", fn.lower())
            if fn.lower().endswith(".srt") and m:
                episodes[int(m.group(1))] = os.path.join(fdir, fn)
            elif fn.lower().endswith(".zip"):
                zip_path = os.path.join(fdir, fn)
        info = meta.get(folder, {})
        catalog[folder] = {
            "title": info.get("title", folder.replace("-", " ").title()),
            "year": info.get("year", ""),
            "aliases": [a.lower() for a in info.get("aliases", [])],
            "note": info.get("note", ""),
            "episodes": episodes, "zip": zip_path,
        }
    return catalog


CATALOG = load_catalog()
LAST_QUERY, CTX, PENDING = {}, {}, {}
ADMIN_FLOW, UFLOW = {}, {}
TOOLS = OrderedDict()
JOIN_CACHE = {}
LAST_MSG, LAST_FB = {}, {}
CHAT_LOCKS = defaultdict(threading.Lock)


def parse_query(raw):
    q = norm(raw)
    season = episode = None
    m = re.search(r"\bs(\d{1,2})\s*e(\d{1,3})\b", q)
    if m:
        season, episode = int(m.group(1)), int(m.group(2))
        q = norm(q[: m.start()] + " " + q[m.end():])
    else:
        m = re.search(r"\bseason\s*(\d{1,2})\b", q)
        if m:
            season = int(m.group(1)); q = norm(q[: m.start()] + " " + q[m.end():])
        m = re.search(r"\b(?:ep|episode|e)\s*[- ]?\s*(\d{1,3})\b", q)
        if m:
            episode = int(m.group(1)); q = norm(q[: m.start()] + " " + q[m.end():])
        elif re.search(r"\b\d{1,3}\s*$", q) and len(q) > 2:
            m2 = re.search(r"\b(\d{1,3})\s*$", q)
            episode = int(m2.group(1)); q = norm(q[: m2.start()])
    return q, season, episode


def _names(aid, a):
    return [norm(a["title"])] + a["aliases"] + [aid.replace("-", " ")]


def search_local(q):
    """-> (aid list, fuzzy?)  exact/substring -> token match -> fuzzy (typo tolerant)"""
    hits = [aid for aid, a in CATALOG.items()
            if not q or any(q in n or n.startswith(q) for n in _names(aid, a))]
    if hits:
        return hits, False
    toks = q.split()
    hits = [aid for aid, a in CATALOG.items()
            if toks and all(any(tk in n for n in _names(aid, a)) for tk in toks)]
    if hits:
        return hits, False
    scored = []
    for aid, a in CATALOG.items():
        best = 0.0
        for n in _names(aid, a):
            best = max(best, SequenceMatcher(None, q, n).ratio())
            for w in n.split():
                best = max(best, SequenceMatcher(None, q, w).ratio())
        if best >= 0.62:
            scored.append((best, aid))
    scored.sort(reverse=True)
    return [aid for _, aid in scored[:3]], True


# ================================================================ quota / gate / access
def quota_take(uid):
    """-> 'free' | 'day' | 'bonus' | False"""
    rec = USERS[str(uid)]
    if has_perks(uid):
        return "free"
    if rec["used_day"] != today():
        rec["used_day"], rec["used_today"] = today(), 0
    limit = SETTINGS["daily_limit"]
    if limit <= 0:
        return "free"
    if rec["used_today"] < limit:
        rec["used_today"] += 1; mark("users"); return "day"
    if rec["bonus"] > 0:
        rec["bonus"] -= 1; mark("users"); return "bonus"
    return False


def quota_refund(uid, kind):
    rec = USERS[str(uid)]
    if kind == "day":
        rec["used_today"] = max(0, rec["used_today"] - 1)
    elif kind == "bonus":
        rec["bonus"] += 1
    mark("users")


def quota_text(uid):
    rec = USERS[str(uid)]
    if has_perks(uid) or SETTINGS["daily_limit"] <= 0:
        return t(uid, "unlimited")
    used = rec["used_today"] if rec["used_day"] == today() else 0
    return f"{used}/{SETTINGS['daily_limit']}"


def member_of(uid, channel, fresh=False):
    key = (uid, channel)
    c = JOIN_CACHE.get(key)
    if c and not fresh and time.time() - c[1] < 60:
        return c[0]
    r = api_post("getChatMember", {"chat_id": channel, "user_id": uid})
    ok = r.get("result", {}).get("status", "") in ("member", "administrator", "creator")
    JOIN_CACHE[key] = (ok, time.time())
    return ok


def joined_all(uid, fresh=False):
    chans = SETTINGS.get("channels", [])
    return all(member_of(uid, c, fresh) for c in chans) if chans else True


def gate_active(feature):
    if not SETTINGS.get("join_gate") or not SETTINGS.get("channels"):
        return False
    return feature != "file" or SETTINGS.get("gate_all_downloads")


def gate_kb(uid):
    rows = [[{"text": f"📢 {c}", "url": f"https://t.me/{c.lstrip('@')}"}] for c in SETTINGS["channels"]]
    rows.append([B(t(uid, "join_check"), "checkjoin")])
    return {"inline_keyboard": rows}


def require_access(chat_id, uid, feature="file", pending=None):
    if has_perks(uid):
        return True
    if feature == "online" and SETTINGS.get("online_premium_only"):
        send_message(chat_id, t(uid, "premium_locked"), kb([B("⭐ Premium", "mn:premium")]))
        return False
    if gate_active(feature) and not joined_all(uid):
        if pending:
            PENDING[uid] = pending
        send_message(chat_id, t(uid, "gate_prompt"), gate_kb(uid))
        return False
    return True


def gate_blocked(uid):
    """Start-flow hard gate: join_gate on + channel thakle, join na kora user samne jete parbe na."""
    if not SETTINGS.get("join_gate") or not SETTINGS.get("channels"):
        return False
    if is_admin(uid) or has_perks(uid):
        return False
    return not joined_all(uid)


def show_gate(chat_id, uid):
    send_message(chat_id, t(uid, "gate_prompt"), gate_kb(uid))


# ================================================================ delivery + tools
def tools_kb(uid, path):
    if not path.lower().endswith(".srt"):
        return None
    tok = hashlib.md5(path.encode()).hexdigest()[:10]
    TOOLS[tok] = path
    while len(TOOLS) > 800:
        TOOLS.popitem(last=False)
    return kb([B("◀◀ -5s", f"tl:{tok}:m5"), B("◀ -1s", f"tl:{tok}:m1"),
               B("+1s ▶", f"tl:{tok}:p1"), B("+5s ▶▶", f"tl:{tok}:p5")],
              [B("-0.5s", f"tl:{tok}:m05"), B("+0.5s", f"tl:{tok}:p05"),
               B(t(uid, "tool_vtt"), f"tl:{tok}:vtt")])


def remember(rec, title, path):
    rel = os.path.relpath(path, BASE)
    rec["history"] = [h for h in rec["history"] if h["p"] != rel]
    rec["history"].insert(0, {"t": title, "p": rel, "ts": int(time.time())})
    del rec["history"][15:]


def deliver(chat_id, uid, path, caption, title, tools=True):
    kind = quota_take(uid)
    if kind is False:
        limit = SETTINGS["daily_limit"]
        send_message(chat_id, t(uid, "quota_hit", used=limit, limit=limit),
                     kb([B(t(uid, "btn_invite"), "mn:invite"), B("🎟 Redeem", "redeem")],
                        [B("⭐ Premium", "mn:premium")]))
        return False
    chat_action(chat_id, "upload_document")
    r = send_document(chat_id, path, caption, tools_kb(uid, path) if tools else None)
    if not r.get("ok"):
        quota_refund(uid, kind)
        send_message(chat_id, t(uid, "dl_fail", err=esc(r.get("description", ""))))
        return False
    rec = USERS[str(uid)]
    rec["downloads"] += 1
    add_xp(rec, 3)
    remember(rec, title, path)
    bump("downloads")
    STATS["dl_titles"][title] = STATS["dl_titles"].get(title, 0) + 1
    mark("users"); mark("stats")
    return True


def run_tool(chat_id, uid, tok, op):
    path = TOOLS.get(tok)
    if not path or not os.path.exists(path):
        return False
    out, label = subtools.make_variant(path, TOOLS_DIR, op)
    title = os.path.splitext(os.path.basename(path))[0]
    send_document(chat_id, out, T(ulang(uid), "caption_tool", title=esc(title), label=label),
                  tools_kb(uid, path))
    return True


# ================================================================ UI: local library
def anime_text(uid, aid):
    a = CATALOG[aid]
    eps = sorted(a["episodes"])
    yr = f" ({a['year']})" if a["year"] else ""
    rng = f" (E{eps[0]:02d}–E{eps[-1]:02d})" if eps else ""
    note = f"\n{esc(a['note'])}" if a["note"] else ""
    return t(uid, "anime_card", title=esc(a["title"]), yr=yr, n=len(eps), rng=rng, note=note)


def episode_keyboard(uid, aid):
    a = CATALOG[aid]
    rows, row = [], []
    for ep in sorted(a["episodes"]):
        row.append(B(f"E{ep:02d}", f"ep:{aid}:{ep}"))
        if len(row) == 6:
            rows.append(row); row = []
    if row:
        rows.append(row)
    if a["zip"]:
        rows.append([B(t(uid, "zip_btn"), f"zip:{aid}")])
    faved = aid in USERS[str(uid)]["favs"]
    rows.append([B(t(uid, "fav_del_btn" if faved else "fav_add_btn"), f"fav:{aid}")])
    return {"inline_keyboard": rows}


def online_row(uid):
    return [B(t(uid, "online_btn"), "online")]


def view_library(chat_id, mid=None):
    if not CATALOG:
        return show(chat_id, t(chat_id, "lib_empty"), kb(home_row(chat_id)), mid)
    rows = [[B(t(chat_id, "lib_row", title=a["title"], n=len(a["episodes"])), f"show:{aid}")]
            for aid, a in CATALOG.items()]
    rows.append(home_row(chat_id))
    show(chat_id, t(chat_id, "lib_title"), kb(*rows), mid)


# ================================================================ online flow
def first_os_source():
    for name, obj in SOURCE_OBJS.items():
        if isinstance(obj, OpenSubs):
            return name, obj
    return None, None


def start_online(chat_id, uid):
    raw = LAST_QUERY.get(chat_id)
    if not raw:
        send_message(chat_id, t(uid, "need_query")); return
    if not SOURCE_OBJS:
        send_message(chat_id, t(uid, "online_none")); return
    title_q, season, episode = parse_query(raw)
    send_message(chat_id, t(uid, "searching_online"))
    chat_action(chat_id)
    ctx = {"title_q": title_q, "season": season, "episode": episode,
           "features": [], "subs": [], "view": [], "page": 0, "langf": "all"}
    CTX[chat_id] = ctx
    _, os_obj = first_os_source()
    feats = []
    if os_obj:
        try:
            feats = os_obj.search_features(title_q, limit=8)
        except Exception:
            feats = []
    if feats:
        ctx["features"] = feats
        rows = []
        for i, f in enumerate(feats):
            icon = "📺" if f["type"] == "tv" else "🎬"
            yr = f" ({f['year']})" if f["year"] else ""
            rows.append([B(f"{icon} {f['title']}{yr}"[:60], f"feat:{i}")])
        send_message(chat_id, t(uid, "pick_title"), {"inline_keyboard": rows})
    else:
        merged_search(chat_id, uid, None)


def merged_search(chat_id, uid, feature):
    ctx = CTX[chat_id]
    ctx["feature"] = feature
    results, errors = [], []
    for name, obj in SOURCE_OBJS.items():
        try:
            if feature and isinstance(obj, OpenSubs):
                subs = obj.search_by_imdb(feature["imdb_id"], languages="bn,en",
                                          season=ctx["season"], episode=ctx["episode"], limit=30)
            else:
                subs = obj.search(ctx["title_q"], languages="bn,en",
                                  season=ctx["season"], episode=ctx["episode"], limit=30)
            for s in subs:
                s["src"] = name
                results.append(s)
        except Exception as e:
            errors.append(f"{name}: {e}")
    results.sort(key=lambda x: x.get("downloads", 0), reverse=True)
    ctx["subs"], ctx["page"] = results, 0
    if not results and errors:
        send_message(chat_id, t(uid, "online_fail", err=esc("; ".join(errors)[:150]))); return
    show_subs_page(chat_id, uid)


def lang_label(uid, code):
    return T(ulang(uid), "lang_" + code) if code in ("bn", "en") else str(code).upper()


def show_subs_page(chat_id, uid, mid=None):
    ctx = CTX[chat_id]
    langf = ctx["langf"]
    view = [s for s in ctx["subs"] if langf == "all" or s["lang"] == langf]
    ctx["view"] = view
    lang_row = [B(t(uid, "lang_bn"), "langf:bn"), B(t(uid, "lang_en"), "langf:en"),
                B(t(uid, "lang_all"), "langf:all")]
    if not view:
        show(chat_id, t(uid, "subs_empty"), kb(lang_row, [B(t(uid, "req_btn"), "req")]), mid)
        return
    pages = (len(view) + PAGE_SIZE - 1) // PAGE_SIZE
    page = max(0, min(ctx["page"], pages - 1))
    ctx["page"] = page
    base = page * PAGE_SIZE
    rows = []
    for i, r in enumerate(view[base:base + PAGE_SIZE]):
        se = f" S{r['season']}E{r['episode']}" if r.get("season") else ""
        rows.append([B(f"{lang_label(uid, r['lang'])}{se} | ⬇{r['downloads']} | {r['release']}"[:60],
                       f"dl:{base + i}")])
    nav = []
    if page > 0:
        nav.append(B(t(uid, "prev"), f"page:{page - 1}"))
    if page < pages - 1:
        nav.append(B(t(uid, "next"), f"page:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append(lang_row)
    feat = ctx.get("feature")
    title = esc(feat["title"] if feat else ctx["title_q"])
    show(chat_id, t(uid, "subs_header", title=title, n=len(view), p=page + 1, pp=pages),
         {"inline_keyboard": rows}, mid)


def online_download(chat_id, uid, idx):
    ctx = CTX.get(chat_id, {})
    view = ctx.get("view", [])
    if idx >= len(view):
        send_message(chat_id, t(uid, "old_result")); return
    r = view[idx]
    src = r.get("src", "")
    obj = SOURCE_OBJS.get(src)
    if obj is None:
        send_message(chat_id, t(uid, "src_off")); return
    cache_path = os.path.join(CACHE_DIR, f"{src}-{r['file_id']}.srt")
    title = r.get("release") or r.get("feature") or ctx.get("title_q", "")
    caption = t(uid, "caption_online", title=esc(title), lang=lang_label(uid, r["lang"]), src=esc(src))
    if not os.path.exists(cache_path):
        try:
            chat_action(chat_id, "upload_document")
            path = obj.download(r["file_id"], CACHE_DIR) if isinstance(obj, OpenSubs) \
                else obj.download(r["url"], CACHE_DIR)
            if os.path.abspath(path) != os.path.abspath(cache_path):
                try:
                    os.replace(path, cache_path)
                except Exception:
                    cache_path = path
        except Exception as e:
            send_message(chat_id, t(uid, "dl_fail", err=esc(e))); return
    send_path = cache_path
    rel = r.get("release")
    if rel:
        safe = re.sub(r"[^\w\-.()\[\] ]+", "_", str(rel)).strip()[:80].strip()
        if safe:
            named_dir = os.path.join(CACHE_DIR, "named")
            os.makedirs(named_dir, exist_ok=True)
            named_path = os.path.join(named_dir, safe if safe.lower().endswith(".srt") else safe + ".srt")
            try:
                if not os.path.exists(named_path):
                    with open(cache_path, "rb") as fsrc, open(named_path, "wb") as fdst:
                        fdst.write(fsrc.read())
                send_path = named_path
            except Exception:
                send_path = cache_path
    deliver(chat_id, uid, send_path, caption, title)


# ================================================================ requests
def pending_reqs():
    return [r for r in REQS if r.get("status") == "pending"]


def make_request(chat_id, user):
    uid = user["id"]
    q = LAST_QUERY.get(chat_id)
    if not q:
        send_message(chat_id, t(uid, "req_need")); return
    if any(r["uid"] == uid and norm(r["q"]) == norm(q) and r["status"] == "pending" for r in REQS):
        send_message(chat_id, t(uid, "req_dup")); return
    with LOCK:
        rid = max([r["id"] for r in REQS] + [0]) + 1
        REQS.append({"id": rid, "uid": uid, "name": user.get("first_name", ""), "q": q,
                     "ts": time.strftime("%Y-%m-%d %H:%M"), "status": "pending"})
        mark("reqs")
    send_message(chat_id, t(uid, "req_ok"))
    for aid in admin_ids():
        send_message(aid, T(ulang(aid), "a_req_new", q=esc(q), name=esc(user.get("first_name", "")), uid=uid),
                     kb([B("👁", f"adm:rq:view:{rid}")]))


def fulfil_requests(title, slug):
    n = 0
    nt, ns = norm(title), slug.replace("-", " ")
    for r in pending_reqs():
        base, _, _ = parse_query(r["q"])
        if base and (nt in base or base in nt or ns in base or base in ns):
            r["status"] = "done"; n += 1
            send_message(r["uid"], t(r["uid"], "req_done", q=esc(r["q"])))
    if n:
        mark("reqs")
    return n


# ================================================================ user views
def view_home(chat_id, mid=None):
    show(chat_id, t(chat_id, "menu_title"), main_menu_kb(chat_id), mid)


def view_help(chat_id, mid=None):
    show(chat_id, t(chat_id, "help"), kb(home_row(chat_id)), mid)


def view_profile(chat_id, mid=None):
    rec = USERS[str(chat_id)]
    lvl, cur, nxt, rank = level_info(rec["xp"])
    status = (t(chat_id, "status_premium", until=fdate(rec["premium_until"]))
              if is_premium(chat_id) else t(chat_id, "status_free"))
    rank_name = rank[1] if ulang(chat_id) == "bn" else rank[0]
    text = t(chat_id, "profile", name=esc(rec["name"]), lvl=lvl, rank=rank_name,
             bar=bar(rec["xp"] - cur, nxt - cur), xp=rec["xp"], nxt=nxt, streak=rec["streak"],
             searches=rec["searches"], downloads=rec["downloads"], refs=rec["refs"],
             bonus=rec["bonus"], status=status, quota=quota_text(chat_id), since=rec["first_seen"])
    show(chat_id, text, kb([B(t(chat_id, "btn_invite"), "mn:invite"), B("🏆 Top", "mn:top")],
                           home_row(chat_id)), mid)


def view_premium(chat_id, mid=None):
    uid = chat_id
    gate = SETTINGS.get("join_gate") and SETTINGS.get("channels")
    rows = []
    if is_premium(uid):
        status = t(uid, "prem_active", until=fdate(USERS[str(uid)]["premium_until"]))
    elif gate and joined_all(uid):
        status = t(uid, "prem_gate_open")
    elif gate:
        status = t(uid, "prem_gate_lock")
        rows += gate_kb(uid)["inline_keyboard"]
    else:
        status = t(uid, "prem_none")
    rows.append([B("🎟 Redeem", "redeem")])
    rows.append(home_row(uid))
    show(chat_id, t(uid, "premium_card", status=status), kb(*rows), mid)


def view_settings(chat_id, mid=None):
    rec = USERS[str(chat_id)]
    state = t(chat_id, "on" if rec["notify"] else "off")
    text = t(chat_id, "settings", lang=LANGS[ulang(chat_id)], notif=state)
    show(chat_id, text, kb([B(t(chat_id, "set_lang"), "set:lang")],
                           [B(t(chat_id, "set_notif", state=state), "set:notif")],
                           [B(t(chat_id, "set_clear_hist"), "set:clearhist")],
                           home_row(chat_id)), mid)


def view_favs(chat_id, mid=None):
    favs = [f for f in USERS[str(chat_id)]["favs"] if f in CATALOG]
    if not favs:
        return show(chat_id, t(chat_id, "fav_empty"), kb(home_row(chat_id)), mid)
    rows = [[B(f"❤️ {CATALOG[f]['title']}", f"show:{f}")] for f in favs]
    rows.append(home_row(chat_id))
    show(chat_id, t(chat_id, "fav_title"), kb(*rows), mid)


def view_history(chat_id, mid=None):
    hist = USERS[str(chat_id)]["history"]
    if not hist:
        return show(chat_id, t(chat_id, "hist_empty"), kb(home_row(chat_id)), mid)
    rows = [[B(f"📄 {h['t']}"[:55], f"hist:{i}")] for i, h in enumerate(hist[:10])]
    rows.append(home_row(chat_id))
    show(chat_id, t(chat_id, "hist_title"), kb(*rows), mid)


def view_invite(chat_id, mid=None):
    rec = USERS[str(chat_id)]
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{chat_id}"
    show(chat_id, t(chat_id, "invite", link=link, bonus=SETTINGS["referral_bonus"], refs=rec["refs"]),
         kb(home_row(chat_id)), mid)


def view_trending(chat_id, mid=None):
    top = Counter(STATS["queries"]).most_common(8)
    if not top:
        return show(chat_id, t(chat_id, "trend_empty"), kb(home_row(chat_id)), mid)
    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 5
    rows = "\n".join(f"{medals[i]} {esc(q)} · {c}×" for i, (q, c) in enumerate(top))
    show(chat_id, t(chat_id, "trend_title", rows=rows), kb(home_row(chat_id)), mid)


def view_top(chat_id, mid=None):
    ranked = sorted(((u, r) for u, r in USERS.items() if not r.get("banned")),
                    key=lambda x: x[1].get("xp", 0), reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    lines = []
    for i, (_, r) in enumerate(ranked):
        nm = esc((r.get("name") or "User")[:3]) + "•••"
        lines.append(f"{medals[i]} {nm} · Lv {level_info(r.get('xp', 0))[0]} · {r.get('xp', 0)} XP")
    show(chat_id, t(chat_id, "top_title", rows="\n".join(lines) or "—"), kb(home_row(chat_id)), mid)


def send_welcome(chat_id, user):
    send_message(chat_id, t(chat_id, "welcome", name=esc(user.get("first_name", ""))), reply_kb(chat_id))
    send_message(chat_id, t(chat_id, "menu_title"), main_menu_kb(chat_id))


def process_referral(user, new_rec, payload):
    m = re.match(r"ref_(\d+)$", payload or "")
    if not m:
        return
    ref_id = m.group(1)
    if ref_id == str(user["id"]) or ref_id not in USERS or new_rec.get("ref_by"):
        return
    ref = USERS[ref_id]
    bonus = SETTINGS["referral_bonus"]
    new_rec["ref_by"] = ref_id
    new_rec["bonus"] += bonus
    ref["bonus"] += bonus; ref["refs"] += 1
    add_xp(ref, 10)
    mark("users")
    send_message(int(ref_id), t(int(ref_id), "ref_joined", name=esc(user.get("first_name", "")), bonus=bonus))
    send_message(user["id"], t(user["id"], "ref_welcome", bonus=bonus))


def do_redeem(chat_id, uid, code):
    code = code.strip().upper()
    c = SETTINGS["codes"].get(code)
    rec = USERS[str(uid)]
    if not c or len(c["used_by"]) >= c.get("uses", 1) or uid in c["used_by"]:
        send_message(chat_id, t(uid, "redeem_bad")); return
    c["used_by"].append(uid)
    if c["type"] == "premium":
        until = grant_premium(rec, c["value"])
        send_message(chat_id, t(uid, "redeem_ok_premium", days=c["value"], until=until))
    else:
        rec["bonus"] += c["value"]; mark("users")
        send_message(chat_id, t(uid, "redeem_ok_credits", n=c["value"]))
    add_xp(rec, 5)
    save_settings()


def submit_feedback(chat_id, user, text):
    uid = user["id"]
    if time.time() - LAST_FB.get(uid, 0) < 60:
        send_message(chat_id, t(uid, "feedback_wait")); return
    LAST_FB[uid] = time.time()
    for aid in admin_ids():
        send_message(aid, T(ulang(aid), "a_feedback", name=esc(user.get("first_name", "") or "User"),
                            uid=uid, text=esc(text[:1500])))
    send_message(chat_id, t(uid, "feedback_ok"))


# ================================================================ user: search entry
def log_query(rec, text, title_q):
    rec["searches"] += 1
    add_xp(rec, 1)
    key = title_q or norm(text)
    STATS["queries"][key] = STATS["queries"].get(key, 0) + 1
    bump("searches")
    mark("users"); mark("stats")


def handle_query(chat_id, user, rec, text):
    uid = user["id"]
    LAST_QUERY[chat_id] = text
    title_q, season, episode = parse_query(text)
    log_query(rec, text, title_q)
    chat_action(chat_id)
    hits, fuzzy = search_local(title_q)
    if not hits:
        send_message(chat_id, t(uid, "not_found"),
                     kb(online_row(uid), [B(t(uid, "req_btn"), "req")]))
        return
    if fuzzy:
        rows = [[B(f"🎬 {CATALOG[a]['title']}", f"show:{a}")] for a in hits]
        send_message(chat_id, t(uid, "did_you_mean"), kb(*rows))
        send_message(chat_id, t(uid, "online_offer"), kb(online_row(uid)))
        return
    for aid in hits[:3]:
        a = CATALOG[aid]
        if episode is not None and episode in a["episodes"]:
            if require_access(chat_id, uid, "file"):
                deliver(chat_id, uid, a["episodes"][episode],
                        t(uid, "caption_local", title=f"{esc(a['title'])} — E{episode:02d}"),
                        f"{a['title']} E{episode:02d}")
        else:
            send_message(chat_id, anime_text(uid, aid), episode_keyboard(uid, aid))
    send_message(chat_id, t(uid, "online_offer"), kb(online_row(uid)))


# ================================================================ admin: views
def src_count():
    return sum(1 for s in SETTINGS["sources"] if s.get("enabled", True))


def view_admin(chat_id, mid=None):
    d = day_stats()
    eps = sum(len(a["episodes"]) for a in CATALOG.values())
    prem = sum(1 for u in USERS if is_premium(int(u)))
    ban = sum(1 for r in USERS.values() if r.get("banned"))
    text = t(chat_id, "a_dash", users=len(USERS), new=d["new"], active=len(d["active"]), s=d["searches"],
             d=d["downloads"], prem=prem, ban=ban, pr=len(pending_reqs()), titles=len(CATALOG), eps=eps,
             src=src_count(), gate="ON" if SETTINGS["join_gate"] else "OFF",
             maint="ON" if SETTINGS["maintenance"] else "OFF", up=fmt_uptime())
    c = chat_id
    rows = [[B(t(c, "a_b_stats"), "adm:stats"), B(t(c, "a_b_users"), "adm:users")],
            [B(t(c, "a_b_bc"), "adm:bc"), B(t(c, "a_b_codes"), "adm:codes")],
            [B(t(c, "a_b_lib"), "adm:lib"), B(t(c, "a_b_reqs"), "adm:rq")],
            [B(t(c, "a_b_src"), "adm:src"), B(t(c, "a_b_ch"), "adm:ch")],
            [B(t(c, "a_b_cfg"), "adm:cfg"), B(t(c, "a_b_admins"), "adm:adms")],
            [B(t(c, "a_b_backup"), "adm:backup"), B(t(c, "a_b_refresh"), "adm:home")]]
    show(chat_id, text, kb(*rows), mid)


def back_row(c):
    return [B(t(c, "a_b_back"), "adm:home")]


def view_analytics(chat_id, mid=None):
    days = sorted(STATS["days"])[-7:]
    mx = max([STATS["days"][d]["searches"] for d in days] + [1])
    rows = "\n".join(f"<code>{d[5:]}</code> {bar(STATS['days'][d]['searches'], mx, 8)} "
                     f"{STATS['days'][d]['searches']}🔎 {STATS['days'][d].get('downloads', 0)}📥 "
                     f"+{STATS['days'][d].get('new', 0)}👤" for d in days) or t(chat_id, "a_none")
    top = "\n".join(f"{i + 1}. {esc(q)} ({c})" for i, (q, c) in
                    enumerate(Counter(STATS["queries"]).most_common(5))) or t(chat_id, "a_none")
    dl = "\n".join(f"{i + 1}. {esc(q)} ({c})" for i, (q, c) in
                   enumerate(Counter(STATS["dl_titles"]).most_common(5))) or t(chat_id, "a_none")
    show(chat_id, t(chat_id, "a_analytics", rows=rows, top=top, dl=dl), kb(back_row(chat_id)), mid)


def user_card(chat_id, uid, mid=None):
    rec = USERS.get(str(uid))
    if not rec:
        return show(chat_id, t(chat_id, "a_u_none"), kb(back_row(chat_id)), mid)
    lvl = level_info(rec["xp"])[0]
    c = chat_id
    status = (t(c, "status_premium", until=fdate(rec["premium_until"]))
              if rec["premium_until"] > time.time() else t(c, "status_free"))
    text = t(c, "a_ucard", name=esc(rec["name"]), uname=f"@{esc(rec['username'])}" if rec["username"] else "",
             uid=uid, lang=ulang(uid), lvl=lvl, xp=rec["xp"], searches=rec["searches"],
             downloads=rec["downloads"], status=status, bonus=rec["bonus"], refs=rec["refs"],
             banned="YES" if rec["banned"] else "no", since=rec["first_seen"], last=rec["last_seen"])
    ban_btn = B(t(c, "a_unban"), f"adm:u:unban:{uid}") if rec["banned"] else B(t(c, "a_ban"), f"adm:u:ban:{uid}")
    show(chat_id, text, kb([ban_btn, B(t(c, "a_revoke"), f"adm:u:revoke:{uid}")],
                           [B("⭐ +7d", f"adm:u:grant:7:{uid}"), B("⭐ +30d", f"adm:u:grant:30:{uid}"),
                            B("⭐ +90d", f"adm:u:grant:90:{uid}")],
                           [B(t(c, "a_credits"), f"adm:u:cred:{uid}"), B(t(c, "a_dm"), f"adm:u:dm:{uid}")],
                           [B(t(c, "a_b_users"), "adm:users")]), mid)


def view_users(chat_id, mid=None):
    c = chat_id
    show(chat_id, t(c, "a_users_menu", n=len(USERS)),
         kb([B(t(c, "a_u_find"), "adm:u:find")],
            [B(t(c, "a_u_recent"), "adm:ul:recent"), B(t(c, "a_u_top"), "adm:ul:top")],
            [B(t(c, "a_u_prem"), "adm:ul:prem"), B(t(c, "a_u_ban"), "adm:ul:ban")],
            [B(t(c, "a_users_csv"), "adm:csv")],
            back_row(c)), mid)


def view_user_list(chat_id, which, mid=None):
    items = list(USERS.items())
    if which == "recent":
        items = items[-10:][::-1]
    elif which == "top":
        items = sorted(items, key=lambda x: x[1].get("xp", 0), reverse=True)[:10]
    elif which == "prem":
        items = [(u, r) for u, r in items if r.get("premium_until", 0) > time.time()][:20]
    else:
        items = [(u, r) for u, r in items if r.get("banned")][:20]
    if not items:
        return show(chat_id, t(chat_id, "a_u_empty"), kb([B(t(chat_id, "a_b_users"), "adm:users")]), mid)
    rows = [[B(f"{r.get('name') or '?'} · {u} · {r.get('xp', 0)}XP"[:60], f"adm:u:view:{u}")]
            for u, r in items]
    rows.append([B(t(chat_id, "a_b_users"), "adm:users")])
    show(chat_id, t(chat_id, "a_users_menu", n=len(USERS)), kb(*rows), mid)


def audience_ids(which):
    ids = []
    for u, r in USERS.items():
        if r.get("banned") or r.get("blocked") or not r.get("notify", True):
            continue
        uid = int(u)
        lang = r.get("lang") or r.get("tg_lang") or "en"
        if which == "all" or (which == "prem" and is_premium(uid)) or \
                (which == "free" and not is_premium(uid)) or which == lang:
            ids.append(uid)
    return ids


def view_bc(chat_id, mid=None):
    c = chat_id
    rows = [[B(t(c, "a_bc_all", n=len(audience_ids("all"))), "adm:bc:all")],
            [B(t(c, "a_bc_prem", n=len(audience_ids("prem"))), "adm:bc:prem"),
             B(t(c, "a_bc_free", n=len(audience_ids("free"))), "adm:bc:free")],
            [B(t(c, "a_bc_bn", n=len(audience_ids("bn"))), "adm:bc:bn"),
             B(t(c, "a_bc_en", n=len(audience_ids("en"))), "adm:bc:en")],
            back_row(c)]
    show(chat_id, t(c, "a_bc_menu"), kb(*rows), mid)


def run_broadcast(admin_chat, src_chat, src_mid, uids):
    ok = fail = 0
    for uid in uids:
        r = api_post("copyMessage", {"chat_id": uid, "from_chat_id": src_chat, "message_id": src_mid})
        if r.get("ok"):
            ok += 1
        else:
            fail += 1
            desc = str(r.get("description", "")).lower()
            if "blocked" in desc or "deactivated" in desc or "not found" in desc:
                USERS[str(uid)]["blocked"] = True
        time.sleep(0.05)
    mark("users")
    send_message(admin_chat, t(admin_chat, "a_bc_done", ok=ok, fail=fail))


def new_code():
    alpha = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "SF-" + "".join(secrets.choice(alpha) for _ in range(4)) + "-" + \
        "".join(secrets.choice(alpha) for _ in range(4))


def view_codes(chat_id, mid=None):
    c = chat_id
    unused = [k for k, v in SETTINGS["codes"].items() if len(v["used_by"]) < v.get("uses", 1)]
    show(chat_id, t(c, "a_codes_menu", n=len(unused)),
         kb([B(t(c, "a_code_new"), "adm:code:new"), B(t(c, "a_code_list"), "adm:code:list")], back_row(c)), mid)


def view_lib(chat_id, mid=None):
    c = chat_id
    eps = sum(len(a["episodes"]) for a in CATALOG.values())
    cached = len([f for f in os.listdir(CACHE_DIR) if os.path.isfile(os.path.join(CACHE_DIR, f))]) \
        if os.path.isdir(CACHE_DIR) else 0
    rows = [[B("🗑 " + f"{a['title']} ({len(a['episodes'])})"[:50], f"adm:libdel:{aid}")]
            for aid, a in CATALOG.items()]
    rows += [[B(t(c, "a_lib_add"), "adm:libadd"), B(t(c, "a_lib_cache"), "adm:libcache")], back_row(c)]
    show(chat_id, t(c, "a_lib", n=len(CATALOG), eps=eps, cache=cached), kb(*rows), mid)


def view_reqs(chat_id, mid=None):
    c = chat_id
    pend = pending_reqs()
    if not pend:
        return show(chat_id, t(c, "a_reqs_none"), kb(back_row(c)), mid)
    rows = [[B(f"#{r['id']} {r['q']}"[:55], f"adm:rq:view:{r['id']}")] for r in pend[-15:][::-1]]
    rows.append(back_row(c))
    show(chat_id, t(c, "a_reqs", n=len(pend)), kb(*rows), mid)


def view_sources(chat_id, mid=None):
    c = chat_id
    lines, rows = [], []
    for s in SETTINGS["sources"]:
        on = s.get("enabled", True)
        lines.append(f"• <b>{esc(s['name'])}</b> ({s['type']}) — {'ON ✅' if on else 'OFF'}")
        rows.append([B(f"{'⏸' if on else '▶️'} {s['name']}", f"adm:srct:{s['name']}"),
                     B(f"🗑 {s['name']}", f"adm:srcd:{s['name']}")])
    rows += [[B(t(c, "a_src_add"), "adm:srca")], back_row(c)]
    show(chat_id, t(c, "a_src", rows="\n".join(lines) or t(c, "a_src_none")), kb(*rows), mid)


def view_channels(chat_id, mid=None):
    c = chat_id
    chans = SETTINGS["channels"]
    rows = [[B(f"🗑 {ch}", f"adm:chd:{ch}")] for ch in chans]
    rows += [[B(t(c, "a_ch_add"), "adm:cha")], back_row(c)]
    show(chat_id, t(c, "a_ch", rows="\n".join(f"• {esc(ch)}" for ch in chans) or t(c, "a_ch_none")),
         kb(*rows), mid)


def onoff(v):
    return "ON ✅" if v else "OFF"


def view_cfg(chat_id, mid=None):
    c = chat_id
    text = t(c, "a_cfg", limit=SETTINGS["daily_limit"] or "♾", ref=SETTINGS["referral_bonus"],
             maint=onoff(SETTINGS["maintenance"]), onl=onoff(SETTINGS["online_premium_only"]),
             gate=onoff(SETTINGS["join_gate"]),
             glevel=t(c, "a_gl_all" if SETTINGS["gate_all_downloads"] else "a_gl_prem"))
    show(chat_id, text, kb([B(t(c, "a_cfg_limit"), "adm:cfgn:daily_limit"),
                            B(t(c, "a_cfg_ref"), "adm:cfgn:referral_bonus")],
                           [B(t(c, "a_cfg_maint"), "adm:cfgt:maintenance")],
                           [B(t(c, "a_cfg_onl"), "adm:cfgt:online_premium_only")],
                           [B(t(c, "a_cfg_gate"), "adm:cfgt:join_gate")],
                           [B(t(c, "a_cfg_glevel"), "adm:cfgt:gate_all_downloads")],
                           back_row(c)), mid)


def view_admins(chat_id, mid=None):
    c = chat_id
    rows = [[B(f"🗑 {a}", f"adm:admd:{a}")] for a in SETTINGS["admins"]] if is_owner(c) else []
    if is_owner(c):
        rows.append([B(t(c, "a_adm_add"), "adm:adma")])
    rows.append(back_row(c))
    listing = "\n".join(f"• <code>{a}</code>" for a in SETTINGS["admins"]) or t(c, "a_none")
    show(chat_id, t(c, "a_admins", owner=ADMIN_ID, rows=listing), kb(*rows), mid)


def send_backup(chat_id):
    flush()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for fp in (USERS_FILE, SETTINGS_FILE, STATS_FILE, REQS_FILE, CATALOG_FILE):
            if os.path.exists(fp):
                z.write(fp, os.path.basename(fp))
    ts = time.strftime("%Y%m%d-%H%M")
    api_post("sendDocument", data={"chat_id": chat_id, "caption": t(chat_id, "a_backup_cap", ts=ts)},
             files={"document": (f"subfinder-backup-{ts}.zip", buf.getvalue())})
    send_users_csv(chat_id)


def send_users_csv(chat_id):
    lines = ["id,name,username,lang,xp,searches,downloads,premium_until,bonus,refs,banned,first_seen,last_seen"]
    for u, r in USERS.items():
        nm = str(r.get("name", "")).replace(",", " ").replace("\n", " ")
        lines.append(",".join(str(x) for x in (u, nm, r.get("username", ""), r.get("lang") or r.get("tg_lang"),
                                               r.get("xp", 0), r.get("searches", 0), r.get("downloads", 0),
                                               fdate(r["premium_until"]) if r.get("premium_until") else "",
                                               r.get("bonus", 0), r.get("refs", 0), r.get("banned", False),
                                               r.get("first_seen", ""), r.get("last_seen", ""))))
    api_post("sendDocument", data={"chat_id": chat_id, "caption": t(chat_id, "a_users_csv")},
             files={"document": ("users.csv", "\n".join(lines).encode("utf-8-sig"))})


# ================================================================ admin: actions
def admin_grant(admin_chat, uid, days):
    rec = USERS.get(str(uid))
    if not rec:
        return False
    until = grant_premium(rec, days)
    send_message(int(uid), t(int(uid), "a_user_prem_msg", days=days, until=until))
    return True


def add_subtitle_file(chat_id, title, year, slug, doc):
    global CATALOG
    content = download_tg_file(doc["file_id"])
    if content is None:
        send_message(chat_id, t(chat_id, "a_add_dlfail")); return 0
    fname = os.path.basename(doc.get("file_name", "subtitle.srt"))
    fdir = os.path.join(DATA_DIR, slug)
    os.makedirs(fdir, exist_ok=True)
    saved = 0
    if fname.lower().endswith(".zip") or content[:2] == b"PK":
        try:
            zf = zipfile.ZipFile(io.BytesIO(content))
            for n in zf.namelist():
                if n.lower().endswith(".srt"):
                    with open(os.path.join(fdir, os.path.basename(n)), "wb") as f:
                        f.write(zf.read(n))
                    saved += 1
            with open(os.path.join(fdir, "full-pack.zip"), "wb") as f:
                f.write(content)
        except Exception as e:
            send_message(chat_id, t(chat_id, "a_add_zipfail", e=esc(e))); return 0
    else:
        with open(os.path.join(fdir, fname), "wb") as f:
            f.write(content)
        saved = 1
    meta = load_json(CATALOG_FILE, {})
    if slug not in meta:
        meta[slug] = {"title": title, "year": year, "aliases": [slug.replace("-", " ")], "note": ""}
        save_json(CATALOG_FILE, meta)
    CATALOG = load_catalog()
    return saved


def admin_document(chat_id, user, doc, caption):
    flow = ADMIN_FLOW.get(chat_id)
    year = ""
    if flow and flow["kind"] == "addsub" and flow["step"] == "files":
        title, slug, year = flow["data"]["title"], flow["data"]["slug"], flow["data"].get("year", "")
    elif caption:
        raw = caption.strip()
        if "|" in raw:
            raw, year = [x.strip() for x in raw.split("|", 1)]
        title, slug = raw, slugify(raw)
    else:
        send_message(chat_id, t(chat_id, "a_add_notitle")); return
    saved = add_subtitle_file(chat_id, title, year, slug, doc)
    if saved:
        if flow and flow["kind"] == "addsub":
            flow["data"]["count"] += saved
        else:
            fulfil_requests(title, slug)
        send_message(chat_id, t(chat_id, "a_add_ok", title=esc(title), n=saved))


def finish_addapi(chat_id, flow):
    d = flow["data"]
    SETTINGS["sources"] = [s for s in SETTINGS["sources"] if s["name"] != d["name"]]
    SETTINGS["sources"].append({"name": d["name"], "type": d["type"], "api_key": d["api_key"],
                                "username": d.get("username", ""), "password": d.get("password", ""),
                                "enabled": True})
    save_settings(); rebuild_sources()
    ADMIN_FLOW.pop(chat_id, None)
    send_message(chat_id, t(chat_id, "a_src_ok", name=esc(d["name"]), t=d["type"]))


def start_flow(chat_id, kind, step, prompt_key, data=None, **kw):
    ADMIN_FLOW[chat_id] = {"kind": kind, "step": step, "data": data or {}}
    send_message(chat_id, t(chat_id, prompt_key, **kw))


def admin_wizard(chat_id, msg):
    """Wizard cholakale message handle. True = kheye felechi."""
    flow = ADMIN_FLOW.get(chat_id)
    if not flow:
        return False
    text = (msg.get("text") or "").strip()
    kind, step, data = flow["kind"], flow["step"], flow["data"]
    c = chat_id
    if kind == "broadcast" and step == "content":
        n = len(audience_ids(data["aud"]))
        data["src"] = (chat_id, msg["message_id"])
        flow["step"] = "confirm"
        api_post("copyMessage", {"chat_id": chat_id, "from_chat_id": chat_id, "message_id": msg["message_id"]})
        send_message(chat_id, t(c, "a_bc_preview", n=n),
                     kb([B(t(c, "a_bc_go"), "adm:bcgo"), B(t(c, "a_bc_no"), "adm:bcno")]))
        return True
    if not text:
        return True
    if kind == "addapi":
        if step == "name":
            data["name"] = slugify(text); flow["step"] = "key"
            send_message(chat_id, t(c, "a_src_key"))
        elif step == "key":
            data["api_key"] = text
            if data["type"] == "opensubtitles":
                flow["step"] = "user"; send_message(chat_id, t(c, "a_src_user"))
            else:
                finish_addapi(chat_id, flow)
        elif step == "user":
            data["username"] = text; flow["step"] = "pass"
            send_message(chat_id, t(c, "a_src_pass"))
        elif step == "pass":
            data["password"] = text
            finish_addapi(chat_id, flow)
        return True
    if kind == "addsub" and step == "title":
        raw, year = text, ""
        if "|" in raw:
            raw, year = [x.strip() for x in raw.split("|", 1)]
        slug = slugify(raw)
        flow["data"] = {"title": raw, "year": year, "slug": slug, "count": 0}
        flow["step"] = "files"
        os.makedirs(os.path.join(DATA_DIR, slug), exist_ok=True)
        send_message(chat_id, t(c, "a_add_files", title=esc(raw)))
        return True
    if kind == "addchannel":
        ch = text.replace("https://t.me/", "@").replace("http://t.me/", "@").strip()
        if not ch.startswith("@"):
            ch = "@" + ch
        info = api_post("getChat", {"chat_id": ch})
        ADMIN_FLOW.pop(chat_id, None)
        if not info.get("ok"):
            send_message(chat_id, t(c, "a_ch_bad")); return True
        if ch not in SETTINGS["channels"]:
            SETTINGS["channels"].append(ch); save_settings()
        send_message(chat_id, t(c, "a_ch_ok", ch=esc(ch)) + "\n" + t(c, "a_ch_warn"))
        return True
    if kind == "finduser":
        ADMIN_FLOW.pop(chat_id, None)
        user_card(chat_id, text.strip())
        return True
    if kind in ("setnum", "credits", "gencode", "adduser_admin"):
        if not re.fullmatch(r"\d+", text):
            send_message(chat_id, t(c, "a_num_bad")); return True
        n = int(text)
        if kind == "setnum":
            SETTINGS[data["key"]] = n; save_settings()
            ADMIN_FLOW.pop(chat_id, None); view_cfg(chat_id)
        elif kind == "credits":
            rec = USERS.get(data["uid"])
            ADMIN_FLOW.pop(chat_id, None)
            if rec:
                rec["bonus"] += n; mark("users")
                send_message(int(data["uid"]), t(int(data["uid"]), "a_user_credit_msg", n=n))
                send_message(chat_id, t(c, "a_done"))
                user_card(chat_id, data["uid"])
        elif kind == "adduser_admin":
            ADMIN_FLOW.pop(chat_id, None)
            if n not in SETTINGS["admins"]:
                SETTINGS["admins"].append(n); save_settings()
            send_message(chat_id, t(c, "a_adm_ok", uid=n)); view_admins(chat_id)
        elif kind == "gencode":
            if step == "val":
                data["value"] = n; flow["step"] = "cnt"
                send_message(chat_id, t(c, "a_code_cnt"))
            else:
                cnt = max(1, min(n, 50))
                codes = []
                for _ in range(cnt):
                    code = new_code()
                    SETTINGS["codes"][code] = {"type": data["ctype"], "value": data["value"],
                                               "uses": 1, "used_by": [], "created": int(time.time())}
                    codes.append(code)
                save_settings(); ADMIN_FLOW.pop(chat_id, None)
                what = f"{data['value']} " + ("days ⭐" if data["ctype"] == "premium" else "downloads 💎")
                send_message(chat_id, t(c, "a_code_made", n=cnt, what=what,
                                        codes="\n".join(f"<code>{x}</code>" for x in codes)))
        return True
    if kind == "dm":
        ADMIN_FLOW.pop(chat_id, None)
        r = send_message(int(data["uid"]), text)
        send_message(chat_id, t(c, "a_dm_sent" if r.get("ok") else "a_dm_fail"))
        return True
    return False


def admin_command(chat_id, user, text):
    global CATALOG
    parts = text.split()
    cmd = parts[0].lower().split("@")[0]
    args = parts[1:]
    c = chat_id
    if cmd in ("/admin", "/stats", "/dashboard"):
        view_admin(c); return True
    if cmd == "/addapi":
        if is_owner(user["id"]):
            show(c, t(c, "a_src_pick"), kb([B("OpenSubtitles", "adm:srcn:opensubtitles"),
                                            B("SubDL", "adm:srcn:subdl")]))
        return True
    if cmd == "/sources":
        view_sources(c); return True
    if cmd == "/addsub":
        start_flow(c, "addsub", "title", "a_add_title"); return True
    if cmd == "/done":
        flow = ADMIN_FLOW.pop(c, None)
        if flow and flow["kind"] == "addsub" and flow["data"].get("slug"):
            d = flow["data"]
            m = fulfil_requests(d["title"], d["slug"])
            send_message(c, t(c, "a_add_done", n=d.get("count", 0), m=m))
        return True
    if cmd == "/listsubs":
        send_message(c, "📚\n" + ("\n".join(f"• {esc(a['title'])} — {len(a['episodes'])} ep ({aid})"
                                          for aid, a in CATALOG.items()) or "—"))
        return True
    if cmd == "/delsub":
        name = slugify(" ".join(args))
        if os.path.isdir(os.path.join(DATA_DIR, name)):
            shutil.rmtree(os.path.join(DATA_DIR, name))
            meta = load_json(CATALOG_FILE, {}); meta.pop(name, None); save_json(CATALOG_FILE, meta)
            CATALOG = load_catalog()
            send_message(c, t(c, "a_lib_deleted", title=esc(name)))
        return True
    if cmd == "/addchannel":
        if args:
            ADMIN_FLOW[c] = {"kind": "addchannel", "step": "x", "data": {}}
            admin_wizard(c, {"text": args[0], "message_id": 0})
        else:
            start_flow(c, "addchannel", "x", "a_ch_ask")
        return True
    if cmd == "/delchannel":
        SETTINGS["channels"] = [x for x in SETTINGS["channels"] if x not in args]
        save_settings(); view_channels(c); return True
    if cmd == "/channels":
        view_channels(c); return True
    if cmd == "/gateall":
        SETTINGS["gate_all_downloads"] = "on" in text.lower(); save_settings(); view_cfg(c); return True
    if cmd == "/gate":
        SETTINGS["join_gate"] = "on" in text.lower(); save_settings(); view_cfg(c); return True
    if cmd == "/maintenance":
        SETTINGS["maintenance"] = "on" in text.lower(); save_settings(); view_cfg(c); return True
    if cmd == "/broadcast":
        view_bc(c); return True
    if cmd == "/user" and args:
        user_card(c, args[0]); return True
    if cmd in ("/ban", "/unban") and args and args[0] in USERS:
        USERS[args[0]]["banned"] = cmd == "/ban"; mark("users")
        user_card(c, args[0]); return True
    if cmd == "/grant" and len(args) >= 2 and args[0] in USERS and args[1].isdigit():
        admin_grant(c, args[0], int(args[1])); user_card(c, args[0]); return True
    if cmd == "/gencode":
        days = int(args[0]) if args and args[0].isdigit() else 7
        cnt = min(int(args[1]), 50) if len(args) > 1 and args[1].isdigit() else 1
        codes = []
        for _ in range(cnt):
            code = new_code()
            SETTINGS["codes"][code] = {"type": "premium", "value": days, "uses": 1, "used_by": [],
                                       "created": int(time.time())}
            codes.append(code)
        save_settings()
        send_message(c, t(c, "a_code_made", n=cnt, what=f"{days} days ⭐",
                          codes="\n".join(f"<code>{x}</code>" for x in codes)))
        return True
    if cmd == "/backup" and is_owner(user["id"]):
        send_backup(c); return True
    return False


# ================================================================ admin: callbacks
def admin_callback(cb, parts):
    global CATALOG
    chat_id = cb["message"]["chat"]["id"]
    mid = cb["message"]["message_id"]
    uid = cb["from"]["id"]
    cid = cb["id"]
    c = chat_id
    act = parts[1] if len(parts) > 1 else "home"
    arg = parts[2] if len(parts) > 2 else ""
    rest = ":".join(parts[3:]) if len(parts) > 3 else ""
    owner_only = {"src", "srca", "srcn", "srct", "srcd", "adma", "admd", "backup", "csv"}
    if act in owner_only and not is_owner(uid):
        answer_callback(cid, t(c, "a_owner"), True); return
    answer_callback(cid)
    if act == "home":
        view_admin(c, mid)
    elif act == "stats":
        view_analytics(c, mid)
    elif act == "users":
        view_users(c, mid)
    elif act == "ul":
        view_user_list(c, arg, mid)
    elif act == "csv":
        send_users_csv(c)
    elif act == "u":                      # adm:u:<action>:...
        if arg == "find":
            start_flow(c, "finduser", "x", "a_u_ask")
        elif arg == "view":
            user_card(c, rest, mid)
        elif arg in ("ban", "unban") and rest in USERS:
            USERS[rest]["banned"] = arg == "ban"; mark("users"); user_card(c, rest, mid)
        elif arg == "revoke" and rest in USERS:
            USERS[rest]["premium_until"] = 0; mark("users"); user_card(c, rest, mid)
        elif arg == "grant":
            days, target = rest.split(":", 1)
            if admin_grant(c, target, int(days)):
                user_card(c, target, mid)
        elif arg == "cred":
            start_flow(c, "credits", "x", "a_ask_credits", {"uid": rest})
        elif arg == "dm":
            start_flow(c, "dm", "x", "a_ask_dm", {"uid": rest})
    elif act == "bc":
        if arg:
            ADMIN_FLOW[c] = {"kind": "broadcast", "step": "content", "data": {"aud": arg}}
            send_message(c, t(c, "a_bc_ask"))
        else:
            view_bc(c, mid)
    elif act == "bcgo":
        flow = ADMIN_FLOW.pop(c, None)
        if flow and flow["kind"] == "broadcast" and flow["step"] == "confirm":
            uids = audience_ids(flow["data"]["aud"])
            send_message(c, t(c, "a_bc_run"))
            src_chat, src_mid = flow["data"]["src"]
            threading.Thread(target=run_broadcast, args=(c, src_chat, src_mid, uids), daemon=True).start()
    elif act == "bcno":
        ADMIN_FLOW.pop(c, None); send_message(c, t(c, "cancelled"))
    elif act == "codes":
        view_codes(c, mid)
    elif act == "code":
        if arg == "new":
            show(c, t(c, "a_code_kind"), kb([B(t(c, "a_code_k_prem"), "adm:code:k:premium"),
                                             B(t(c, "a_code_k_cred"), "adm:code:k:credits")]), mid)
        elif arg == "k":
            unit = "days" if rest == "premium" else "downloads"
            start_flow(c, "gencode", "val", "a_code_val", {"ctype": rest}, unit=unit)
        elif arg == "list":
            codes = [f"<code>{k}</code> · {v['value']}{'d' if v['type'] == 'premium' else '💎'}"
                     for k, v in SETTINGS["codes"].items() if len(v["used_by"]) < v.get("uses", 1)]
            show(c, t(c, "a_code_unused", codes="\n".join(codes[:60]) or "—"),
                 kb([B(t(c, "a_b_codes"), "adm:codes")]), mid)
    elif act == "lib":
        view_lib(c, mid)
    elif act == "libadd":
        start_flow(c, "addsub", "title", "a_add_title")
    elif act == "libcache":
        n = 0
        if os.path.isdir(CACHE_DIR):
            for f in os.listdir(CACHE_DIR):
                fp = os.path.join(CACHE_DIR, f)
                if os.path.isfile(fp):
                    os.remove(fp); n += 1
            shutil.rmtree(TOOLS_DIR, ignore_errors=True)
            os.makedirs(TOOLS_DIR, exist_ok=True)
        send_message(c, t(c, "a_lib_cleared", n=n)); view_lib(c)
    elif act == "libdel" and arg in CATALOG:
        show(c, t(c, "a_lib_del_ask", title=esc(CATALOG[arg]["title"])),
             kb([B(t(c, "a_yes"), f"adm:libdok:{arg}"), B(t(c, "a_no"), "adm:lib")]), mid)
    elif act == "libdok" and arg in CATALOG:
        title = CATALOG[arg]["title"]
        shutil.rmtree(os.path.join(DATA_DIR, arg), ignore_errors=True)
        meta = load_json(CATALOG_FILE, {}); meta.pop(arg, None); save_json(CATALOG_FILE, meta)
        CATALOG = load_catalog()
        send_message(c, t(c, "a_lib_deleted", title=esc(title))); view_lib(c)
    elif act == "rq":
        if arg == "view":
            r = next((x for x in REQS if str(x["id"]) == rest), None)
            if not r:
                return view_reqs(c, mid)
            show(c, t(c, "a_req_card", id=r["id"], q=esc(r["q"]), name=esc(r["name"]), uid=r["uid"], ts=r["ts"]),
                 kb([B(t(c, "a_req_done_btn"), f"adm:rq:done:{r['id']}")],
                    [B(t(c, "a_req_del_btn"), f"adm:rq:del:{r['id']}"), B("👤", f"adm:u:view:{r['uid']}")],
                    [B(t(c, "a_b_reqs"), "adm:rq")]), mid)
        elif arg in ("done", "del"):
            r = next((x for x in REQS if str(x["id"]) == rest), None)
            if r:
                r["status"] = "done" if arg == "done" else "deleted"; mark("reqs")
                if arg == "done":
                    send_message(r["uid"], t(r["uid"], "req_done", q=esc(r["q"])))
            view_reqs(c, mid)
        else:
            view_reqs(c, mid)
    elif act == "src":
        view_sources(c, mid)
    elif act == "srca":
        show(c, t(c, "a_src_pick"), kb([B("OpenSubtitles", "adm:srcn:opensubtitles"),
                                        B("SubDL", "adm:srcn:subdl")]), mid)
    elif act == "srcn":
        start_flow(c, "addapi", "name", "a_src_name", {"type": arg}, t=arg)
    elif act == "srct":
        for s in SETTINGS["sources"]:
            if s["name"] == arg:
                s["enabled"] = not s.get("enabled", True)
        save_settings(); rebuild_sources(); view_sources(c, mid)
    elif act == "srcd":
        SETTINGS["sources"] = [s for s in SETTINGS["sources"] if s["name"] != arg]
        save_settings(); rebuild_sources(); view_sources(c, mid)
    elif act == "ch":
        view_channels(c, mid)
    elif act == "cha":
        start_flow(c, "addchannel", "x", "a_ch_ask")
    elif act == "chd":
        SETTINGS["channels"] = [x for x in SETTINGS["channels"] if x != ":".join(parts[2:])]
        save_settings(); view_channels(c, mid)
    elif act == "cfg":
        view_cfg(c, mid)
    elif act == "cfgt" and arg in ("maintenance", "online_premium_only", "join_gate", "gate_all_downloads"):
        SETTINGS[arg] = not SETTINGS[arg]; save_settings(); view_cfg(c, mid)
    elif act == "cfgn" and arg in ("daily_limit", "referral_bonus"):
        start_flow(c, "setnum", "x", "a_cfg_num", {"key": arg})
    elif act == "adms":
        view_admins(c, mid)
    elif act == "adma":
        start_flow(c, "adduser_admin", "x", "a_adm_ask")
    elif act == "admd":
        SETTINGS["admins"] = [a for a in SETTINGS["admins"] if str(a) != arg]
        save_settings(); view_admins(c, mid)
    elif act == "backup":
        send_backup(c)


# ================================================================ main handlers
USER_VIEWS = {"/menu": view_home, "/help": view_help, "/profile": view_profile, "/premium": view_premium,
              "/settings": view_settings, "/favorites": view_favs, "/favs": view_favs,
              "/history": view_history, "/invite": view_invite, "/trending": view_trending,
              "/popular": view_trending, "/top": view_top, "/list": view_library, "/library": view_library}
MENU_VIEWS = {"home": view_home, "help": view_help, "profile": view_profile, "premium": view_premium,
              "settings": view_settings, "favs": view_favs, "history": view_history, "invite": view_invite,
              "trending": view_trending, "library": view_library, "top": view_top}


def handle_message(msg):
    if msg.get("chat", {}).get("type") != "private" or "from" not in msg:
        return
    chat_id = msg["chat"]["id"]
    user = msg["from"]
    uid = user["id"]
    text = (msg.get("text") or "").strip()
    rec, new = touch_user(user)
    admin = is_admin(uid)
    cmd = text.split()[0].lower().split("@")[0] if text.startswith("/") else ""

    if rec["banned"] and not admin:
        send_message(chat_id, t(uid, "banned")); return
    if SETTINGS["maintenance"] and not admin:
        send_message(chat_id, t(uid, "maint")); return
    now = time.time()
    if not admin and now - LAST_MSG.get(uid, 0) < 0.5:
        LAST_MSG[uid] = now
        return
    LAST_MSG[uid] = now

    # ---- admin: files / commands / wizards
    if admin:
        if cmd == "/cancel":
            ADMIN_FLOW.pop(chat_id, None); UFLOW.pop(uid, None)
            send_message(chat_id, t(uid, "cancelled")); return
        if msg.get("document"):
            admin_document(chat_id, user, msg["document"], msg.get("caption", "")); return
        if cmd:
            prev = ADMIN_FLOW.get(chat_id)
            if admin_command(chat_id, user, text):
                if cmd != "/done" and ADMIN_FLOW.get(chat_id) is prev:
                    ADMIN_FLOW.pop(chat_id, None)
                return
        if chat_id in ADMIN_FLOW and admin_wizard(chat_id, msg):
            return
    elif msg.get("document"):
        send_message(chat_id, t(uid, "no_file_upload")); return

    if not text:
        return

    # ---- start / language
    if cmd == "/start":
        payload = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
        if new and payload:
            process_referral(user, rec, payload)
        if rec["lang"] is None:
            send_message(chat_id, T("en", "lang_pick"), lang_picker_kb(":w"))
        elif gate_blocked(uid):
            show_gate(chat_id, uid)
        else:
            send_welcome(chat_id, user)
        return
    if gate_blocked(uid) and cmd not in ("/lang", "/id", "/cancel"):
        if rec["lang"] is None:
            send_message(chat_id, T("en", "lang_pick"), lang_picker_kb(":w"))
        else:
            show_gate(chat_id, uid)
        return
    if cmd == "/admin" and ADMIN_ID is None:
        send_message(chat_id, t(uid, "a_not_set")); return
    if cmd == "/cancel":
        UFLOW.pop(uid, None); send_message(chat_id, t(uid, "cancelled")); return
    if cmd == "/lang":
        send_message(chat_id, T("en", "lang_pick"), lang_picker_kb()); return

    # ---- pending user flows
    if uid in UFLOW and not cmd:
        kind = UFLOW.pop(uid)
        if kind == "redeem":
            do_redeem(chat_id, uid, text)
        elif kind == "feedback":
            submit_feedback(chat_id, user, text)
        return

    if cmd in USER_VIEWS:
        USER_VIEWS[cmd](chat_id); return
    if cmd == "/id":
        send_message(chat_id, f"🆔 <code>{uid}</code>"); return
    if cmd == "/redeem":
        args = text.split(maxsplit=1)
        if len(args) > 1:
            do_redeem(chat_id, uid, args[1])
        else:
            UFLOW[uid] = "redeem"; send_message(chat_id, t(uid, "redeem_ask"))
        return
    if cmd == "/feedback":
        args = text.split(maxsplit=1)
        if len(args) > 1:
            submit_feedback(chat_id, user, args[1])
        else:
            UFLOW[uid] = "feedback"; send_message(chat_id, t(uid, "feedback_ask"))
        return
    if cmd == "/request":
        make_request(chat_id, user); return
    if cmd:
        return

    # ---- reply keyboard buttons
    act = LABELS.get(text)
    if act:
        if act == "search":
            send_message(chat_id, t(uid, "ask_name"))
        elif act == "request":
            make_request(chat_id, user)
        else:
            {"library": view_library, "trending": view_trending, "favs": view_favs,
             "profile": view_profile, "premium": view_premium, "settings": view_settings}[act](chat_id)
        return

    handle_query(chat_id, user, rec, text)


def handle_callback(cb):
    if "message" not in cb:
        return
    data = cb.get("data", "")
    chat_id = cb["message"]["chat"]["id"]
    mid = cb["message"]["message_id"]
    user = cb["from"]
    uid = user["id"]
    rec, _ = touch_user(user)
    cid = cb["id"]
    parts = data.split(":")
    admin = is_admin(uid)

    if rec["banned"] and not admin:
        answer_callback(cid, T(ulang(uid), "banned"), True); return
    if SETTINGS["maintenance"] and not admin:
        answer_callback(cid, T(ulang(uid), "maint"), True); return
    if parts[0] == "adm":
        if not admin:
            answer_callback(cid, t(uid, "a_denied"), True); return
        admin_callback(cb, parts); return

    if gate_blocked(uid) and parts[0] != "lg" and data != "checkjoin":
        answer_callback(cid, t(uid, "join_no"), True)
        show_gate(chat_id, uid)
        return

    # ---- language
    if parts[0] == "lg" and len(parts) >= 2 and parts[1] in LANGS:
        rec["lang"] = parts[1]; mark("users")
        answer_callback(cid, T(parts[1], "lang_set").replace("<b>", "").replace("</b>", ""))
        if len(parts) > 2 and parts[2] == "w":
            if gate_blocked(uid):
                show_gate(chat_id, uid)
            else:
                send_welcome(chat_id, user)
        else:
            send_message(chat_id, t(uid, "lang_set"), reply_kb(uid)); view_settings(chat_id)
        return

    # ---- menu navigation
    if parts[0] == "mn":
        answer_callback(cid)
        fn = MENU_VIEWS.get(parts[1] if len(parts) > 1 else "home")
        if fn:
            fn(chat_id, mid)
        return
    if parts[0] == "set" and len(parts) == 2:
        answer_callback(cid)
        if parts[1] == "lang":
            show(chat_id, T("en", "lang_pick"), lang_picker_kb(), mid)
        elif parts[1] == "notif":
            rec["notify"] = not rec["notify"]; mark("users"); view_settings(chat_id, mid)
        elif parts[1] == "clearhist":
            rec["history"] = []; mark("users")
            send_message(chat_id, t(uid, "hist_cleared")); view_settings(chat_id, mid)
        return
    if data == "redeem":
        answer_callback(cid); UFLOW[uid] = "redeem"; send_message(chat_id, t(uid, "redeem_ask")); return
    if data == "checkjoin":
        if joined_all(uid, fresh=True):
            answer_callback(cid, t(uid, "join_ok"))
            if PENDING.pop(uid, None) == "online":
                send_message(chat_id, t(uid, "join_ok"))
                start_online(chat_id, uid)
            else:
                send_welcome(chat_id, user)
        else:
            answer_callback(cid, t(uid, "join_no"), True)
        return

    # ---- tools
    if parts[0] == "tl" and len(parts) == 3:
        if parts[2] not in subtools.OPS and parts[2] != "vtt":
            answer_callback(cid); return
        if run_tool(chat_id, uid, parts[1], parts[2]):
            answer_callback(cid, "✅")
        else:
            answer_callback(cid, t(uid, "tool_expired"), True)
        return

    # ---- favorites / history
    if parts[0] == "fav" and len(parts) == 2 and parts[1] in CATALOG:
        favs = rec["favs"]
        if parts[1] in favs:
            favs.remove(parts[1]); answer_callback(cid, t(uid, "fav_removed"))
        else:
            favs.append(parts[1]); answer_callback(cid, t(uid, "fav_added"))
        mark("users")
        edit_markup(chat_id, mid, episode_keyboard(uid, parts[1])); return
    if parts[0] == "hist" and len(parts) == 2 and parts[1].isdigit():
        i = int(parts[1])
        if i < len(rec["history"]):
            h = rec["history"][i]
            fp = os.path.join(BASE, h["p"])
            if os.path.exists(fp):
                answer_callback(cid, t(uid, "sending"))
                send_document(chat_id, fp, f"🕘 {esc(h['t'])}\nSubFinder", tools_kb(uid, fp)); return
        answer_callback(cid, t(uid, "hist_gone"), True); return

    # ---- library
    if parts[0] == "show" and len(parts) == 2 and parts[1] in CATALOG:
        answer_callback(cid)
        send_message(chat_id, anime_text(uid, parts[1]), episode_keyboard(uid, parts[1])); return
    if parts[0] == "ep" and len(parts) == 3 and parts[2].isdigit():
        a, ep = CATALOG.get(parts[1]), int(parts[2])
        if a and ep in a["episodes"]:
            if require_access(chat_id, uid, "file"):
                answer_callback(cid, t(uid, "sending"))
                deliver(chat_id, uid, a["episodes"][ep],
                        t(uid, "caption_local", title=f"{esc(a['title'])} — E{ep:02d}"), f"{a['title']} E{ep:02d}")
                return
        answer_callback(cid); return
    if parts[0] == "zip" and len(parts) == 2:
        a = CATALOG.get(parts[1])
        if a and a.get("zip"):
            if require_access(chat_id, uid, "zip"):
                answer_callback(cid, t(uid, "sending"))
                deliver(chat_id, uid, a["zip"], t(uid, "caption_zip", title=esc(a["title"])),
                        f"{a['title']} (ZIP)", tools=False)
                return
        answer_callback(cid); return

    # ---- online
    if data == "online":
        answer_callback(cid)
        if require_access(chat_id, uid, "online", pending="online"):
            start_online(chat_id, uid)
        return
    if data == "req":
        answer_callback(cid); make_request(chat_id, user); return
    if parts[0] == "feat" and chat_id in CTX:
        answer_callback(cid, "🔎")
        feats = CTX[chat_id].get("features", [])
        if parts[1].isdigit() and int(parts[1]) < len(feats):
            merged_search(chat_id, uid, feats[int(parts[1])])
        return
    if parts[0] == "langf" and chat_id in CTX:
        answer_callback(cid)
        CTX[chat_id]["langf"] = parts[1]; CTX[chat_id]["page"] = 0
        show_subs_page(chat_id, uid, mid); return
    if parts[0] == "page" and chat_id in CTX and parts[1].isdigit():
        answer_callback(cid)
        CTX[chat_id]["page"] = int(parts[1]); show_subs_page(chat_id, uid, mid); return
    if parts[0] == "dl" and len(parts) == 2 and parts[1].isdigit():
        answer_callback(cid, t(uid, "sending"))
        online_download(chat_id, uid, int(parts[1])); return
    answer_callback(cid, t(uid, "unknown_cb"))


# ================================================================ boot
CMD_DESC = [
    ("start", "মেইন মেনু", "Main menu"), ("library", "লাইব্রেরি", "Subtitle library"),
    ("trending", "ট্রেন্ডিং", "What's trending"), ("favorites", "ফেভারিট", "Saved titles"),
    ("history", "ডাউনলোড হিস্ট্রি", "Download history"), ("profile", "প্রোফাইল ও লেভেল", "Profile & level"),
    ("invite", "ইনভাইট ও বোনাস", "Invite & earn"), ("redeem", "কোড রিডিম", "Redeem a code"),
    ("top", "লিডারবোর্ড", "Leaderboard"), ("premium", "প্রিমিয়াম", "Premium"),
    ("settings", "সেটিংস", "Settings"), ("lang", "ভাষা বদলান", "Change language"),
    ("feedback", "মতামত পাঠান", "Send feedback"), ("help", "হেল্প", "Help"),
]
ADMIN_CMD_DESC = [("admin", "Control center"), ("addsub", "Add subtitles"), ("broadcast", "Broadcast"),
                  ("user", "User card: /user ID"), ("gencode", "Codes: /gencode DAYS COUNT"),
                  ("maintenance", "/maintenance on|off")]


def setup_commands():
    en = [{"command": c, "description": e} for c, _, e in CMD_DESC]
    bn = [{"command": c, "description": b} for c, b, _ in CMD_DESC]
    api_post("setMyCommands", {"commands": json.dumps(en)})
    api_post("setMyCommands", {"commands": json.dumps(bn), "language_code": "bn"})
    for aid in admin_ids():
        full = en + [{"command": c, "description": d} for c, d in ADMIN_CMD_DESC]
        api_post("setMyCommands", {"commands": json.dumps(full),
                                   "scope": json.dumps({"type": "chat", "chat_id": aid})})


def migrate_old_log():
    if not STATS["queries"] and os.path.exists(OLD_LOG_FILE):
        for line in open(OLD_LOG_FILE, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split(" | ")
            if len(p) == 3:
                q, _, _ = parse_query(p[2])
                if q:
                    STATS["queries"][q] = STATS["queries"].get(q, 0) + 1
        mark("stats")


def dispatch(upd):
    try:
        if "message" in upd:
            with CHAT_LOCKS[upd["message"]["chat"]["id"]]:
                handle_message(upd["message"])
        elif "callback_query" in upd:
            cq = upd["callback_query"]
            chat = cq["message"]["chat"]["id"] if "message" in cq else 0
            with CHAT_LOCKS[chat]:
                handle_callback(cq)
    except Exception as e:
        import traceback
        print("handler error:", e)
        traceback.print_exc()



def startup():
    global BOT_USERNAME
    if not TOKEN:
        print("BOT TOKEN PAI NAI! token.txt file a token rekhe abar chalao।")
        sys.exit(1)
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(TOOLS_DIR, exist_ok=True)
    migrate_old_log()
    me = api_post("getMe")
    BOT_USERNAME = me.get("result", {}).get("username", "")
    print("╭──────────────────────────────╮")
    print("│   SubFinder  (v6)       │")
    print("╰──────────────────────────────╯")
    print("Bot cholche: @" + BOT_USERNAME)
    print("Library:", {k: len(v["episodes"]) for k, v in CATALOG.items()})
    print("Sources:", list(SOURCE_OBJS), "| Owner:", ADMIN_ID, "| Admins:", SETTINGS["admins"],
          "| Users:", len(USERS))
    if ADMIN_ID is None:
        print("⚠️  config.json a admin_id nai — bot a /id likhe ID niye config.json a boshao।")
    setup_commands()
    threading.Thread(target=flusher, daemon=True).start()
def main():
    startup()
    pool = ThreadPoolExecutor(max_workers=12)
    base = (os.environ.get("WEBHOOK_BASE") or os.environ.get("RENDER_EXTERNAL_URL") or "").rstrip("/")
    if base:
        run_webhook(pool, base)
        return
    offset = 0
    try:
        while True:
            try:
                r = SESSION.get(f"{API}/getUpdates", timeout=60,
                                params={"offset": offset, "timeout": 50,
                                        "allowed_updates": json.dumps(["message", "callback_query"])})
                for upd in r.json().get("result", []):
                    offset = upd["update_id"] + 1
                    pool.submit(dispatch, upd)
            except Exception as e:
                print("loop error:", e)
                time.sleep(3)
    finally:
        flush()


def run_webhook(pool, base):
    import hashlib
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    secret = hashlib.sha256(TOKEN.encode()).hexdigest()[:20]
    hook_path = "/wh/" + secret
    hook_url = base + hook_path
    r = api_post("setWebhook", {"url": hook_url, "drop_pending_updates": True,
                                "allowed_updates": json.dumps(["message", "callback_query"])})
    print("Webhook set:", hook_url, "| ok:", (r or {}).get("ok"))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("SubFinder is alive".encode())

        def do_POST(self):
            if self.path != hook_path:
                self.send_response(404)
                self.end_headers()
                return
            try:
                n = int(self.headers.get("Content-Length", 0))
                upd = json.loads(self.rfile.read(n) or b"{}")
                if isinstance(upd, dict) and "update_id" in upd:
                    pool.submit(dispatch, upd)
            except Exception as e:
                print("webhook error:", e)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, *args):
            pass

    port = int(os.environ.get("PORT", "10000"))
    print("Webhook server listening on port", port)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
