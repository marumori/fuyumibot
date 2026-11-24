import pytest

from pipeline import liveness, status
from pipeline.model import Source
from tests.helpers import mk


@pytest.fixture(autouse=True)
def fresh_status(tmp_path, monkeypatch):
    monkeypatch.setattr(status, "PATH", tmp_path / "status.json")
    status.reset()


def test_guard_exception_keeps_last_good():
    def boom():
        raise RuntimeError("412")
    assert status.guard("bilibili", boom, 50) is None
    assert status.data()["sources"]["bilibili"]["consecutive_failures"] == 1


def test_guard_rejects_big_drop():
    assert status.guard("bk_tv", lambda: [1, 2, 3], 120) is None
    assert "減少" in status.data()["sources"]["bk_tv"]["last_error"]


def test_guard_accepts_small_previous():
    assert status.guard("letters", lambda: [1], 3) == [1]


def test_guard_success_resets_failures():
    status.guard("yt", lambda: (_ for _ in ()).throw(OSError()), 0)
    assert status.guard("yt", lambda: [1, 2], 0) == [1, 2]
    assert status.data()["sources"]["yt"]["consecutive_failures"] == 0


def test_needs_alert_after_three():
    for _ in range(3):
        status.guard("bilibili", lambda: (_ for _ in ()).throw(OSError()), 0)
    assert status.needs_alert() == ["bilibili"]


def test_persisted(tmp_path):
    status.guard("yt", lambda: [1], 0)
    status.save()
    status.reset()
    status.load()
    assert status.data()["sources"]["yt"]["consecutive_failures"] == 0


def test_liveness_hides_clip_with_only_dead_source():
    c = mk("2020-01-01", ["hirari"])
    liveness.check([c], {"youtube": lambda s: False}, sleep=0)
    assert c.sources[0].alive is False and c.hidden


def test_liveness_falls_back_to_bilibili():
    c = mk("2020-01-01", ["hirari"])
    c.sources.append(Source("bilibili", "BV1", "u"))
    liveness.check([c], {"youtube": lambda s: False, "bilibili": lambda s: True}, sleep=0)
    assert not c.hidden and c.best_source().platform == "bilibili"


def test_liveness_unknown_result_keeps_state():
    c = mk("2020-01-01", ["hirari"])
    liveness.check([c], {"youtube": lambda s: None}, sleep=0)
    assert c.sources[0].alive and not c.hidden


def test_liveness_limit_and_offset():
    clips = [mk("2020-01-01", ["hirari"], n=str(i)) for i in range(5)]
    seen = []
    nxt = liveness.check(clips, {"youtube": lambda s: seen.append(s.id) or True}, limit=2, offset=4, sleep=0)
    assert len(seen) == 2 and nxt == 1
