"""Upload sources share RawUpload and to_clip."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .. import review
from ..dictionary import Dictionaries
from ..merge import clip_id
from ..model import Clip, Source
from ..title_parser import parse_title

JST = timezone(timedelta(hours=9))


class SourceError(Exception):
    pass


@dataclass
class RawUpload:
    platform: str
    id: str
    url: str
    title: str
    uploaded_at: str | None


def _jst_date(iso: str | None) -> str:
    if not iso:
        return datetime.now(JST).date().isoformat()
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(JST).date().isoformat()


def to_clip(raw: RawUpload, d: Dictionaries) -> Clip:
    p = parse_title(raw.title, d, platform=raw.platform)
    date, ds = (p.date, "title") if p.date else (_jst_date(raw.uploaded_at), "post_time")
    c = Clip(id="", broadcast_date=date, date_source=ds, program=p.program, songs=p.songs,
             performers=p.performers, title_raw=raw.title,
             sources=[Source(raw.platform, raw.id, raw.url, raw.uploaded_at)], tags=list(p.tags))
    c.id = clip_id(c)
    if not p.ok:
        review.add("title_unparsed", c.id, f"{raw.title} → 読めなかった部分: {p.leftover or '日付'}")
    if ds == "post_time":
        review.add("date_post_time", c.id, f"{raw.title} → 放送日は {date}（投稿日より）で合っていますか")
    return c
