"""Find songs / programs / people mentioned in 冬美便り posts; derive FLASH issues."""
from __future__ import annotations

import re

from .dictionary import Dictionaries
from .jp import normalize
from .model import FlashIssue, Letter

_KANJI = re.compile(r"[一-鿿]")


def mentions(body: str, d: Dictionaries) -> dict:
    t = normalize(body)
    quoted = set(re.findall(r"「([^」]+)」", t))
    songs: list[tuple[int, str]] = []
    for s in d.songs:
        for form in [s["title"], *s.get("aliases", [])]:
            f = normalize(form)
            pos = t.find(f)
            if pos < 0:
                continue
            if f in quoted or (len(f) >= 4 and _KANJI.search(f)):
                songs.append((pos, s["id"]))
                break
    progs = []
    for p in d.programs:
        if any(len(normalize(f)) >= 3 and normalize(f) in t for f in [p["name"], *p.get("aliases", [])]):
            progs.append((t.find(normalize(p["name"])) if normalize(p["name"]) in t else 10**6, p["name"]))
    people = [(t.find(normalize(p["name"])), p["name"]) for p in d.performers
              if p["name"] != "坂本冬美" and len(p["name"]) >= 3 and normalize(p["name"]) in t]
    order = lambda xs: list(dict.fromkeys(x for _, x in sorted(xs)))
    return {"songs": order(songs), "programs": order(progs), "people": order(people)}


def flash_from_letters(letters: list[tuple[Letter, str]]) -> list[FlashIssue]:
    out = []
    for letter, body in letters:
        if "モゴモゴ対談" in letter.title or "モゴモゴ対談" in body:
            people = letter.mentions.get("people", [])
            out.append(FlashIssue(letter.date, people[0] if people else "", letter.url))
    return out
