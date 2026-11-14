"""
SubDL.com online source (ditiyo source)
----------------------------------------
API key lage (free): https://subdl.com — account/API page theke.
Search:  GET https://api.subdl.com/api/v1/subtitles?api_key=..&film_name=..
Download: result er url (zip file) https://dl.subdl.com theke.
"""

import hashlib
import io
import os
import zipfile

import requests

SEARCH_URL = "https://api.subdl.com/api/v1/subtitles"
DL_BASE = "https://dl.subdl.com"


class SubDLError(Exception):
    pass


class SubDL:
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "SubFinder v4.0"})

    def search(self, query, languages="bn,en", season=None, episode=None,
               type_=None, limit=30):
        langs = ",".join(x.strip().upper() for x in languages.split(",") if x.strip())
        params = {"api_key": self.api_key, "film_name": query,
                  "languages": langs, "subs_per_page": 30}
        if season is not None:
            params["season_number"] = season
        if episode is not None:
            params["episode_number"] = episode
        if type_:
            params["type"] = type_
        r = self.session.get(SEARCH_URL, params=params, timeout=30)
        if r.status_code != 200:
            raise SubDLError(f"search fail ({r.status_code})")
        data = r.json()
        out = []
        for item in data.get("subtitles", []) or []:
            url = item.get("url") or item.get("download_url") or ""
            if not url:
                continue
            lang = (item.get("language") or item.get("lang") or "?").lower()
            out.append({
                "src": "subdl",
                "file_id": hashlib.md5(url.encode()).hexdigest()[:16],
                "url": url if url.startswith("http") else DL_BASE + url,
                "lang": lang[:2],
                "release": (item.get("releaseName") or item.get("release_name")
                            or item.get("name") or "")[:60],
                "downloads": item.get("downloads") or item.get("download_count") or 0,
                "feature": query,
                "season": item.get("season") or season,
                "episode": item.get("episode") or episode,
            })
            if len(out) >= limit:
                break
        return out

    def search_features(self, query, limit=8):
        # SubDL er alada title-list endpoint nai; direct search use hobe
        return []

    def download(self, url, dest_dir):
        r = self.session.get(url, timeout=60)
        r.raise_for_status()
        content = r.content
        os.makedirs(dest_dir, exist_ok=True)
        if content[:2] == b"PK":
            zf = zipfile.ZipFile(io.BytesIO(content))
            srts = [n for n in zf.namelist() if n.lower().endswith(".srt")]
            if not srts:
                raise SubDLError("zip er vitore .srt pai nai")
            name = os.path.basename(srts[0])
            path = os.path.join(dest_dir, name)
            with open(path, "wb") as f:
                f.write(zf.read(srts[0]))
            return path
        path = os.path.join(dest_dir, "subdl-subtitle.srt")
        with open(path, "wb") as f:
            f.write(content)
        return path
