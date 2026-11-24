"""Parse upload titles: `[番組] 曲、曲 出演者＆出演者 w/ゲスト YYYYMMDD`."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from .dictionary import Dictionaries
from .jp import normalize

_GROUP = re.compile(r"^\s*(?:\[([^\]]*)\]|【([^】]*)】)\s*")
_DATE = re.compile(r"(\d{8})(?!.*\d{8})")
_NO_SONG = "(無曲名)"
_BILI_NOISE = re.compile(r"(\(含talking\)|\bcut\b|\btalking\b)", re.I)


@dataclass
class ParsedTitle:
    program: str | None
    songs: list[str]
    performers: list[str]
    date: str | None
    leftover: str
    ok: bool
    tags: list[str] = field(default_factory=list)


def _iso(digits: str) -> str | None:
    try:
        return date(int(digits[:4]), int(digits[4:6]), int(digits[6:])).isoformat()
    except ValueError:
        return None


def parse_title(title: str, d: Dictionaries, platform: str = "x") -> ParsedTitle:
    t = normalize(title)
    if platform == "bilibili":
        t = _BILI_NOISE.sub(" ", t.replace("彥", "彦"))
    groups = []
    while (m := _GROUP.match(t)):
        g = (m.group(1) or m.group(2) or "").strip()
        if g:
            groups.append(g)
        t = t[m.end():]
    program, tags = (groups[0], groups[1:]) if groups else (None, [])

    m = _DATE.search(t)
    iso = _iso(m.group(1)) if m else None
    body = t[: m.start()] + " " + t[m.end():] if m else t

    body = body.replace(_NO_SONG, " ")
    performers, rest = d.match_performers_from_right(body)

    matches = d.match_songs_longest(rest)
    songs = [sid for _, _, sid in matches]
    leftover = normalize(rest)
    for start, end, _ in sorted(matches, reverse=True):
        leftover = leftover[:start] + " " + leftover[end:]
    leftover, caps = d.strip_captions(leftover)
    tags += caps
    leftover = re.sub(r"[\s、・＆()]+", " ", leftover).strip()
    return ParsedTitle(program, songs, performers, iso, leftover, bool(iso) and not leftover, tags)
