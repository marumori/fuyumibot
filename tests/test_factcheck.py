from pipeline.factcheck import verify
from tests.helpers import app, mk


def test_alias_program_matches(d):
    c = mk("2026-01-24", ["saikai-sakaba"], program="人生歌")
    verify([c], [app("2026-01-24", "人生、歌がある", note="VTR")], d)
    assert c.verified == {"broadcaster": "BS朝日", "program": "人生、歌がある", "note": "VTR"}


def test_substring_program_matches(d):
    c = mk("2026-12-31", ["yozakura-oshichi"], program="紅白")
    verify([c], [app("2026-12-31", "第77回NHK紅白歌合戦", broadcaster="NHK総合")], d)
    assert c.verified and c.verified["broadcaster"] == "NHK総合"


def test_verify_requires_program_match(d):
    c = mk("2026-01-24", ["saikai-sakaba"], program="うたコン")
    verify([c], [app("2026-01-24", "人生、歌がある")], d)
    assert c.verified is None


def test_verify_needs_program_in_title(d):
    c = mk("2026-01-24", ["saikai-sakaba"], program=None)
    verify([c], [app("2026-01-24", "人生、歌がある")], d)
    assert c.verified is None


def test_verify_never_on_post_time_dates(d):
    c = mk("2026-01-24", ["saikai-sakaba"], program="人生歌", date_source="post_time")
    verify([c], [app("2026-01-24", "人生、歌がある")], d)
    assert c.verified is None
