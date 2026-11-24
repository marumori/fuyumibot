"""Build a deterministic copy of the site (static files + fixture data) for browser tests."""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipeline import build  # noqa: E402
from pipeline.model import Appearance, FlashArticle, Letter, Pick, Source, save  # noqa: E402
from tests.helpers import mk  # noqa: E402


def make(out: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(root / "site", out, ignore=shutil.ignore_patterns("data", "v"))
    data = out.parent / "ui_data"
    data.mkdir(exist_ok=True)
    for f in ["songs.yaml", "performers.yaml", "programs.yaml", "captions.yaml"]:
        shutil.copy(root / "data" / f, data / f)
    a = mk("2025-12-31", ["yozakura-oshichi"], program="紅白", performers=["坂本冬美", "M!LK"], n="a")
    a.verified = {"broadcaster": "NHK総合", "program": "NHK紅白歌合戦", "note": ""}
    b = mk("2024-12-31", ["iwaizake"], n="b")
    c = mk("2023-12-31", ["abare-daiko"], n="c")
    e = mk("2022-12-31", ["hirari"], n="e")
    x = mk("2021-12-31", ["yuki-shinshin"], n="x", yt=False)
    x.sources[0].url = "https://x.com/jounotakeuchi/status/2006396667155919096"
    bl = mk("2020-12-31", ["omatsuri-mambo"], n="bl", yt=False)
    bl.sources = [Source("bilibili", "BV1szWZ6NEDE", "https://www.bilibili.com/video/BV1szWZ6NEDE")]
    clips = [a, b, c, e, x, bl]
    for i, cl in enumerate(clips):
        cl.sources[0].uploaded_at = f"2026-11-1{i}T00:00:00Z"
    save(data / "clips.json", clips)
    save(data / "appearances.json", [Appearance("2026-12-31", "19:20〜23:45", "NHK総合", "第77回NHK紅白歌合戦", "TV", "")])
    save(data / "letters.json", [Letter("2026-12-29", "紅白リハーサル", "https://fuyumi-fc.com/letter/index.php?y=2026&m=12#post1",
                                        {"songs": ["yozakura-oshichi"], "programs": [], "people": []}),
                                 Letter("2025-12-31", "大みそかの便り", "https://fuyumi-fc.com/letter/index.php?y=2025&m=12#post9",
                                        {"songs": ["yozakura-oshichi"], "programs": [], "people": []})])
    save(data / "flash_articles.json", [
        FlashArticle("2024-12-31", "紅白の舞台裏を語る", "https://smart-flash.jp/entertainment/entertainment-news/1/",
                     "週刊FLASH 2025年1月7日号", ["M!LK"], {"songs": ["yozakura-oshichi", "senbonzakura"], "programs": [], "people": []}),
        FlashArticle("2026-12-22", "モゴモゴ対談", "https://smart-flash.jp/entertainment/entertainment-news/2/", "", [], None)])
    save(data / "picks.json", [Pick("2026-12-31", "大みそかのうた", "紅白・年忘れの季節", [a.id, b.id, c.id, e.id])])
    build.build_all(data, out, "2026-12-31", now="2026-12-31T08:00")


if __name__ == "__main__":
    make(Path(sys.argv[1]))
