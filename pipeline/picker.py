"""今日のおすすめ: a deterministic 3–5 clip YouTube playlist per date (spec §7)."""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import yaml

from .factcheck import program_matches
from .model import Appearance, Clip, Letter, Pick

SPECIAL_DAYS = Path("data/special_days.yaml")
_CHUSHU = {2026: "09-25", 2027: "09-15", 2028: "10-03", 2029: "09-22", 2030: "09-12",
           2031: "10-01", 2032: "09-19", 2033: "09-08", 2034: "09-27", 2035: "09-16"}
_SEASON = {12: "冬", 1: "冬", 2: "冬", 3: "春", 4: "春", 5: "春", 6: "夏", 7: "夏", 8: "夏", 9: "秋", 10: "秋", 11: "秋"}
_SKIP_NOTES = {"再放送", "VTR", "VTR出演"}


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def movable(rule: str, year: int) -> str | None:
    if rule == "mothers_day":
        return _nth_weekday(year, 5, 6, 2).isoformat()
    if rule == "respect_aged_day":
        return _nth_weekday(year, 9, 0, 3).isoformat()
    if rule == "chushu":
        return f"{year}-{_CHUSHU[year]}" if year in _CHUSHU else None
    return None


def _special_for(day: str) -> dict | None:
    if not SPECIAL_DAYS.exists():
        return None
    for s in yaml.safe_load(SPECIAL_DAYS.read_text("utf-8")) or []:
        r = s["rule"]
        if (len(r) == 5 and r == day[5:]) or movable(r, int(day[:4])) == day:
            return s
    return None


def _choose(day: str, pool: list[Clip]) -> list[str]:
    rng = random.Random(day)
    pool = sorted(pool, key=lambda c: c.id)
    rng.shuffle(pool)
    pool.sort(key=lambda c: c.youtube() is None)   # YouTube first: it plays on by itself
    return [c.id for c in pool[: min(5, max(3, min(4, len(pool))))]]


def pick(day: str, clips: list[Clip], appearances: list[Appearance], letters: list[Letter],
         overrides: dict, history: list[Pick], d) -> Pick:
    if day in overrides:
        o = overrides[day]
        return Pick(day, o["theme"], "今日の選曲", list(o["clip_ids"]))
    since = (date.fromisoformat(day) - timedelta(days=30)).isoformat()
    recent = {i for p in history if since <= p.date < day for i in p.clip_ids}
    ok = [c for c in clips if not c.hidden and c.best_source() and c.id not in recent
          and (d is None or d.is_fuyumi(c.performers))]

    def songs_in(ids):
        return [c for c in ok if set(c.songs) & set(ids)]

    rules = []
    sp = _special_for(day)
    if sp:
        pool = songs_in(sp.get("songs", []))
        pool += [c for c in ok if c not in pool and set(c.performers) & set(sp.get("performers", []))]
        if d is not None:
            pool += [c for c in ok if c not in pool and any(program_matches(c.program, p, d) for p in sp.get("programs", []))]
        rules.append((sp["title"], sp["reason"], pool))
    if d is not None:
        for a in appearances:
            if a.date == day and a.kind == "TV" and a.note not in _SKIP_NOTES:
                pool = [c for c in ok if program_matches(c.program, a.program, d)]
                rules.append(("今夜の放送の前に", f"今日 {a.time} {a.broadcaster}「{a.program}」に出演", pool))
    start = (date.fromisoformat(day) - timedelta(days=3)).isoformat()
    mentioned = [s for lt in letters if start <= lt.date <= day for s in lt.mentions.get("songs", [])]
    rules.append(("冬美さんが便りで触れた曲", "冬美さんが便りで触れた曲", songs_in(mentioned)))
    if d is not None:
        season = _SEASON[int(day[5:7])]
        pool = [c for c in ok if any(season in d.song(s).get("season", []) for s in c.songs if s in d._song_by_id)]
        rules.append((f"{season}のうた", "季節のうた", pool))
    rules.append(("珍しい映像", "珍しい映像", [c for c in ok if c.broadcast_date[:4] <= "2005"]))
    rules.append(("冬美、歌がある", "いろいろな年の冬美さん", ok))
    for title, reason, pool in rules:
        if len(pool) >= 3:
            return Pick(day, title, reason, _choose(day, pool))
    return Pick(day, "冬美、歌がある", "いろいろな年の冬美さん", _choose(day, ok) if ok else [])
