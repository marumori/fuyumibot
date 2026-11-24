from pipeline.model import Clip, Source, save, load


def _clip(sources):
    return Clip(id="c1", broadcast_date="2025-12-31", date_source="title", program=None,
                songs=[], performers=[], title_raw="t", sources=sources)


def test_best_source_prefers_alive_youtube():
    c = _clip([Source("x", "1", "u1"), Source("bilibili", "BV1", "u2"),
               Source("youtube", "y1", "u3", alive=False)])
    assert c.best_source().platform == "bilibili"
    assert c.youtube() is None


def test_best_source_youtube_first():
    c = _clip([Source("x", "1", "u1"), Source("youtube", "y1", "u3")])
    assert c.best_source().platform == "youtube"
    assert c.youtube().id == "y1"


def test_best_source_none_when_all_dead():
    assert _clip([Source("x", "1", "u", alive=False)]).best_source() is None


def test_save_is_stable_and_roundtrips(tmp_path):
    p = tmp_path / "c.json"
    c = _clip([Source("x", "1", "u1")])
    save(p, [c]); a = p.read_bytes()
    save(p, load(p, Clip)); b = p.read_bytes()
    assert a == b
    assert load(p, Clip)[0] == c
