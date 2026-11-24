from pipeline.model import Letter, Pick
from pipeline.picker import movable, pick
from tests.helpers import app, mk


def lib():
    clips = []
    for i, y in enumerate(range(1995, 2026)):
        for s in ["abare-daiko", "yozakura-oshichi", "iwaizake", "jinsei-iroiro", "yuki-shinshin",
                  "horoyoi-mangetsu", "hirari", "ganpeki-no-haha", "senbonzakura", "omatsuri-mambo"]:
            clips.append(mk(f"{y}-0{1 + i % 9}-1{i % 9}", [s], program="人生歌" if y % 2 else "うたコン", n=str(y)))
    return clips


def P(date, clips=None, apps=(), letters=(), overrides=None, history=(), d=None):
    return pick(date, clips or lib(), list(apps), list(letters), overrides or {}, list(history), d)


def test_pick_override_wins(d):
    clips = lib()
    ids = [c.id for c in clips[:3]]
    p = P("2027-05-01", clips, overrides={"2027-05-01": {"theme": "わたしの選曲", "clip_ids": ids}}, d=d)
    assert p.theme_title == "わたしの選曲" and p.clip_ids == ids


def test_pick_birthday(d):
    assert P("2027-03-30", d=d).theme_title.startswith("お誕生日")


def test_pick_debut_uses_abare_daiko(d):
    clips = lib()
    p = P("2027-03-04", clips, d=d)
    by_id = {c.id: c for c in clips}
    assert all(by_id[i].songs == ["abare-daiko"] for i in p.clip_ids)


def test_pick_memorial_wording(d):
    assert "偲んで" in P("2027-11-08", d=d).theme_title


def test_pick_tv_today_uses_same_program(d):
    clips = lib()
    p = P("2027-06-05", clips, apps=[app("2027-06-05", "人生、歌がある")], d=d)
    by_id = {c.id: c for c in clips}
    assert p.theme_title == "今夜の放送の前に"
    assert all(by_id[i].program == "人生歌" for i in p.clip_ids)


def test_pick_skips_vtr_appearance(d):
    p = P("2027-06-05", apps=[app("2027-06-05", "人生、歌がある", note="VTR")], d=d)
    assert p.theme_title != "今夜の放送の前に"


def test_pick_letter_mention(d):
    lt = Letter("2027-06-04", "t", "u", {"songs": ["hirari"]})
    p = P("2027-06-05", letters=[lt], d=d)
    assert p.reason == "冬美さんが便りで触れた曲"


def test_pick_season_winter(d):
    clips = lib()
    p = P("2027-01-20", clips, d=d)
    by_id = {c.id: c for c in clips}
    assert all("冬" in d.song(by_id[i].songs[0]).get("season", []) for i in p.clip_ids)


def test_pick_only_youtube_and_no_repeat_30_days(d):
    clips = lib() + [mk("2001-01-01", ["yuki-shinshin"], yt=False, n="x")]
    first = P("2027-01-20", clips, d=d)
    hist = [Pick("2027-01-20", first.theme_title, first.reason, first.clip_ids)]
    second = P("2027-01-21", clips, history=hist, d=d)
    assert not set(first.clip_ids) & set(second.clip_ids)
    by_id = {c.id: c for c in clips}
    assert all(by_id[i].youtube() for i in first.clip_ids + second.clip_ids)


def test_pick_size_between_3_and_5(d):
    assert 3 <= len(P("2027-07-07", d=d).clip_ids) <= 5


def test_pick_deterministic(d):
    clips = lib()
    assert P("2027-07-07", clips, d=d) == P("2027-07-07", clips, d=d)


def test_pick_falls_back_when_theme_has_too_few(d):
    clips = [mk("2020-01-01", ["hirari"], n=str(i)) for i in range(4)]
    p = P("2027-03-04", clips, d=d)
    assert len(p.clip_ids) == 3 or len(p.clip_ids) == 4


def test_pick_empty_library_returns_empty():
    p = pick("2027-07-07", [], [], [], {}, [], None)
    assert p.clip_ids == []


def test_movable_dates():
    assert movable("mothers_day", 2027) == "2027-05-09"
    assert movable("respect_aged_day", 2027) == "2027-09-20"
    assert movable("chushu", 2026) == "2026-09-25"


def test_default_theme_name(d):
    clips = [mk("2020-01-01", ["hirari"], n=str(i)) for i in range(4)]
    assert P("2027-07-07", clips, d=d).theme_title == "冬美、歌がある"
