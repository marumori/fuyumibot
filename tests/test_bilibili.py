import json
from pathlib import Path

import pytest

from pipeline.sources import SourceError
from pipeline.sources.bilibili import parse_page


def test_parse_page():
    js = json.loads(Path("tests/fixtures/bili_page1.json").read_text("utf-8"))
    ups = parse_page(js)
    assert len(ups) == 50
    assert ups[0].id == "BV1szWZ6NEDE"
    assert ups[0].url == "https://www.bilibili.com/video/BV1szWZ6NEDE"
    assert ups[0].title == "ひらり　坂本冬美 20261116"
    assert ups[0].uploaded_at.endswith("Z")


def test_error_code_raises():
    with pytest.raises(SourceError):
        parse_page({"code": -352, "message": "風控校验失败"})


def test_empty_page():
    assert parse_page({"code": 0, "data": {"archives": []}}) == []


def test_fetch_all_returns_partial_when_blocked(monkeypatch):
    from pipeline.sources import RawUpload, bilibili
    pages = {1: [RawUpload("bilibili", "BV1", "u", "t", None)]}

    def fake(pn):
        if pn in pages:
            return pages[pn]
        raise SourceError("bilibili http 412")
    monkeypatch.setattr(bilibili, "_page", fake)
    monkeypatch.setattr(bilibili.time, "sleep", lambda s: None)
    assert [u.id for u in bilibili.fetch_all()] == ["BV1"]
