import pytest
from pipeline.dictionary import Dictionaries


@pytest.fixture(scope="module")
def d():
    return Dictionaries.load("data")


def ids(d, text):
    return [m[2] for m in d.match_songs_longest(text)]


def test_longest_match_prefers_full_title(d):
    assert ids(d, "夜桜お七 千本桜") == ["yozakura-oshichi", "senbonzakura"]


def test_short_alias_maps_to_canonical(d):
    assert ids(d, "お七") == ["yozakura-oshichi"]
    assert d.song("yozakura-oshichi")["title"] == "夜桜お七"


def test_alias_variants(d):
    assert ids(d, "ほろよい満月") == ids(d, "ほろ酔い満月")
    assert d.song(ids(d, "ほろよい満月")[0])["title"] == "ほろ酔い満月"
    assert ids(d, "まだ君に恋してる") == ["mata-kimi-ni-koishiteru"]


def test_space_inside_song(d):
    assert ids(d, "SWEET MEMORIES") == ["sweet-memories"]


def test_performer_units_and_aliases(d):
    assert d.match_performers_from_right("心の糸 演歌5人娘") == (["演歌5人娘"], "心の糸")
    assert d.match_performers_from_right("あばれ太鼓 坂本冬美 w/大塚宝") == (["坂本冬美", "大塚宝"], "あばれ太鼓")
    assert d.match_performers_from_right("酒と泪と男と女 吉幾三＆藤あや子") == (["吉幾三", "藤あや子"], "酒と泪と男と女")


def test_glued_performer(d):
    assert d.match_performers_from_right("TATTOO藤あや子") == (["藤あや子"], "TATTOO")


def test_program_alias(d):
    assert d.program("人生歌") == "人生、歌がある"
    assert d.program("人生歌がある") == "人生、歌がある"
    assert d.program("紅白") == "NHK紅白歌合戦"
    assert d.program("存在しない番組") is None


def test_required_readings(d):
    expected = {"yozakura-oshichi": "よざくらおしち", "yuki-shinshin": "ゆきしんしん", "iwaizake": "いわいざけ",
                "amagigoe": "あまぎごえ", "meoto-zenzai": "めおとぜんざい", "hanagatami": "はながたみ",
                "saikai-sakaba": "さいかいさかば", "abare-daiko": "あばれだいこ"}
    for sid, y in expected.items():
        assert d.song(sid)["yomi"] == y, sid


def test_non_songs_absent(d):
    for bad in ["My", "SWEET", "LIVE", "Dancing", "Electro", "乙女座", "新曲紹介"]:
        assert not any(s["title"] == bad for s in d.songs), bad


def test_song_places(d):
    assert d.song("noto-wa-iirankaine")["places"] == ["石川"]
    assert d.song("amagigoe")["places"] == ["静岡"]
    assert all("places" in s for s in d.songs)


def test_fuyumi_clip_rule(d):
    assert d.is_fuyumi(["坂本冬美"])
    assert d.is_fuyumi(["五木ひろし", "坂本冬美"])
    assert d.is_fuyumi(["あやふゆ"])
    assert not d.is_fuyumi(["藤あや子"])
    assert not d.is_fuyumi([])
