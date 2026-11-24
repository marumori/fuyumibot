"""Match clips to fan-club TV/radio records (✓ 放送日確認済み)."""
from __future__ import annotations

from .dictionary import Dictionaries
from .model import Appearance, Clip


def _k(s: str) -> str:
    return s.replace(" ", "").replace("、", "").replace("・", "").lower()


def program_matches(clip_program: str | None, app_program: str, d: Dictionaries) -> bool:
    if not clip_program:
        return False
    a = _k(d.program(clip_program) or clip_program)
    b = _k(d.program(app_program) or app_program)
    return bool(a and b) and (a == b or a in b or b in a)


def verify(clips: list[Clip], appearances: list[Appearance], d: Dictionaries) -> None:
    by_date: dict[str, list[Appearance]] = {}
    for a in appearances:
        by_date.setdefault(a.date, []).append(a)
    for c in clips:
        c.verified = None
        if c.date_source != "title":
            continue
        for a in by_date.get(c.broadcast_date, []):
            if program_matches(c.program, a.program, d):
                c.verified = {"broadcaster": a.broadcaster, "program": a.program, "note": a.note}
                break
