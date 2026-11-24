from pathlib import Path

from pipeline.sources import flash

F = Path("tests/fixtures")


def test_parse_tag_page():
    arts = flash.parse_tag_page((F / "flash_tag.html").read_text("utf-8"))
    assert len(arts) == 2
    a = arts[0]
    assert a.date == "2026-11-21"
    assert a.url == "https://smart-flash.jp/entertainment/entertainment-news/439644/"
    assert a.title.startswith("大竹しのぶが吐露")
    assert a.issue == "週刊FLASH 2026年12月1日・8日合併号"
    assert "大竹しのぶ" in a.people and "坂本冬美" not in a.people
    assert a.mentions is None


def test_last_page_number():
    assert flash.last_page((F / "flash_tag.html").read_text("utf-8")) == 8


def test_article_text_only_body():
    t = flash.parse_article_text((F / "flash_article.html").read_text("utf-8"))
    assert "夜桜お七" in t and "祝い酒" in t
    assert "ほろ酔い満月" not in t
