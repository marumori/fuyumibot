"""Regression tests for the final-review findings."""
import pytest

from pipeline import liveness, run, status
from pipeline.model import Appearance, Clip, load, save
from pipeline.sources import SourceError, sheet, xembed, youtube
from pipeline.sources import fanclub as fc
from tests.helpers import mk
from tests.test_run import env  # noqa: F401  (fixture)


def test_bk_tv_does_not_delete_todays_schedule_entry(env, monkeypatch):
    monkeypatch.setattr(run, "fetch_schedule", lambda: [Appearance("2026-11-24", "7:00〜7:54", "BS-TBS", "名曲ショー", "TV", "")])
    run.daily("2026-11-24")
    apps = load(env / "appearances.json", Appearance)
    assert any(a.date == "2026-11-24" and a.program == "名曲ショー" for a in apps)


def test_bad_sheet_link_does_not_stop_daily(env, monkeypatch):
    monkeypatch.setattr(run, "read_sheet", lambda key, h: [{"リンク": "https://youtu.be/BAD", "メモ": ""}] if key == "SHEET_ADD_CSV" else [])

    def boom(*a):
        raise OSError("timeout")
    monkeypatch.setattr(run, "fetch_link", boom)
    run.daily("2026-11-24")
    assert (env / "picks.json").exists()
    assert status.data()["sources"]["sheet_links"]["consecutive_failures"] == 1


def test_empty_youtube_feed_is_a_failure():
    with pytest.raises(SourceError):
        youtube.parse_feed('<feed xmlns="http://www.w3.org/2005/Atom"></feed>')


def test_schedule_page_without_entries_markup_is_a_failure():
    with pytest.raises(SourceError):
        fc.parse_schedule("<html><body>メンテナンス中</body></html>")


def test_x_rate_limit_is_unknown_not_dead(monkeypatch):
    class R:
        status_code = 429
    monkeypatch.setattr(xembed.http, "get", lambda *a, **k: R())
    assert liveness.x_alive(mk("2020-01-01", yt=False).sources[0]) is None


def test_x_404_is_dead(monkeypatch):
    class R:
        status_code = 404
    monkeypatch.setattr(xembed.http, "get", lambda *a, **k: R())
    assert liveness.x_alive(mk("2020-01-01", yt=False).sources[0]) is False


def test_x_tombstone_is_dead(monkeypatch):
    class R:
        status_code = 200
        def json(self):
            return {"__typename": "TweetTombstone"}
    monkeypatch.setattr(xembed.http, "get", lambda *a, **k: R())
    assert liveness.x_alive(mk("2020-01-01", yt=False).sources[0]) is False


def test_liveness_unhides_when_source_returns():
    c = mk("2020-01-01", ["hirari"])
    liveness.check([c], {"youtube": lambda s: False}, sleep=0)
    assert c.hidden
    liveness.check([c], {"youtube": lambda s: True}, sleep=0)
    assert not c.hidden


def test_liveness_never_unhides_owner_hidden():
    c = mk("2020-01-01", ["hirari"], hidden=True)
    c.tags.append("owner_hidden")
    liveness.check([c], {"youtube": lambda s: True}, sleep=0)
    assert c.hidden


def test_owner_show_answer_survives_weekly_check(d):
    c = mk("2020-01-01", ["hirari"], yt=False, hidden=True)
    c.sources[0].has_video = False
    sheet.apply_answers([{"種類": "no_video", "対象": c.id, "内容": "", "答え": "表示"}], [c], d)
    liveness.check([c], {"x": lambda s: True}, sleep=0)
    assert not c.hidden


def test_xembed_keeps_existing_program_bracket():
    assert xembed._clean("[人生歌] 夜桜お七 坂本冬美 20250101 BS朝日").startswith("[人生歌] 夜桜お七")
