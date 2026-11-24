"""CLI: python -m pipeline.run <command>"""
from __future__ import annotations

import argparse
from pathlib import Path

from . import review
from .dictionary import Dictionaries
from .model import Clip, save
from .seed_import import import_seed
from .sources import to_clip
from .sources import bilibili, youtube
from .merge import merge
from .model import load
import os

DATA = Path("data")


def cmd_import_seed() -> None:
    d = Dictionaries.load(DATA)
    review.load(DATA / "review.json")
    clips = import_seed(DATA / "seed" / "x_table.md", d)
    save(DATA / "clips.json", sorted(clips, key=lambda c: (c.broadcast_date, c.id)))
    review.save(DATA / "review.json")
    print(f"{len(clips)} clips, {len(review.items())} review items")


def ingest(raws, d) -> int:
    clips = load(DATA / "clips.json", Clip)
    before = len(clips)
    clips = merge(clips, [to_clip(r, d) for r in raws], d.program)
    save(DATA / "clips.json", sorted(clips, key=lambda c: (c.broadcast_date, c.id)))
    return len(clips) - before


def cmd_import_backcatalogue() -> None:
    d = Dictionaries.load(DATA)
    review.load(DATA / "review.json")
    raws = []
    try:
        raws += bilibili.fetch_all()
    except Exception as e:  # blocked from this network: Bilibili links then come via the sheet
        print(f"bilibili unavailable: {e}")
    key = os.environ.get("YT_API_KEY")
    raws += youtube.fetch_all(key) if key else youtube.fetch_recent()
    if not key:
        print("YT_API_KEY not set: YouTube limited to the latest 15 uploads")
    added = ingest(raws, d)
    review.save(DATA / "review.json")
    print(f"{len(raws)} uploads fetched, {added} new clips")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["import-seed", "import-backcatalogue"])
    a = ap.parse_args(argv)
    {"import-seed": cmd_import_seed, "import-backcatalogue": cmd_import_backcatalogue}[a.command]()


if __name__ == "__main__":
    main()
