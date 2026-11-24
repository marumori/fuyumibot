from pipeline import review
from pipeline.seed_import import import_seed, read_rows, row_to_clip


def row(**kw):
    base = {"mmdd": "01-01", "yyyy": "2023", "title": "あばれ太鼓 坂本冬美 20230101",
            "x_url": "https://x.com/jounotakeuchi/status/111", "posted_utc": "2023-01-01 03:54 UTC",
            "relation": "X獨有", "bili_url": "", "note": ""}
    base.update(kw)
    return base


def test_read_rows_columns():
    rows = read_rows("data/seed/x_table.md")
    assert len(rows) == 669
    assert rows[0]["x_url"].startswith("https://x.com/jounotakeuchi/status/")
    assert rows[0]["posted_utc"] == "2023-01-01 03:54 UTC"


def test_post_time_late_utc_shifts_to_next_jst_day(d):
    c = row_to_clip(row(title="（無曲名） 20230107", posted_utc="2023-01-07 22:32 UTC", note="日期取自發文時間"), d)
    assert c.broadcast_date == "2023-01-08" and c.date_source == "post_time"


def test_title_date_kept_when_not_post_time(d):
    c = row_to_clip(row(), d)
    assert c.broadcast_date == "2023-01-01" and c.date_source == "title"
    assert c.songs == ["abare-daiko"] and c.performers == ["坂本冬美"]
    assert c.sources[0].platform == "x" and c.sources[0].id == "111"


def test_bilibili_same_post_becomes_second_source(d):
    c = row_to_clip(row(relation="同一條", bili_url="https://www.bilibili.com/video/BV1nFWg64Ei8"), d)
    assert [s.platform for s in c.sources] == ["x", "bilibili"]
    assert c.sources[1].id == "BV1nFWg64Ei8"


def test_probable_same_post_queues_review(d):
    review.reset()
    row_to_clip(row(relation="疑似同一條", bili_url="https://www.bilibili.com/video/BV1x"), d)
    assert any(i["kind"] == "merge_uncertain" for i in review.items())


def test_no_video_rows_hidden(d):
    c = row_to_clip(row(note="未偵測到原生影片(可能為連結/圖文)"), d)
    assert c.hidden and not c.sources[0].has_video


def test_no_video_with_bilibili_not_hidden(d):
    c = row_to_clip(row(note="未偵測到原生影片", relation="同一條", bili_url="https://www.bilibili.com/video/BV9"), d)
    assert not c.hidden


def test_import_seed_counts(d):
    review.reset()
    rows = read_rows("data/seed/x_table.md")
    assert sum(row_to_clip(r, d).date_source == "post_time" for r in rows) == 164
    clips = import_seed("data/seed/x_table.md", d)
    assert 560 <= len(clips) <= 669
    assert len({c.id for c in clips}) == len(clips)
    assert any(i["kind"] == "date_post_time" for i in review.items())
