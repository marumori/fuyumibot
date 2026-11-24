import pytest

from pipeline.sources import sheet
from tests.helpers import mk


def test_wrong_headers_raise():
    with pytest.raises(sheet.SheetError):
        sheet.parse_csv("URL,memo\nx,y\n", sheet.ADD_HEADERS)


def test_parse_csv_ok():
    rows = sheet.parse_csv("リンク,メモ\nhttps://x.com/a/status/1,\n", sheet.ADD_HEADERS)
    assert rows == [{"リンク": "https://x.com/a/status/1", "メモ": ""}]


def test_links_to_sources():
    rows = [{"リンク": "https://x.com/jounotakeuchi/status/2006396667155919096?s=20"},
            {"リンク": "https://twitter.com/jounotakeuchi/status/123"},
            {"リンク": "https://youtu.be/abcDEF123?si=x"},
            {"リンク": "https://www.youtube.com/watch?v=zzz111&t=3"},
            {"リンク": "https://www.bilibili.com/video/BV1szWZ6NEDE/?spm=1"},
            {"リンク": "メモだけ"}]
    assert sheet.links_to_sources(rows) == [
        ("x", "2006396667155919096", "https://x.com/jounotakeuchi/status/2006396667155919096"),
        ("x", "123", "https://x.com/jounotakeuchi/status/123"),
        ("youtube", "abcDEF123", "https://www.youtube.com/watch?v=abcDEF123"),
        ("youtube", "zzz111", "https://www.youtube.com/watch?v=zzz111"),
        ("bilibili", "BV1szWZ6NEDE", "https://www.bilibili.com/video/BV1szWZ6NEDE")]


def test_overrides_map_links_to_clip_ids():
    c = mk("2020-01-01", ["hirari"])
    c.sources[0].url = "https://www.youtube.com/watch?v=Q1"
    c.sources[0].id = "Q1"
    rows = [{"日付": "2027/3/30", "テーマ": "わたしの選曲", "リンク1": "https://youtu.be/Q1",
             "リンク2": "", "リンク3": "", "リンク4": "", "リンク5": ""}]
    assert sheet.overrides(rows, [c]) == {"2027-03-30": {"theme": "わたしの選曲", "clip_ids": [c.id]}}


def test_apply_answers_title_and_unhide(d):
    a = mk("2020-01-01", [], n="a", hidden=True)
    b = mk("2020-01-02", [], n="b")
    rows = [{"種類": "no_video", "対象": a.id, "内容": "", "答え": "表示"},
            {"種類": "title_unparsed", "対象": b.id, "内容": "", "答え": "夜桜お七; 坂本冬美、藤あや子; 20200103"}]
    sheet.apply_answers(rows, [a, b], d)
    assert not a.hidden
    assert b.songs == ["yozakura-oshichi"] and b.performers == ["坂本冬美", "藤あや子"]
    assert b.broadcast_date == "2020-01-03" and b.date_source == "title"


def test_apply_answers_date_confirm(d):
    a = mk("2020-01-01", [], date_source="post_time")
    sheet.apply_answers([{"種類": "date_post_time", "対象": a.id, "内容": "", "答え": "20191231"}], [a], d)
    assert a.broadcast_date == "2019-12-31" and a.date_source == "title"
