"""
SubFinder persistence (MongoDB) — Render free te restart/redeploy hole data jeno na muche.

MONGODB_URI env set thakle:
  - users / settings / stats / requests / catalog JSON  -> Mongo `state` collection
  - admin er add kora subtitle file (data/...)           -> Mongo `libfiles` collection
Startup a Mongo theke local file a restore hoy, tarpor bot normal vabe local file diyei kaj kore.
MONGODB_URI na thakle kichu-i bodlay na (age jemon chilo temon).
"""
import hashlib
import json
import os
import threading
import time

URI = os.environ.get("MONGODB_URI", "").strip()
DB_NAME = os.environ.get("MONGODB_DB", "subfinder")
SYNCED = ("users.json", "settings.json", "stats.json", "requests.json", "catalog.json", "chatmsgs.json")

_db = None
_dirty = {}          # filename -> local path
_last = {}           # filename -> md5 of last pushed text
_lock = threading.Lock()


def enabled():
    return _db is not None


def init():
    global _db
    if not URI:
        return False
    try:
        from pymongo import MongoClient
        cl = MongoClient(URI, serverSelectionTimeoutMS=8000)
        cl.admin.command("ping")
        _db = cl[DB_NAME]
        print("MongoDB persistence: ON (db=%s)" % DB_NAME)
        return True
    except Exception as e:
        _db = None
        print("MongoDB connect fail (local file diye cholbe):", e)
        return False


def restore_all(base):
    """Mongo theke local file gula nibe. catalog.json merge hoy (repo er entry age)."""
    if _db is None:
        return
    try:
        for doc in _db.state.find({"_id": {"$in": list(SYNCED)}}):
            name, text = doc["_id"], doc.get("data", "")
            path = os.path.join(base, name)
            if name == "catalog.json" and os.path.exists(path):
                try:
                    remote = json.loads(text)
                    local = json.load(open(path, encoding="utf-8"))
                    text = json.dumps({**remote, **local}, ensure_ascii=False, indent=1)
                except Exception:
                    continue
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            _last[name] = hashlib.md5(text.encode()).hexdigest()
        n = 0
        for doc in _db.libfiles.find({}):
            path = os.path.join(base, doc["_id"])
            if not os.path.exists(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    f.write(bytes(doc["data"]))
                n += 1
        print("Mongo restore done | library files restored:", n)
    except Exception as e:
        print("Mongo restore error:", e)


def mark(path):
    """save_json er por local file ta dirty kore (background thread push korbe)."""
    name = os.path.basename(path)
    if _db is not None and name in SYNCED:
        with _lock:
            _dirty[name] = path


def _push_state():
    with _lock:
        items = list(_dirty.items())
        _dirty.clear()
    for name, path in items:
        try:
            text = open(path, encoding="utf-8").read()
            h = hashlib.md5(text.encode()).hexdigest()
            if _last.get(name) == h:
                continue
            _db.state.replace_one({"_id": name}, {"_id": name, "data": text, "ts": time.time()}, upsert=True)
            _last[name] = h
        except Exception as e:
            print("Mongo push error:", name, e)
            with _lock:
                _dirty.setdefault(name, path)


def _worker():
    while True:
        time.sleep(5)
        if _db is not None:
            _push_state()


def start_worker():
    if _db is not None:
        threading.Thread(target=_worker, daemon=True).start()


def flush():
    if _db is not None:
        _push_state()


def push_file(base, path):
    """Library file (data/slug/x.srt) Mongo te rakho. 16MB er boro hole skip."""
    if _db is None or not os.path.exists(path):
        return
    try:
        raw = open(path, "rb").read()
        if len(raw) > 15 * 1024 * 1024:
            return
        rel = os.path.relpath(path, base).replace(os.sep, "/")
        _db.libfiles.replace_one({"_id": rel}, {"_id": rel, "data": raw, "ts": time.time()}, upsert=True)
    except Exception as e:
        print("Mongo file push error:", e)


def delete_prefix(rel_prefix):
    """data/slug folder delete hole Mongo theke-o muche felo."""
    if _db is None:
        return
    try:
        import re
        _db.libfiles.delete_many({"_id": {"$regex": "^" + re.escape(rel_prefix.rstrip("/") + "/")}})
    except Exception as e:
        print("Mongo delete error:", e)
