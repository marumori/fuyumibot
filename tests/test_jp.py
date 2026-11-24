from pipeline import jp


def test_sort_key_orders_gojuon():
    words = ["れーざーびーむ", "あばれだいこ", "がんばれ", "かもめ", "ぱぴぷ", "はな"]
    assert sorted(words, key=jp.sort_key) == ["あばれだいこ", "かもめ", "がんばれ", "はな", "ぱぴぷ", "れーざーびーむ"]


def test_long_vowel_takes_previous_vowel():
    assert jp.sort_key("れーざー")[0] == jp.sort_key("れえざあ")[0]


def test_katakana_and_small_kana():
    assert jp.sort_key("チャップリン")[0] == jp.sort_key("ちやつぷりん")[0]


def test_subtitle_after_wave_ignored():
    assert jp.sort_key("はな〜さくら")[0] == jp.sort_key("はな")[0]


def test_gyo():
    assert jp.gyo("よざくらおしち") == "や"
    assert jp.gyo("TATTOO") == "英数字"
    assert jp.gyo("がんばれ") == "か"
    assert jp.gyo("ぱぴぷ") == "は"
    assert jp.gyo("をとめ") == "あ"


def test_wareki_boundaries():
    assert jp.wareki(1989, 1, 7) == "昭和64年"
    assert jp.wareki(1989, 1, 8) == "平成元年"
    assert jp.wareki(2019, 4, 30) == "平成31年"
    assert jp.wareki(2019, 5, 1) == "令和元年"
    assert jp.wareki(1994) == "平成6年"


def test_format_date():
    assert jp.format_date("2025-12-31") == "2025年12月31日（水）"
    assert jp.format_date("1994-12-31", with_wareki=True) == "1994年12月31日（土）（平成6年）"


def test_normalize_wave_dash_and_spaces():
    assert jp.normalize("森口博子でしょう～　花のワルツ") == "森口博子でしょう〜 花のワルツ"


def test_normalize_bang_and_amp():
    assert jp.normalize("風に立つ!") == "風に立つ！"
    assert jp.normalize("吉幾三&藤あや子") == "吉幾三＆藤あや子"
    assert jp.normalize("ＡＢＣ　１２") == "ABC 12"
