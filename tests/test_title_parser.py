import pytest

from pipeline.title_parser import parse_title

CASES = [
    ("[徹子の部屋] 再会酒場(セリフ入り)、また君に恋してる、夜桜お七 坂本冬美 20240116",
     ("徹子の部屋", ["saikai-sakaba", "mata-kimi-ni-koishiteru", "yozakura-oshichi"], ["坂本冬美"], "2024-01-16", True)),
    ("あばれ太鼓　坂本冬美 w/大塚宝　20230101", (None, ["abare-daiko"], ["坂本冬美", "大塚宝"], "2023-01-01", True)),
    ("[紅白歌合戦お正月SP] （無曲名） 坂本冬美＆M!LK 20260103", ("紅白歌合戦お正月SP", [], ["坂本冬美", "M!LK"], "2026-01-03", True)),
    ("心の糸 演歌5人娘 20240104", (None, ["kokoro-no-ito"], ["演歌5人娘"], "2024-01-04", True)),
    ("（無曲名） 20250104", (None, [], [], "2025-01-04", True)),
    ("謎の新曲 坂本冬美 20260101", (None, [], ["坂本冬美"], "2026-01-01", False)),
    ("夜桜お七 千本桜 坂本冬美＆小林幸子 20230101", (None, ["yozakura-oshichi", "senbonzakura"], ["坂本冬美", "小林幸子"], "2023-01-01", True)),
    ("TATTOO藤あや子 20230101", (None, ["tattoo"], ["藤あや子"], "2023-01-01", True)),
    ("新曲紹介 遠い昔の恋の歌 坂本冬美 20260101", (None, ["tooi-mukashi-no-koi-no-uta"], ["坂本冬美"], "2026-01-01", True)),
    ("[BCコンサート] [ノンストップ] ほろ酔い満月 坂本冬美 20220101", ("BCコンサート", ["horoyoi-mangetsu"], ["坂本冬美"], "2022-01-01", True)),
]


@pytest.mark.parametrize("title,exp", CASES)
def test_parse(title, exp, d):
    r = parse_title(title, d)
    assert (r.program, r.songs, r.performers, r.date, r.ok) == exp


def test_bilibili_style(d):
    r = parse_title("【cut】あばれ太鼓　坂本冬美 w/大塚宝　20230101 (含talking)", d, platform="bilibili")
    assert r.songs == ["abare-daiko"] and r.date == "2023-01-01" and r.ok


def test_missing_date_not_ok(d):
    r = parse_title("冬美、歌がある", d)
    assert r.date is None and not r.ok


def test_program_display_name_is_raw_bracket(d):
    assert parse_title("[人生歌] 再会酒場 坂本冬美 20240101", d).program == "人生歌"
