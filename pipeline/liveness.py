"""Weekly check that each upload still exists; dead sources fall back, clips with none are hidden."""
from __future__ import annotations

import time
from typing import Callable

from . import http
from .model import Clip, Source
from .sources import xembed


def youtube_alive(s: Source) -> bool | None:
    r = http.get("https://www.youtube.com/oembed", params={"url": s.url, "format": "json"})
    if r.status_code == 200:
        return True
    return False if r.status_code in (401, 403, 404) else None


def bilibili_alive(s: Source) -> bool | None:
    r = http.get("https://api.bilibili.com/x/web-interface/view", params={"bvid": s.id},
                 headers={"User-Agent": http.BROWSER_UA})
    if r.status_code != 200:
        return None
    code = r.json().get("code")
    return True if code == 0 else (False if code in (-404, 62002, 62004) else None)


def x_alive(s: Source) -> bool | None:
    return xembed.status(s.id)


DEFAULT_CHECKERS: dict[str, Callable[[Source], bool | None]] = {
    "youtube": youtube_alive, "bilibili": bilibili_alive, "x": x_alive}


AUTO = "auto_hidden"      # hidden by this check; unhidden again when a source comes back
OWNER = "owner_hidden"    # hidden by the owner's answer; never unhidden automatically


def check(clips: list[Clip], checkers=None, limit: int = 300, offset: int = 0, sleep: float = 1.0) -> int:
    """Check up to `limit` sources starting at `offset` (wrapping). Returns the next offset.
    A checker returning None means "unknown" and leaves the source as it was."""
    checkers = checkers or DEFAULT_CHECKERS
    pairs = [(c, s) for c in clips for s in c.sources]
    if not pairs:
        return 0
    offset %= len(pairs)
    window = (pairs[offset:] + pairs[:offset])[:limit]
    for c, s in window:
        fn = checkers.get(s.platform)
        if not fn:
            continue
        try:
            alive = fn(s)
        except Exception:  # noqa: BLE001
            alive = None
        if alive is not None:
            s.alive = alive
        if sleep:
            time.sleep(sleep)
    for c in {id(c): c for c, _ in window}.values():
        playable = any(s.alive and s.has_video for s in c.sources)
        if not playable and not c.hidden:
            c.hidden = True
            c.tags.append(AUTO)
        elif playable and AUTO in c.tags and OWNER not in c.tags:
            c.hidden = False
            c.tags.remove(AUTO)
    return (offset + len(window)) % len(pairs)
