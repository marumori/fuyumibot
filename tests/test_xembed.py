import json
from pathlib import Path

from pipeline.sources import to_clip
from pipeline.sources import xembed


def test_from_json_moves_trailing_program_to_bracket():
    raw = xembed.from_json(json.loads(Path("tests/fixtures/x_tweet.json").read_text("utf-8")))
    assert raw.title.startswith("[紅白] 夜桜お七")
    assert "t.co" not in raw.title and "&amp;" not in raw.title
    assert raw.url == "https://x.com/jounotakeuchi/status/2006396667155919096"
    assert raw.uploaded_at == "2025-12-31T16:06:57Z"
    assert raw.has_video


def test_to_clip_from_x(d):
    raw = xembed.from_json(json.loads(Path("tests/fixtures/x_tweet.json").read_text("utf-8")))
    c = to_clip(raw, d)
    assert c.songs == ["yozakura-oshichi"] and c.performers == ["坂本冬美", "M!LK"] and c.program == "紅白"


def test_fetch_failure_returns_none(monkeypatch):
    class R:
        status_code = 404
    monkeypatch.setattr(xembed.http, "get", lambda *a, **k: R())
    assert xembed.fetch("1") is None


def test_fetch_exception_returns_none(monkeypatch):
    def boom(*a, **k):
        raise OSError("net")
    monkeypatch.setattr(xembed.http, "get", boom)
    assert xembed.fetch("1") is None
