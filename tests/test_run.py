import json

import pytest

from pipeline import run, status
from pipeline.model import Appearance, Clip, load, save
from pipeline.sources import RawUpload, SourceError
from tests.helpers import mk


@pytest.fixture
def env(tmp_path, monkeypatch):
    import shutil
    for f in ["songs.yaml", "performers.yaml", "programs.yaml", "captions.yaml", "special_days.yaml"]:
        shutil.copy(f"data/{f}", tmp_path / f)
    monkeypatch.setattr(run, "DATA", tmp_path)
    monkeypatch.setattr(status, "PATH", tmp_path / "status.json")
    monkeypatch.setattr(run, "build_site", lambda *a, **k: None)
    status.reset()
    save(tmp_path / "clips.json", [mk("2020-01-01", ["hirari"], n=str(i)) for i in range(3)])
    calls = {}
    monkeypatch.setattr(run, "fetch_youtube", lambda: [RawUpload("youtube", "NEW1", "https://www.youtube.com/watch?v=NEW1", "ひらり　坂本冬美 20261116", "2026-11-17T01:00:00Z")])
    monkeypatch.setattr(run, "fetch_bilibili", lambda: (_ for _ in ()).throw(SourceError("bilibili http 412")))
    monkeypatch.setattr(run, "fetch_schedule", lambda: [Appearance("2026-11-24", "7:00〜7:54", "BS-TBS", "おはよう！僕らの名曲ショー", "TV", "VTR")])
    monkeypatch.setattr(run, "fetch_bk_tv", lambda y: [Appearance("2026-11-16", "", "NHK総合", "はやウタ", "TV", "")])
    monkeypatch.setattr(run, "fetch_letters", lambda y, m: [])
    monkeypatch.setattr(run, "read_sheet", lambda key, headers: [])
    from pipeline.model import FlashArticle
    monkeypatch.setattr(run, "fetch_flash_page", lambda n=1: ([FlashArticle("2026-11-21", "対談", "https://smart-flash.jp/e/1/", "", ["大竹しのぶ"])], 8))
    monkeypatch.setattr(run, "fetch_flash_text", lambda url: "「夜桜お七」の話")
    return tmp_path


def test_daily_ingests_and_survives_bilibili_block(env):
    run.daily("2026-11-24")
    clips = load(env / "clips.json", Clip)
    new = [c for c in clips if any(s.id == "NEW1" for s in c.sources)]
    assert new and new[0].broadcast_date == "2026-11-16"
    st = json.loads((env / "status.json").read_text())
    assert st["sources"]["bilibili"]["consecutive_failures"] == 1
    assert st["sources"]["youtube"]["consecutive_failures"] == 0
    picks = json.loads((env / "picks.json").read_text())
    assert {p["date"] for p in picks} >= {"2026-11-24", "2026-11-25"}


def test_daily_keeps_appearances_when_bk_tv_shrinks(env, monkeypatch):
    save(env / "appearances.json", [Appearance(f"2026-01-{i:02d}", "", "X", f"p{i}", "TV", "") for i in range(1, 29)])
    run.daily("2026-11-24")
    apps = load(env / "appearances.json", Appearance)
    assert len([a for a in apps if a.date.startswith("2026-01")]) == 28


def test_daily_verifies_new_clip(env):
    run.daily("2026-11-24")
    # はやウタ has no program in the title, so no ✓ — the clip still exists
    clips = load(env / "clips.json", Clip)
    assert all(c.verified is None for c in clips)


def test_daily_sheet_x_link(env, monkeypatch):
    monkeypatch.setattr(run, "read_sheet", lambda key, headers: [{"リンク": "https://x.com/jounotakeuchi/status/77", "メモ": ""}] if key == "SHEET_ADD_CSV" else [])
    monkeypatch.setattr(run, "fetch_x", lambda tid: RawUpload("x", tid, f"https://x.com/jounotakeuchi/status/{tid}", "[紅白] 夜桜お七 坂本冬美 20251231", "2025-12-31T16:06:57Z"))
    run.daily("2026-11-24")
    clips = load(env / "clips.json", Clip)
    assert any(s.id == "77" for c in clips for s in c.sources)


def test_daily_reads_flash_and_song_mentions(env):
    from pipeline.model import FlashArticle
    run.daily("2026-11-24")
    [a] = load(env / "flash_articles.json", FlashArticle)
    assert a.mentions["songs"] == ["yozakura-oshichi"]
    assert "夜桜お七" not in (env / "flash_articles.json").read_text("utf-8").replace("yozakura", "")


def test_daily_survives_flash_failure(env, monkeypatch):
    def boom(*a):
        raise OSError("down")
    monkeypatch.setattr(run, "fetch_flash_page", boom)
    run.daily("2026-11-24")
    assert status.data()["sources"]["flash"]["consecutive_failures"] == 1
