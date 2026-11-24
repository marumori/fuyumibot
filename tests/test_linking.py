from pipeline.linking import flash_from_letters, mentions
from pipeline.model import Letter


def test_mentions_songs_programs_people(d):
    m = mentions("今日は「ひらり」と夜桜お七を歌いました。BS朝日「人生、歌がある」で藤あや子さんと。", d)
    assert m["songs"] == ["hirari", "yozakura-oshichi"]
    assert m["programs"] == ["人生、歌がある"]
    assert m["people"] == ["藤あや子"]


def test_mentions_ignore_short_common_words(d):
    assert mentions("ここから時代が変わる女の人", d)["songs"] == []


def test_flash_from_letters():
    ls = [(Letter("2026-11-10", "モゴモゴ対談o(^-^)o", "u1", {"people": ["大竹しのぶ"]}), "FLASHのモゴモゴ対談"),
          (Letter("2026-11-23", "クリスマスツリー", "u2", {}), "ツリー")]
    [f] = flash_from_letters(ls)
    assert (f.issue_date, f.guest, f.letter_url) == ("2026-11-10", "大竹しのぶ", "u1")
