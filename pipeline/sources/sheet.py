"""The owner's Google Sheet (published as CSV): 追加 / おすすめ / 確認 tabs."""
from __future__ import annotations

import csv
import io
import re
from urllib.parse import parse_qs, urlparse

from .. import http, review
from ..dictionary import Dictionaries
from ..jp import normalize
from ..model import Clip

ADD_HEADERS = ["リンク", "メモ"]
PICK_HEADERS = ["日付", "テーマ", "リンク1", "リンク2", "リンク3", "リンク4", "リンク5"]
REVIEW_HEADERS = ["種類", "対象", "内容", "答え"]


class SheetError(Exception):
    pass


def parse_csv(text: str, expected_headers: list[str]) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    if [h.strip() for h in (reader.fieldnames or [])][: len(expected_headers)] != expected_headers:
        raise SheetError(f"見出しが違います: {reader.fieldnames} (期待: {expected_headers})")
    return [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in reader]


def read_csv(url: str, expected_headers: list[str]) -> list[dict]:
    r = http.get(url)
    if r.status_code != 200:
        raise SheetError(f"sheet {r.status_code}")
    r.encoding = "utf-8"
    return parse_csv(r.text, expected_headers)


def parse_link(link: str) -> tuple[str, str, str] | None:
    u = urlparse(link.strip())
    host = (u.netloc or "").lower().removeprefix("www.").removeprefix("m.")
    if host in ("x.com", "twitter.com", "mobile.twitter.com"):
        m = re.match(r"/([^/]+)/status/(\d+)", u.path)
        return ("x", m[2], f"https://x.com/{m[1]}/status/{m[2]}") if m else None
    if host == "youtu.be":
        vid = u.path.strip("/")
        return ("youtube", vid, f"https://www.youtube.com/watch?v={vid}") if vid else None
    if host == "youtube.com":
        vid = (parse_qs(u.query).get("v") or [""])[0] or (u.path.split("/shorts/")[-1] if "/shorts/" in u.path else "")
        return ("youtube", vid, f"https://www.youtube.com/watch?v={vid}") if vid else None
    if host == "bilibili.com":
        m = re.search(r"/video/(BV\w+)", u.path)
        return ("bilibili", m[1], f"https://www.bilibili.com/video/{m[1]}") if m else None
    return None


def links_to_sources(rows: list[dict]) -> list[tuple[str, str, str]]:
    return [p for r in rows if (p := parse_link(r.get("リンク", "")))]


def _date(s: str) -> str | None:
    m = re.match(r"(\d{4})\D?(\d{1,2})\D?(\d{1,2})", normalize(s))
    return f"{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}" if m else None


def overrides(rows: list[dict], clips: list[Clip]) -> dict[str, dict]:
    by_src = {(s.platform, s.id): c.id for c in clips for s in c.sources}
    out = {}
    for r in rows:
        day = _date(r.get("日付", ""))
        ids = [by_src.get(p[:2]) for k in PICK_HEADERS[2:] if (p := parse_link(r.get(k, "")))]
        ids = [i for i in ids if i]
        if day and ids:
            out[day] = {"theme": r.get("テーマ") or "今日の選曲", "clip_ids": ids}
    return out


def apply_answers(rows: list[dict], clips: list[Clip], d: Dictionaries) -> dict[str, str]:
    """Apply the owner's answers. Returns {song_id: reading} for reading answers."""
    by_id = {c.id: c for c in clips}
    readings = {}
    for r in rows:
        kind, ref, ans = r.get("種類"), r.get("対象"), normalize(r.get("答え", ""))
        if not ans:
            continue
        c = by_id.get(ref)
        if kind == "reading_unreviewed":
            readings[ref] = ans
        elif c and kind == "no_video" and ans in ("表示", "はい"):
            c.hidden = False
        elif c and kind == "no_video" and ans in ("非表示", "いいえ"):
            c.hidden = True
        elif c and kind == "date_post_time":
            day = _date(ans)
            if day:
                c.broadcast_date = day
            if day or ans == "はい":
                c.date_source = "title"
        elif c and kind == "title_unparsed":
            parts = [p.strip() for p in re.split(r"[;；]", ans)]
            songs = [m[2] for m in d.match_songs_longest(parts[0])] if parts and parts[0] else []
            c.songs = songs
            if len(parts) > 1:
                c.performers = [p for p in re.split(r"[、,＆]", parts[1]) if p]
            if len(parts) > 2 and _date(parts[2]):
                c.broadcast_date, c.date_source = _date(parts[2]), "title"
        else:
            continue
        review.resolve(kind, ref)
    return readings
