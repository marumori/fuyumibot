"""Official fan club pages (guest-readable): schedule, TV/radio backnumber, magazine, 冬美便り.

Only facts (date, program, title, link) are kept. Letter bodies are returned in memory for
mention-matching and never stored.
"""
from __future__ import annotations

import re
import time
from datetime import date, timedelta

from bs4 import BeautifulSoup

from .. import http
from ..jp import normalize
from ..model import Appearance, Letter
from . import SourceError

BASE = "https://fuyumi-fc.com"
_D = r"(\d{4})/(\d{1,2})/(\d{1,2})"
_NOTES = ["再放送", "VTR出演", "VTR", "生放送", "電話出演"]
_KIND = {"テレビ番組": "TV", "ラジオ番組": "ラジオ", "ラジオ放送": "ラジオ"}
_robots_ok: bool | None = None


def parse_dates(s: str) -> list[str]:
    s = normalize(s)
    m = re.search(_D + r"[^〜~]*(?:[〜~]\s*(?:(\d{4})/)?(\d{1,2})/(\d{1,2}))?", s)
    if not m:
        return []
    start = date(int(m[1]), int(m[2]), int(m[3]))
    if not m[5]:
        return [start.isoformat()]
    end = date(int(m[4] or m[1]), int(m[5]), int(m[6]))
    return [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]


def _split_title(t: str) -> tuple[str, str]:
    t = normalize(t)
    m = re.match(r"(.*?)\s*「(.+)」", t)
    return (m[1].strip(), m[2].strip()) if m else ("", t)


def _entries(html: str, box_class: str, body_class: str):
    soup = BeautifulSoup(html, "html.parser")
    for box in soup.select(f"div.{box_class}"):
        d, t, b = box.select_one("td.schedate"), box.select_one("td.schetitle"), box.select_one(f"div.{body_class}")
        if d and t and b:
            yield d.get_text(), t.get_text(), b.get_text("\n")


def _appearances(html: str, box_class: str, body_class: str) -> list[Appearance]:
    out = []
    for dtext, ttext, body in _entries(html, box_class, body_class):
        lines = [normalize(x) for x in body.split("\n") if normalize(x)]
        kind = next((_KIND[k] for k in _KIND if lines and k in lines[0]), None)
        if not kind:
            continue
        info = lines[1] if len(lines) > 1 else ""
        tm = re.search(r"\d{1,2}:\d{2}(?:\s*[〜~]\s*\d{1,2}:\d{2})?", info)
        note = next((n for n in _NOTES if f"※{n}" in info.replace(" ", "")), "")
        broadcaster, program = _split_title(ttext)
        for iso in parse_dates(dtext):
            out.append(Appearance(iso, tm[0].replace(" ", "").replace("~", "〜") if tm else "",
                                  broadcaster, program, kind, note))
    return out


def parse_schedule(html: str) -> list[Appearance]:
    if "schemainbox" not in html:
        raise SourceError("schedule page has no entries (page changed?)")
    return _appearances(html, "schemainbox", "schemain")


def parse_bk_tv(html: str) -> list[Appearance]:
    if "infomainbox" not in html:
        raise SourceError("TV backnumber page has no entries (page changed?)")
    return _appearances(html, "infomainbox", "infomain")


def parse_letters(html: str, year: int, month: int) -> list[tuple[Letter, str]]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for box in soup.select("div.infomainbox[id^=post]"):
        t, d, b = box.select_one("td.newstitle"), box.select_one("td.newsdate"), box.select_one("div.infomain")
        dates = parse_dates(d.get_text()) if d else []
        if not (t and dates):
            continue
        url = f"{BASE}/letter/index.php?y={year}&m={month}#{box['id']}"
        out.append((Letter(dates[0], normalize(t.get_text()), url, {}), normalize(b.get_text(" ")) if b else ""))
    return out


def parse_letter_months(html: str) -> list[tuple[int, int]]:
    return sorted({(int(y), int(m)) for y, m in re.findall(r"\?y=(\d{4})&(?:amp;)?m=(\d{1,2})", html)})


def _allowed() -> bool:
    global _robots_ok
    if _robots_ok is None:
        r = http.get(f"{BASE}/robots.txt")
        disallowed = re.findall(r"(?im)^Disallow:\s*(\S+)", r.text) if r.status_code == 200 else []
        _robots_ok = not any(p in ("/", "/schedule", "/letter") for p in disallowed)
    return _robots_ok


def _fetch(path: str) -> str:
    if not _allowed():
        raise SourceError("robots.txt disallows fan club pages")
    time.sleep(2)
    r = http.get(BASE + path)
    if r.status_code != 200:
        raise SourceError(f"fanclub {path} {r.status_code}")
    r.encoding = "utf-8"
    return r.text


def fetch_schedule() -> list[Appearance]:
    return parse_schedule(_fetch("/schedule/index.php"))


def fetch_bk_tv(year: int) -> list[Appearance]:
    return parse_bk_tv(_fetch(f"/schedule/bk_tv.php?y={year}"))


def fetch_letters(year: int, month: int) -> list[tuple[Letter, str]]:
    return parse_letters(_fetch(f"/letter/index.php?y={year}&m={month}"), year, month)
