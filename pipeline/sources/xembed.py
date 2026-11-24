"""Read one X post by id from X's public embed data (free, unofficial; may stop working)."""
from __future__ import annotations

import html
import re

from .. import http
from . import RawUpload

API = "https://cdn.syndication.twimg.com/tweet-result?id={id}&token=a"


def _clean(text: str) -> str:
    t = html.unescape(text)
    t = re.sub(r"https?://t\.co/\S+", "", t).strip()
    m = re.search(r"(\d{8})\s*(.*)$", t)
    if m and m.group(2).strip() and not t.startswith("["):
        t = f"[{m.group(2).strip()}] {t[: m.start()].strip()} {m.group(1)}"
    return t


def from_json(js: dict) -> RawUpload:
    tid, user = js["id_str"], js.get("user", {}).get("screen_name", "jounotakeuchi")
    media = js.get("mediaDetails") or []
    return RawUpload("x", tid, f"https://x.com/{user}/status/{tid}", _clean(js.get("text", "")),
                     js["created_at"].replace(".000Z", "Z"), any(m.get("type") == "video" for m in media))


def status(tweet_id: str) -> bool | None:
    """True = exists, False = clearly deleted (404 / tombstone), None = unknown (rate limit, network)."""
    try:
        r = http.get(API.format(id=tweet_id))
        if r.status_code == 404:
            return False
        if r.status_code != 200:
            return None
        js = r.json()
        if js.get("__typename") == "TweetTombstone":
            return False
        return True if js.get("id_str") else None
    except Exception:
        return None


def fetch(tweet_id: str) -> RawUpload | None:
    try:
        r = http.get(API.format(id=tweet_id))
        if r.status_code != 200:
            return None
        return from_json(r.json())
    except Exception:
        return None
