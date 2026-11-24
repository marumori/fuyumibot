"""u-fuyumi.net (アンダー冬美) fan forum — used only behind the scenes to confirm TV broadcasts.

Stored: topic title, link, date of the first post. Never stored or shown: member names, post text.
Requests are spread out (2 s apart, limited per run) to be gentle on a small fan-run site.
"""
from __future__ import annotations

import re
import time

from bs4 import BeautifulSoup

from .. import http
from ..jp import normalize
from ..model import ForumTopic
from . import SourceError

LISTING = "https://u-fuyumi.net/forums/forum/forum-779"


def parse_listing(html: str) -> list[ForumTopic]:
    if "bbp-topics" not in html:
        raise SourceError("forum listing has no topics (page changed?)")
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for a in soup.select("ul.bbp-topics a.bbp-topic-permalink"):
        out.append(ForumTopic(normalize(a.get_text()), a["href"].split("?")[0]))
    return out


def last_page(html: str) -> int:
    return max((int(n) for n in re.findall(r"/forum-779/page/(\d+)", html)), default=1)


def parse_topic_date(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    d = soup.select_one("span.bbp-reply-post-date, span.bbp-topic-post-date")
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", d.get_text() if d else "")
    return f"{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}" if m else None


def _get(url: str) -> str:
    time.sleep(2)
    r = http.get(url)
    if r.status_code != 200:
        raise SourceError(f"forum {r.status_code} {url}")
    r.encoding = "utf-8"
    return r.text


def fetch_listing(n: int = 1) -> tuple[list[ForumTopic], int]:
    html = _get(LISTING if n == 1 else f"{LISTING}/page/{n}")
    return parse_listing(html), last_page(html)


def fetch_topic_date(url: str) -> str | None:
    return parse_topic_date(_get(url))
