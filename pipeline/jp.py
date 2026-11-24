"""Japanese text utilities: normalisation, 五十音 sort keys, 和暦, date labels."""
from __future__ import annotations

import re
import unicodedata
from datetime import date

_SMALL = str.maketrans("ぁぃぅぇぉっゃゅょゎゕゖ", "あいうえおつやゆよわかけ")
_VOWEL_ROWS = {
    "あ": "あかさたなはまやらわがざだばぱ",
    "い": "いきしちにひみりぎじぢびぴゐ",
    "う": "うくすつぬふむゆるぐずづぶぷゔ",
    "え": "えけせてねへめれげぜでべぺゑ",
    "お": "おこそとのほもよろをごぞどぼぽ",
}
_VOWEL_OF = {ch: v for v, chars in _VOWEL_ROWS.items() for ch in chars}
_PUNCT = re.compile(r"[「」『』・！!？?、。,.\s'\"()（）\[\]【】〜~♪☆★]")
_WEEKDAYS = "月火水木金土日"
_GYO = [("あ", "あいうえお"), ("か", "かきくけこ"), ("さ", "さしすせそ"), ("た", "たちつてと"),
        ("な", "なにぬねの"), ("は", "はひふへほ"), ("ま", "まみむめも"), ("や", "やゆよ"),
        ("ら", "らりるれろ"), ("わ", "わゐゑをん")]
_ERAS = [(date(2019, 5, 1), "令和"), (date(1989, 1, 8), "平成"), (date(1926, 12, 25), "昭和")]


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("~", "〜").replace("!", "！").replace("&", "＆")
    return re.sub(r"\s+", " ", s).strip()


def to_hiragana(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def _strip_dakuten(s: str) -> str:
    return unicodedata.normalize("NFC", "".join(
        c for c in unicodedata.normalize("NFD", s) if c not in "゙゚"))


def _kana_form(yomi: str) -> str:
    s = to_hiragana(normalize(yomi)).lower()
    s = s.split("〜")[0]
    s = s.translate(_SMALL).replace("ゔ", "ぶ").replace("を", "お")
    out = []
    for ch in s:
        if ch == "ー":
            prev = out[-1] if out else ""
            out.append(_VOWEL_OF.get(prev, ""))
        else:
            out.append(ch)
    return _PUNCT.sub("", "".join(out))


def sort_key(yomi: str) -> tuple:
    kana = _kana_form(yomi)
    group = 0 if kana and "ぁ" <= kana[0] <= "ゖ" else 1
    return (_strip_dakuten(kana), group, kana)


def gyo(yomi: str) -> str:
    kana = _kana_form(yomi)
    first = _strip_dakuten(kana[:1]) if kana else ""
    for name, chars in _GYO:
        if first and first in chars:
            return name
    return "英数字"


def wareki(year: int, month: int = 12, day: int = 31) -> str:
    d = date(year, month, day)
    for start, name in _ERAS:
        if d >= start:
            n = year - start.year + 1
            return f"{name}{'元' if n == 1 else n}年"
    return ""


def format_date(iso: str, with_wareki: bool = False) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    s = f"{y}年{m}月{d}日（{_WEEKDAYS[date(y, m, d).weekday()]}）"
    if with_wareki:
        s += f"（{wareki(y, m, d)}）"
    return s


def year_label(year: int) -> str:
    return f"{year}年（{wareki(year)}）"
