"""Review queue (確認): things the pipeline could not decide alone."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

KINDS = {"title_unparsed", "merge_uncertain", "date_post_time", "no_video", "reading_unreviewed"}
_items: list[dict] = []


def reset(items: list[dict] | None = None) -> None:
    _items.clear()
    _items.extend(items or [])


def add(kind: str, ref: str, detail: str) -> None:
    assert kind in KINDS, kind
    if any(i["kind"] == kind and i["ref"] == ref for i in _items):
        return
    _items.append({"kind": kind, "ref": ref, "detail": detail,
                   "created": datetime.now(timezone.utc).strftime("%Y-%m-%d")})


def resolve(kind: str, ref: str) -> None:
    _items[:] = [i for i in _items if not (i["kind"] == kind and i["ref"] == ref)]


def items() -> list[dict]:
    return list(_items)


def load(path) -> None:
    p = Path(path)
    reset(json.loads(p.read_text("utf-8")) if p.exists() else [])


def save(path) -> None:
    Path(path).write_text(json.dumps(sorted(_items, key=lambda i: (i["kind"], i["ref"])),
                                     ensure_ascii=False, indent=1) + "\n", "utf-8")
