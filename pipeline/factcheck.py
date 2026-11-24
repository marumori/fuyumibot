"""Match clips to fan-club TV/radio records (✓ 放送日確認済み)."""
from __future__ import annotations

from .dictionary import Dictionaries
from datetime import date, timedelta

from .model import Appearance, Clip, ForumTopic


def _k(s: str) -> str:
    return s.replace(" ", "").replace("、", "").replace("・", "").lower()


def program_matches(clip_program: str | None, app_program: str, d: Dictionaries) -> bool:
    if not clip_program:
        return False
    a = _k(d.program(clip_program) or clip_program)
    b = _k(d.program(app_program) or app_program)
    return bool(a and b) and (a == b or a in b or b in a)


FORUM_BEFORE, FORUM_AFTER = 3, 1   # fans post announcements a few days ahead, reports the day after


def verify(clips: list[Clip], appearances: list[Appearance], d: Dictionaries, forum: list[ForumTopic] = ()) -> None:
    """✓ when the fan-club TV record (or, failing that, a fan-forum topic near the date) names the same program."""
    by_date: dict[str, list[Appearance]] = {}
    for a in appearances:
        by_date.setdefault(a.date, []).append(a)
    topics_by_date: dict[str, list[ForumTopic]] = {}
    for t in forum:
        if t.date:
            topics_by_date.setdefault(t.date, []).append(t)
    for c in clips:
        c.verified = None
        if c.date_source != "title":
            continue
        for a in by_date.get(c.broadcast_date, []):
            if program_matches(c.program, a.program, d):
                c.verified = {"broadcaster": a.broadcaster, "program": a.program, "note": a.note, "source": "fanclub"}
                break
        if c.verified or not c.program:
            continue
        day = date.fromisoformat(c.broadcast_date)
        for k in range(-FORUM_BEFORE, FORUM_AFTER + 1):
            hit = next((t for t in topics_by_date.get((day + timedelta(days=k)).isoformat(), [])
                        if program_matches(c.program, t.title, d)), None)
            if hit:
                c.verified = {"broadcaster": "", "program": hit.title, "note": "", "source": "fan_forum"}
                break
