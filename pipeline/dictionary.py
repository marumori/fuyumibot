"""Song / performer / program / caption dictionaries loaded from data/*.yaml."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .jp import normalize

_SEPARATORS = (" ", "＆", "、", "w/", "W/", "with")


def _key(s: str) -> str:
    return normalize(s).replace(" ", "").lower()


@dataclass
class Dictionaries:
    songs: list[dict]
    performers: list[dict]
    programs: list[dict]
    captions: list[str]

    @classmethod
    def load(cls, data_dir) -> "Dictionaries":
        p = Path(data_dir)
        read = lambda name: yaml.safe_load((p / name).read_text("utf-8")) or []
        cap = p / "captions.yaml"
        d = cls(read("songs.yaml"), read("performers.yaml"), read("programs.yaml"),
                read("captions.yaml") if cap.exists() else [])
        d._index()
        return d

    def _index(self) -> None:
        self._song_by_id = {s["id"]: s for s in self.songs}
        self._song_forms: list[tuple[str, str]] = []
        for s in self.songs:
            for form in [s["title"], *s.get("aliases", [])]:
                self._song_forms.append((normalize(form), s["id"]))
        self._song_forms.sort(key=lambda f: -len(f[0]))
        self._perf: dict[str, str] = {}
        for p in self.performers:
            for form in [p["name"], *p.get("aliases", [])]:
                self._perf[normalize(form)] = p["name"]
        self._perf_forms = sorted(self._perf, key=len, reverse=True)
        self._prog: dict[str, str] = {}
        for p in self.programs:
            for form in [p["name"], *p.get("aliases", [])]:
                self._prog[_key(form)] = p["name"]
        self._with_fuyumi = {p["name"] for p in self.performers if p.get("with_fuyumi")}
        self._captions = sorted((normalize(c) for c in self.captions), key=len, reverse=True)

    def song(self, sid: str) -> dict:
        return self._song_by_id[sid]

    def match_songs_longest(self, text: str) -> list[tuple[int, int, str]]:
        """Non-overlapping longest matches, left to right. Matches must sit on token boundaries."""
        t = normalize(text)
        found, i = [], 0
        while i < len(t):
            hit = None
            if i == 0 or t[i - 1] in " 、・(（「":
                for form, sid in self._song_forms:
                    if t.startswith(form, i):
                        end = i + len(form)
                        if end == len(t) or t[end] in " 、)）」":
                            hit = (i, end, sid)
                            break
            if hit:
                found.append(hit)
                i = hit[1]
            else:
                i += 1
        return found

    def performer(self, name: str) -> str | None:
        return self._perf.get(normalize(name))

    def match_performers_from_right(self, text: str) -> tuple[list[str], str]:
        rest = normalize(text)
        found: list[str] = []
        while True:
            stripped = rest.rstrip(" ＆、")
            for sep in ("w/", "W/"):
                if stripped.endswith(sep):
                    stripped = stripped[: -len(sep)].rstrip()
            hit = next((f for f in self._perf_forms if stripped.endswith(f)), None)
            if not hit:
                break
            found.insert(0, self._perf[hit])
            rest = stripped[: -len(hit)]
            rest = rest[:-2] if rest.endswith(("w/", "W/")) else rest
        return found, rest.strip(" ＆、")

    def is_fuyumi(self, performers: list[str]) -> bool:
        """Shown on the site only when the title names 坂本冬美 (alone or with others, or a unit that includes her)."""
        return any(p in self._with_fuyumi for p in performers)

    def program(self, name: str | None) -> str | None:
        if not name:
            return None
        return self._prog.get(_key(name))

    def strip_captions(self, text: str) -> tuple[str, list[str]]:
        t, found = normalize(text), []
        for c in self._captions:
            if c in t:
                found.append(c)
                t = t.replace(c, " ")
        return " ".join(t.split()), found
