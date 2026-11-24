"""Bilibili space 6972913 uploads (public endpoint, no login)."""
from __future__ import annotations

import time
from datetime import datetime, timezone

from .. import http
from . import RawUpload, SourceError

MID = 6972913
API = "https://api.bilibili.com/x/series/recArchivesByKeywords?mid={mid}&keywords=&ps=50&pn={pn}"


def parse_page(js: dict) -> list[RawUpload]:
    if js.get("code") != 0:
        raise SourceError(f"bilibili code {js.get('code')}: {js.get('message')}")
    out = []
    for a in (js.get("data") or {}).get("archives") or []:
        ts = datetime.fromtimestamp(a["pubdate"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        out.append(RawUpload("bilibili", a["bvid"], f"https://www.bilibili.com/video/{a['bvid']}", a["title"], ts))
    return out


def _page(pn: int) -> list[RawUpload]:
    r = http.get(API.format(mid=MID, pn=pn), headers={"User-Agent": http.BROWSER_UA,
                                                       "Referer": f"https://space.bilibili.com/{MID}"})
    if r.status_code != 200:
        raise SourceError(f"bilibili http {r.status_code}")
    return parse_page(r.json())


def fetch_recent(pages: int = 1) -> list[RawUpload]:
    out = []
    for pn in range(1, pages + 1):
        out += _page(pn)
    return out


def fetch_all() -> list[RawUpload]:
    """Page through all uploads; stop politely (keeping what we have) if Bilibili blocks us."""
    out, pn = [], 1
    while True:
        try:
            page = _page(pn)
        except SourceError as e:
            if not out:
                raise
            print(f"bilibili stopped at page {pn}: {e}")
            return out
        if not page:
            return out
        out += page
        pn += 1
        time.sleep(3)
