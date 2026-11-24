"""smart-flash.jp 坂本冬美 tag: article list (title, date, issue, people) and songs mentioned.

Only facts and links are stored. Article text is read in memory to find song names and is never saved.
(The WordPress API answers 403, so the public tag pages are used; robots.txt allows them.)
"""
from __future__ import annotations

import re
import time
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup

from .. import http
from ..jp import normalize
from ..model import FlashArticle
from . import SourceError

TAG = "https://smart-flash.jp/tag/%e5%9d%82%e6%9c%ac%e5%86%ac%e7%be%8e/"
SELF = "坂本冬美"


def _clean_url(u: str) -> str:
    p = urlsplit(u)
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


def parse_tag_page(html: str) -> list[FlashArticle]:
    if "itemList" not in html:
        raise SourceError("FLASH tag page has no article list (page changed?)")
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for li in soup.select("ul.itemList > li"):
        a = li.select_one("h2.itemText a")
        d = li.select_one("p.date")
        m = re.search(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", d.get_text() if d else "")
        if not (a and m):
            continue
        people = [normalize(t.get_text()) for t in li.select("ul.tagList span")]
        issue = li.select_one("div.sourceNews a")
        out.append(FlashArticle(f"{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}", normalize(a.get_text()), _clean_url(a["href"]),
                                normalize(issue.get_text()) if issue else "", [p for p in people if p != SELF]))
    return out


def last_page(html: str) -> int:
    nums = [int(n) for n in re.findall(r"/tag/[^\"/]+/(\d+)/", html)]
    return max(nums, default=1)


def parse_article_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    body = soup.select_one("div.text")
    return normalize(body.get_text(" ")) if body else ""


def _get(url: str) -> str:
    time.sleep(2)
    r = http.get(url)
    if r.status_code != 200:
        raise SourceError(f"FLASH {r.status_code} {url}")
    r.encoding = "utf-8"
    return r.text


def fetch_tag_page(n: int = 1) -> tuple[list[FlashArticle], int]:
    html = _get(TAG if n == 1 else f"{TAG}{n}/")
    return parse_tag_page(html), last_page(html)


def fetch_article_text(url: str) -> str:
    return parse_article_text(_get(url))
