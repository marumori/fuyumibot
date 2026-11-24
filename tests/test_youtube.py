from pathlib import Path

from pipeline.sources import to_clip
from pipeline.sources.youtube import parse_feed, parse_playlist_items


def test_parse_feed():
    ups = parse_feed(Path("tests/fixtures/yt_feed.xml").read_text("utf-8"))
    assert len(ups) == 15
    assert ups[0].title == "あばれ太鼓　坂本冬美 w/大塚宝　20230101"
    assert ups[0].platform == "youtube"
    assert ups[0].url == f"https://www.youtube.com/watch?v={ups[0].id}"
    assert ups[0].uploaded_at.startswith("2026-11-09")


def test_parse_playlist_items():
    js = {"items": [{"snippet": {"title": "祝い酒　坂本冬美 20240101", "publishedAt": "2026-11-09T17:45:48Z",
                                 "resourceId": {"videoId": "abc123"}}}]}
    [u] = parse_playlist_items(js)
    assert (u.id, u.title, u.uploaded_at) == ("abc123", "祝い酒　坂本冬美 20240101", "2026-11-09T17:45:48Z")


def test_to_clip(d):
    ups = parse_feed(Path("tests/fixtures/yt_feed.xml").read_text("utf-8"))
    c = to_clip(ups[0], d)
    assert c.broadcast_date == "2023-01-01" and c.songs == ["abare-daiko"]
    assert c.sources[0].platform == "youtube" and c.date_source == "title"


def test_to_clip_without_date_uses_upload_date_as_post_time(d):
    from pipeline.sources import RawUpload
    c = to_clip(RawUpload("youtube", "z", "u", "冬美、歌がある", "2024-01-15T15:52:30Z"), d)
    assert c.date_source == "post_time" and c.broadcast_date == "2024-01-16"
