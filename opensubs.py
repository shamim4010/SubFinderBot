"""
OpenSubtitles.com online source
--------------------------------
config.json theke credentials ney:
{
  "opensubtitles": {
    "api_key": "TOMAR_API_KEY",
    "username": "TOMAR_USERNAME",
    "password": "TOMAR_PASSWORD"
  }
}
Account khola free: https://www.opensubtitles.com/en/newuser
API key: account er profile/API page theke "Consumers" baniye nao.

Sotorko: free account a protidin download er limit thake (olpo koyekta).
Tai bot age nijer cache theke dey, na pele online download kore cache a rekhe dey.
"""

import io
import json
import os
import time
import zipfile

import requests

BASE_URL = "https://api.opensubtitles.com/api/v1"
UA = "AnimeSubtitlesBD v2.0"


class OpenSubsError(Exception):
    pass


class OpenSubs:
    def __init__(self, api_key, username="", password=""):
        self.api_key = api_key
        self.username = username
        self.password = password
        self.token = None
        self.token_time = 0
        self.session = requests.Session()
        self.session.headers.update(
            {"Api-Key": api_key, "User-Agent": UA, "Content-Type": "application/json"}
        )

    # ------------------------------------------------------------ auth
    def login(self):
        if not self.username or not self.password:
            raise OpenSubsError("OpenSubtitles username/password config a nai")
        r = self.session.post(
            f"{BASE_URL}/login",
            json={"username": self.username, "password": self.password},
            timeout=30,
        )
        if r.status_code != 200:
            raise OpenSubsError(f"login fail ({r.status_code})")
        self.token = r.json().get("token")
        self.token_time = time.time()
        return self.token

    def ensure_token(self):
        if not self.token or time.time() - self.token_time > 20 * 3600:
            self.login()
        return self.token

    # ------------------------------------------------------------ search
    def search(self, query, languages="bn,en", season=None, episode=None,
               type_=None, limit=10):
        """Subtitle list ferot dey: [{file_id, lang, release, downloads, feature}]"""
        params = {"query": query, "languages": languages, "order_by": "download_count"}
        if season is not None:
            params["season_number"] = season
        if episode is not None:
            params["episode_number"] = episode
        if type_:
            params["type"] = type_
        r = self.session.get(f"{BASE_URL}/subtitles", params=params, timeout=30)
        if r.status_code != 200:
            raise OpenSubsError(f"search fail ({r.status_code})")
        out = []
        for item in r.json().get("data", []):
            a = item.get("attributes", {})
            files = a.get("files", [])
            if not files:
                continue
            feat = a.get("feature_details", {}) or {}
            out.append({
                "file_id": files[0].get("file_id"),
                "file_name": files[0].get("file_name", "subtitle.srt"),
                "lang": a.get("language", "?"),
                "release": a.get("release", "")[:60],
                "downloads": a.get("download_count", 0),
                "feature": feat.get("title") or feat.get("movie_name") or query,
                "year": feat.get("year", ""),
                "season": feat.get("season_number"),
                "episode": feat.get("episode_number"),
            })
            if len(out) >= limit:
                break
        return out


    # ------------------------------------------------------------ features (titles)
    def search_features(self, query, limit=8):
        """Movie/series er title list dey: [{imdb_id, title, year, type}]"""
        r = self.session.get(f"{BASE_URL}/features", params={"query": query}, timeout=30)
        if r.status_code != 200:
            raise OpenSubsError(f"features fail ({r.status_code})")
        out = []
        for item in r.json().get("data", []):
            a = item.get("attributes", {})
            out.append({
                "imdb_id": a.get("imdb_id"),
                "title": a.get("title") or a.get("original_title") or query,
                "year": a.get("year", ""),
                "type": a.get("feature_type", ""),
            })
            if len(out) >= limit:
                break
        return out

    def search_by_imdb(self, imdb_id, languages="bn,en", season=None,
                       episode=None, limit=30):
        """Ekta nirdisto title er subtitle list (language filter shoho paginate korar jonno beshi ney)."""
        params = {"imdb_id": imdb_id, "languages": languages,
                  "order_by": "download_count"}
        if season is not None:
            params["season_number"] = season
        if episode is not None:
            params["episode_number"] = episode
        r = self.session.get(f"{BASE_URL}/subtitles", params=params, timeout=30)
        if r.status_code != 200:
            raise OpenSubsError(f"search fail ({r.status_code})")
        out = []
        for item in r.json().get("data", []):
            a = item.get("attributes", {})
            files = a.get("files", [])
            if not files:
                continue
            feat = a.get("feature_details", {}) or {}
            out.append({
                "file_id": files[0].get("file_id"),
                "file_name": files[0].get("file_name", "subtitle.srt"),
                "lang": a.get("language", "?"),
                "release": a.get("release", "")[:60],
                "downloads": a.get("download_count", 0),
                "feature": feat.get("title") or feat.get("movie_name") or "",
                "year": feat.get("year", ""),
                "season": feat.get("season_number"),
                "episode": feat.get("episode_number"),
            })
            if len(out) >= limit:
                break
        return out

    # ------------------------------------------------------------ download
    def download(self, file_id, dest_dir):
        """file_id download kore dest_dir te save kore path ferot dey (cache er jonno)."""
        token = self.ensure_token()
        r = self.session.post(
            f"{BASE_URL}/download",
            json={"file_id": file_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if r.status_code == 406:
            raise OpenSubsError("Ajker free download limit shesh")
        if r.status_code != 200:
            raise OpenSubsError(f"download fail ({r.status_code})")
        info = r.json()
        link = info.get("link")
        fname = info.get("file_name") or f"{file_id}.srt"
        raw = self.session.get(link, timeout=60)
        raw.raise_for_status()
        content = raw.content
        os.makedirs(dest_dir, exist_ok=True)
        # zip/gz hole vitore .srt ber kori
        if fname.lower().endswith(".zip") or content[:2] == b"PK":
            zf = zipfile.ZipFile(io.BytesIO(content))
            srts = [n for n in zf.namelist() if n.lower().endswith(".srt")]
            if not srts:
                raise OpenSubsError("zip er vitore .srt pai nai")
            name = os.path.basename(srts[0])
            path = os.path.join(dest_dir, name)
            with open(path, "wb") as f:
                f.write(zf.read(srts[0]))
            return path
        if not fname.lower().endswith(".srt"):
            fname += ".srt"
        path = os.path.join(dest_dir, fname)
        with open(path, "wb") as f:
            f.write(content)
        return path


def load_from_config(config_path):
    """config.json thakle OpenSubs object dey, na thakle None."""
    if not os.path.exists(config_path):
        return None
    try:
        cfg = json.load(open(config_path, encoding="utf-8"))
        os_cfg = cfg.get("opensubtitles", {})
        if os_cfg.get("api_key"):
            return OpenSubs(os_cfg["api_key"], os_cfg.get("username", ""),
                            os_cfg.get("password", ""))
    except Exception as e:
        print("config load error:", e)
    return None
