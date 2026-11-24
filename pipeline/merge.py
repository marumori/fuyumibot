"""Cross-platform merge / de-duplication of clips."""
from __future__ import annotations

import hashlib
from datetime import datetime

from .model import Clip


def clip_id(c: Clip) -> str:
    first = f"{c.sources[0].platform}:{c.sources[0].id}" if c.sources else ""
    h = hashlib.sha1(f"{c.title_raw}|{first}".encode("utf-8")).hexdigest()[:6]
    return f"{c.broadcast_date}-{c.songs[0] if c.songs else 'talk'}-{h}"


def _keys(c: Clip) -> set[tuple[str, str]]:
    return {(s.platform, s.id) for s in c.sources}


def _ts(s) -> datetime | None:
    try:
        return datetime.fromisoformat(s.uploaded_at.replace("Z", "+00:00")) if s.uploaded_at else None
    except ValueError:
        return None


def _same_performance(a: Clip, b: Clip, canon=lambda p: p) -> bool:
    if a.broadcast_date != b.broadcast_date or not a.songs or not b.songs or a.songs[0] != b.songs[0]:
        return False
    same_prog = a.program and b.program and canon(a.program) == canon(b.program)
    return bool(same_prog or set(a.performers) & set(b.performers))


def _near_duplicate_post(a: Clip, b: Clip) -> bool:
    if a.title_raw != b.title_raw or not a.songs:
        return False
    xa = [_ts(s) for s in a.sources if s.platform == "x" and _ts(s)]
    xb = [_ts(s) for s in b.sources if s.platform == "x" and _ts(s)]
    return any(abs((p - q).total_seconds()) < 86400 for p in xa for q in xb)


def _absorb(target: Clip, other: Clip) -> None:
    have = _keys(target)
    for s in other.sources:
        if (s.platform, s.id) not in have:
            target.sources.append(s)
        else:
            for i, t in enumerate(target.sources):
                if (t.platform, t.id) == (s.platform, s.id):
                    target.sources[i] = s
    if target.date_source == "post_time" and other.date_source == "title":
        target.broadcast_date, target.date_source = other.broadcast_date, "title"
    target.hidden = target.hidden and other.hidden
    for tag in other.tags:
        if tag not in target.tags:
            target.tags.append(tag)


def merge(existing: list[Clip], incoming: list[Clip], canon_program=lambda p: p) -> list[Clip]:
    out = list(existing)
    for c in incoming:
        target = next((e for e in out if _keys(e) & _keys(c)), None)
        if target is None:
            target = next((e for e in out if _same_performance(e, c, canon_program)), None)
        if target is None:
            target = next((e for e in out if _near_duplicate_post(e, c)), None)
        if target is None:
            out.append(c)
        else:
            _absorb(target, c)
    return out
