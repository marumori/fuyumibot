import re

import pytest

from pipeline.dictionary import Dictionaries


@pytest.fixture(scope="session")
def d():
    return Dictionaries.load("data")


def read_seed_titles(path="data/seed/x_table.md"):
    out = []
    for line in open(path, encoding="utf-8"):
        if re.match(r"\| \d\d-\d\d \|", line):
            out.append(line.split("|")[3].strip())
    return out
