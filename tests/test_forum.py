from pathlib import Path

from pipeline.factcheck import verify
from pipeline.model import ForumTopic
from pipeline.sources import forum
from tests.helpers import app, mk

F = Path("tests/fixtures")


def test_parse_listing_titles_and_links_only():
    topics = forum.parse_listing((F / "forum_list.html").read_text("utf-8"))
    assert [t.title for t in topics] == ["BS日本のうた福岡・飯塚", "歌謡プレミアム特別版"]
    assert topics[0].url.startswith("https://u-fuyumi.net/forums/topic/")
    assert topics[0].date is None
    assert set(vars(topics[0])) == {"title", "url", "date"}


def test_last_page():
    assert forum.last_page((F / "forum_list.html").read_text("utf-8")) == 61


def test_topic_date_is_first_post():
    assert forum.parse_topic_date((F / "forum_topic.html").read_text("utf-8")) == "2023-12-11"


def test_forum_confirms_when_fanclub_has_no_record(d):
    c = mk("2023-12-16", ["saikai-sakaba"], program="人生歌")
    verify([c], [], d, forum=[ForumTopic("人生、歌がある", "https://u-fuyumi.net/forums/topic/x", "2023-12-14")])
    assert c.verified == {"broadcaster": "", "program": "人生、歌がある", "note": "", "source": "fan_forum"}


def test_forum_window_is_3_days_before_to_1_after(d):
    t = lambda day: [ForumTopic("人生、歌がある", "u", day)]
    for day, ok in [("2023-12-12", False), ("2023-12-13", True), ("2023-12-17", True), ("2023-12-18", False)]:
        c = mk("2023-12-16", ["saikai-sakaba"], program="人生歌")
        verify([c], [], d, forum=t(day))
        assert bool(c.verified) is ok, day


def test_fanclub_record_wins_over_forum(d):
    c = mk("2023-12-16", ["saikai-sakaba"], program="人生歌")
    verify([c], [app("2023-12-16", "人生、歌がある")], d, forum=[ForumTopic("人生、歌がある", "u", "2023-12-15")])
    assert c.verified["source"] == "fanclub" and c.verified["broadcaster"] == "BS朝日"


def test_forum_never_confirms_post_time_dates(d):
    c = mk("2023-12-16", ["saikai-sakaba"], program="人生歌", date_source="post_time")
    verify([c], [], d, forum=[ForumTopic("人生、歌がある", "u", "2023-12-16")])
    assert c.verified is None
