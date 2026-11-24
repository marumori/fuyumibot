"""Data model and stable JSON persistence."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Literal

PLATFORM_ORDER = {"youtube": 0, "bilibili": 1, "x": 2}


@dataclass
class Source:
    platform: Literal["youtube", "bilibili", "x"]
    id: str
    url: str
    uploaded_at: str | None = None
    has_video: bool = True
    alive: bool = True


@dataclass
class Clip:
    id: str
    broadcast_date: str
    date_source: Literal["title", "post_time"]
    program: str | None
    songs: list[str]
    performers: list[str]
    title_raw: str
    sources: list[Source]
    verified: dict | None = None
    tags: list[str] = field(default_factory=list)
    hidden: bool = False

    def best_source(self) -> Source | None:
        live = [s for s in self.sources if s.alive]
        return min(live, key=lambda s: PLATFORM_ORDER[s.platform]) if live else None

    def youtube(self) -> Source | None:
        return next((s for s in self.sources if s.platform == "youtube" and s.alive), None)

    @classmethod
    def from_dict(cls, d: dict) -> "Clip":
        d = dict(d)
        d["sources"] = [Source(**s) for s in d.get("sources", [])]
        return cls(**d)


@dataclass
class Appearance:
    date: str
    time: str
    broadcaster: str
    program: str
    kind: str
    note: str = ""


@dataclass
class Letter:
    date: str
    title: str
    url: str
    mentions: dict = field(default_factory=dict)


@dataclass
class FlashIssue:
    issue_date: str
    guest: str
    letter_url: str


@dataclass
class Pick:
    date: str
    theme_title: str
    reason: str
    clip_ids: list[str]


def _from(cls, d):
    if hasattr(cls, "from_dict"):
        return cls.from_dict(d)
    names = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in d.items() if k in names})


def load(path, cls) -> list:
    p = Path(path)
    if not p.exists():
        return []
    return [_from(cls, d) for d in json.loads(p.read_text("utf-8"))]


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1) + "\n"


def save(path, items) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dumps([asdict(i) if hasattr(i, "__dataclass_fields__") else i for i in items]), "utf-8")
