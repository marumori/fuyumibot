"""One-time import of the owner's existing list (data/seed/x_table.md)."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from . import review
from .dictionary import Dictionaries
from .merge import clip_id, merge
from .model import Clip, Source
from .title_parser import parse_title

COLS = ["mmdd", "yyyy", "title", "x_url", "posted_utc", "relation", "bili_url", "note"]
JST = timezone(timedelta(hours=9))


def read_rows(path) -> list[dict]:
    rows = []
    for line in open(path, encoding="utf-8"):
        if re.match(r"\| \d\d-\d\d \|", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(dict(zip(COLS, cells)))
    return rows


def _utc(s: str) -> datetime:
    return datetime.strptime(s.replace(" UTC", ""), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def row_to_clip(row: dict, d: Dictionaries) -> Clip:
    p = parse_title(row["title"], d)
    posted = _utc(row["posted_utc"])
    note = row.get("note", "")
    if "日期取自發文時間" in note:
        date, date_source = posted.astimezone(JST).date().isoformat(), "post_time"
    else:
        date, date_source = p.date or posted.astimezone(JST).date().isoformat(), "title" if p.date else "post_time"
    x_id = row["x_url"].rstrip("/").split("/")[-1]
    has_video = "未偵測到原生影片" not in note
    sources = [Source("x", x_id, row["x_url"], posted.strftime("%Y-%m-%dT%H:%M:%SZ"), has_video)]
    if row.get("bili_url") and row.get("relation") in ("同一條", "疑似同一條"):
        bv = row["bili_url"].rstrip("/").split("/")[-1]
        sources.append(Source("bilibili", bv, row["bili_url"]))
    c = Clip(id="", broadcast_date=date, date_source=date_source, program=p.program, songs=p.songs,
             performers=p.performers, title_raw=row["title"], sources=sources, tags=list(p.tags),
             hidden=not any(s.has_video for s in sources))
    c.id = clip_id(c)
    if not p.ok:
        review.add("title_unparsed", c.id, f"{row['title']} → 読めなかった部分: {p.leftover}")
    if date_source == "post_time":
        review.add("date_post_time", c.id, f"{row['title']} → 放送日は {date}（投稿日より）で合っていますか")
    if c.hidden:
        review.add("no_video", c.id, f"{row['title']} → 動画が見つかりません。表示しますか")
    if row.get("relation") == "疑似同一條":
        review.add("merge_uncertain", c.id, f"{row['title']} ↔ {row['bili_url']} は同じ映像ですか")
    return c


def import_seed(path, d: Dictionaries) -> list[Clip]:
    return merge([], [row_to_clip(r, d) for r in read_rows(path)], d.program)
