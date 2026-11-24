import json

import pytest

from pipeline import build
from pipeline.model import Appearance, FlashIssue, Letter, Pick, Source, save
from tests.helpers import mk


@pytest.fixture
def site(tmp_path, d):
    data, out = tmp_path / "data", tmp_path / "site"
    data.mkdir()
    for f in ["songs.yaml", "performers.yaml", "programs.yaml", "captions.yaml"]:
        (data / f).write_text(open(f"data/{f}", encoding="utf-8").read(), "utf-8")
    a = mk("2025-12-31", ["yozakura-oshichi"], program="紅白", performers=["坂本冬美", "M!LK"], n="a")
    a.verified = {"broadcaster": "NHK総合", "program": "第76回NHK紅白歌合戦", "note": ""}
    b = mk("2024-12-31", ["iwaizake"], n="b")
    c = mk("2024-12-31", [], program="人生歌", n="c", yt=False, date_source="post_time")
    h = mk("2023-12-31", ["hirari"], n="h", hidden=True)
    tv = mk("2026-11-16", ["hirari"], program="はやウタ", n="tv")
    tv.sources[0].uploaded_at = "2026-11-17T00:00:00Z"
    save(data / "clips.json", [a, b, c, h, tv])
    save(data / "appearances.json", [Appearance("2026-12-31", "19:20〜23:45", "NHK総合", "第77回NHK紅白歌合戦", "TV", ""),
                                     Appearance("2026-11-16", "", "NHK総合", "はやウタ", "TV", "")])
    save(data / "letters.json", [Letter("2026-12-29", "紅白リハーサル", "https://fuyumi-fc.com/letter/index.php?y=2026&m=12#post1",
                                        {"songs": ["yozakura-oshichi"], "programs": [], "people": []})])
    save(data / "flash.json", [FlashIssue("2026-12-22", "M!LK", "https://fuyumi-fc.com/letter/x")])
    save(data / "picks.json", [Pick("2026-12-31", "大みそかのうた", "紅白・年忘れの季節", [a.id, b.id])])
    (data / "review.json").write_text(json.dumps([{"kind": "no_video", "ref": h.id, "detail": "動画なし", "created": "x"}]), "utf-8")
    build.build_all(data, out, "2026-12-31", now="2026-12-31T08:00")
    return out, {"a": a, "b": b, "c": c, "h": h, "tv": tv}


def J(p):
    return json.loads(p.read_text("utf-8"))


def test_today_sections(site):
    out, cl = site
    t = J(out / "data/today.json")
    assert t["date_label"] == "12月31日（木）"
    assert t["pick"]["theme_title"] == "大みそかのうた" and [c["id"] for c in t["pick"]["clips"]] == [cl["a"].id, cl["b"].id]
    assert [y["year"] for y in t["on_this_day"]["years"]] == [2025, 2024]
    assert t["on_this_day"]["exact"] is True
    assert t["appearances"][0]["state"] == "before" and t["appearances"][0]["start"] == "19:20"
    assert t["letters"][0]["clips"][0]["id"] == cl["a"].id
    assert t["flash"]["guest"] == "M!LK" and t["flash"]["clips"][0]["id"] == cl["a"].id
    assert t["new"][0]["id"] == cl["tv"].id


def test_hidden_excluded_everywhere(site):
    out, cl = site
    assert cl["h"].id not in (out / "data/today.json").read_text("utf-8")
    assert cl["h"].id not in (out / "data/days/12-31.json").read_text("utf-8")
    assert not (out / f"v/{cl['h'].id}").exists()


def test_card_labels(site):
    out, cl = site
    t = J(out / "data/today.json")
    card = t["on_this_day"]["years"][0]["clips"][0]
    assert card["title_label"] == "「夜桜お七」"
    assert card["date_label"] == "2025年12月31日（水）（令和7年）"
    assert card["performers_label"] == "坂本冬美、M!LK"
    assert card["verified"] is True and card["program"] == "NHK紅白歌合戦"
    assert card["thumb"].startswith("https://i.ytimg.com/vi/")
    talk = next(c for y in t["on_this_day"]["years"] for c in y["clips"] if c["id"] == cl["c"].id)
    assert talk["title_label"] == "トーク・その他" and talk["verified"] is False and talk["platform"] == "x"


def test_today_size_small(site):
    out, _ = site
    assert (out / "data/today.json").stat().st_size < 20000


def test_empty_day_uses_nearby(site, tmp_path):
    out, _ = site
    build.build_all(out.parent / "data", out, "2026-01-02", now="2026-01-02T08:00")
    t = J(out / "data/today.json")
    assert t["on_this_day"]["exact"] is False and t["on_this_day"]["years"]


def test_appearance_states(site):
    out, cl = site
    build.build_all(out.parent / "data", out, "2026-11-16", now="2026-11-16T23:00")
    t = J(out / "data/today.json")
    assert t["appearances"][0]["state"] == "clip" and t["appearances"][0]["clip"]["id"] == cl["tv"].id


def test_calendar_and_days(site):
    out, cl = site
    cal = J(out / "data/calendar.json")
    assert cal["12-31"]["videos"] == 3 and cal["12-29"]["letters"] == 1 and cal["12-22"]["flash"] == 1
    day = J(out / "data/days/12-31.json")
    assert day["label"] == "12月31日" and [y["year_label"] for y in day["years"]][:2] == ["2025年（令和7年）", "2024年（令和6年）"]


def test_songs_sorted_gojuon(site):
    out, _ = site
    songs = J(out / "data/songs.json")
    titles = [s["title"] for s in songs]
    assert titles == sorted(titles, key=lambda t: [s["yomi"] for s in songs if s["title"] == t][0])
    assert {s["title"] for s in songs} == {"夜桜お七", "祝い酒", "ひらり"}
    assert next(s for s in songs if s["title"] == "夜桜お七")["gyo"] == "や"
    assert J(out / "data/songs/yozakura-oshichi.json")["clips"][0]["id"]


def test_clip_page_ogp(site):
    out, cl = site
    html = (out / f"v/{cl['a'].id}/index.html").read_text("utf-8")
    assert 'name="robots" content="noindex,nofollow"' in html
    assert 'property="og:title" content="「夜桜お七」坂本冬美 2025年12月31日"' in html
    assert f'/v/{cl["a"].id}/' in html and "twitter:card" in html
    assert "<script" in html and "/assets/player.js" in html


def test_review_json_limited(site):
    out, _ = site
    r = J(out / "data/review.json")
    assert set(r[0]) == {"種類", "対象", "内容"}
