from pipeline.title_parser import parse_title
from tests.conftest import read_seed_titles

BANNED = {"My", "SWEET", "LIVE", "Dancing", "Electro", "乙女座"}


def test_all_seed_titles_parse_or_flag(d):
    rows = read_seed_titles()
    results = [parse_title(t, d) for t in rows]
    assert len(rows) == 669
    assert all(r.date for r in results)
    ok = sum(r.ok for r in results) / len(results)
    bad = [t for t, r in zip(rows, results) if not r.ok]
    assert ok >= 0.95, bad
    assert not any(s in BANNED for r in results for s in r.songs)
