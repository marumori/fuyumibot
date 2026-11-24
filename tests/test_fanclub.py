from pathlib import Path

from pipeline.sources import fanclub as fc

F = Path("tests/fixtures")


def html(name):
    return (F / name).read_text("utf-8")


def test_schedule_tv_only_and_kouhaku():
    apps = fc.parse_schedule(html("fc_schedule.html"))
    assert apps and all(a.kind in ("TV", "ラジオ") for a in apps)
    k = [a for a in apps if a.date == "2026-12-31" and "紅白" in a.program]
    assert k and k[0].broadcaster == "NHK総合" and k[0].program == "第77回NHK紅白歌合戦"
    assert k[0].time == "19:20〜23:45"


def test_schedule_vtr_note():
    a = next(a for a in fc.parse_schedule(html("fc_schedule.html")) if a.date == "2026-11-24")
    assert a.note == "VTR" and a.time == "7:00〜7:54"


def test_bk_tv_range_expands_and_notes():
    apps = fc.parse_bk_tv(html("fc_bk_tv_2026.html"))
    yocchan = [a for a in apps if "よっちゃん" in a.program]
    assert [a.date for a in yocchan] == ["2026-04-07", "2026-04-08", "2026-04-09", "2026-04-10"]
    jinsei = next(a for a in apps if a.date == "2026-01-24")
    assert (jinsei.broadcaster, jinsei.program, jinsei.note) == ("BS朝日", "人生、歌がある", "VTR")
    assert any(a.note == "再放送" for a in apps)
    assert len(apps) >= 120


def test_letters_have_no_body_and_anchor_urls():
    rows = fc.parse_letters(html("fc_letter_sample.html"), 2026, 11)
    letter, body = rows[0]
    assert letter.date == "2026-11-19" and letter.title == "モゴモゴ対談(^^)"
    assert letter.url == "https://fuyumi-fc.com/letter/index.php?y=2026&m=11#post40858"
    assert "ひらり" in body
    assert not hasattr(letter, "body")


def test_archive_months():
    assert (2004, 6) in fc.parse_letter_months(html("fc_letter_sample.html"))


def test_parse_date_variants():
    assert fc.parse_dates("2027/1/15（金）") == ["2027-01-15"]
    assert fc.parse_dates("2026/04/07（火）～04/10（金）") == ["2026-04-07", "2026-04-08", "2026-04-09", "2026-04-10"]
    assert fc.parse_dates("2027/2/12(金)～2/28(日)")[-1] == "2027-02-28"
    assert fc.parse_dates("未定") == []
