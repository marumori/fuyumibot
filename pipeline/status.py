"""Per-source health (data/status.json): last-good fallback and failure alerts."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

PATH = Path("data/status.json")
JST = timezone(timedelta(hours=9))
_data: dict = {}


def reset() -> None:
    _data.clear()
    _data.update({"sources": {}, "cursors": {}})


def load() -> None:
    reset()
    if Path(PATH).exists():
        _data.update(json.loads(Path(PATH).read_text("utf-8")))
        _data.setdefault("sources", {})
        _data.setdefault("cursors", {})


def save() -> None:
    Path(PATH).write_text(json.dumps(_data, ensure_ascii=False, indent=1, sort_keys=True) + "\n", "utf-8")


def data() -> dict:
    return _data


def _rec(name: str) -> dict:
    return _data.setdefault("sources", {}).setdefault(name, {"last_ok": None, "last_error": None, "consecutive_failures": 0})


def guard(name: str, fn, previous_count: int):
    """Run fn(). On error, or a suspicious drop (>20% fewer rows than before), return None so the
    caller keeps its last-good data."""
    rec = _rec(name)
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M")
    try:
        result = fn()
        n = len(result)
        if previous_count >= 5 and n < 0.8 * previous_count:
            raise ValueError(f"件数が急に減少しました ({previous_count}→{n})")
    except Exception as e:  # noqa: BLE001 — every source failure is handled the same way
        rec["last_error"] = f"{now} {type(e).__name__}: {e}"
        rec["consecutive_failures"] += 1
        return None
    rec["last_ok"] = now
    rec["consecutive_failures"] = 0
    return result


def needs_alert() -> list[str]:
    return sorted(n for n, r in _data.get("sources", {}).items() if r["consecutive_failures"] >= 3)
