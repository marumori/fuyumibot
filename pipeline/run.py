"""CLI: python -m pipeline.run <command>"""
from __future__ import annotations

import argparse
from pathlib import Path

from . import review
from .dictionary import Dictionaries
from .model import Clip, save
from .seed_import import import_seed

DATA = Path("data")


def cmd_import_seed() -> None:
    d = Dictionaries.load(DATA)
    review.load(DATA / "review.json")
    clips = import_seed(DATA / "seed" / "x_table.md", d)
    save(DATA / "clips.json", sorted(clips, key=lambda c: (c.broadcast_date, c.id)))
    review.save(DATA / "review.json")
    print(f"{len(clips)} clips, {len(review.items())} review items")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["import-seed"])
    a = ap.parse_args(argv)
    {"import-seed": cmd_import_seed}[a.command]()


if __name__ == "__main__":
    main()
