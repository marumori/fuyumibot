"""CLI: python -m pipeline.run daily|weekly|import-seed|import-backcatalogue|import-fanclub-history"""
from __future__ import annotations

import argparse
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from . import http, liveness, picker, review, status
from .dictionary import Dictionaries
from .factcheck import verify
from .linking import flash_from_letters, mentions
from .merge import merge
from .model import Appearance, Clip, FlashArticle, FlashIssue, ForumTopic, Letter, Pick, load, save
from .seed_import import import_seed
from .sources import RawUpload, SourceError, bilibili, fanclub, flash, forum, sheet, to_clip, xembed, youtube

DATA = Path("data")
JST = timezone(timedelta(hours=9))

# Thin wrappers so tests can replace network access.
fetch_youtube = youtube.fetch_recent
fetch_bilibili = bilibili.fetch_recent
fetch_schedule = fanclub.fetch_schedule
fetch_bk_tv = fanclub.fetch_bk_tv
fetch_letters = fanclub.fetch_letters
fetch_x = xembed.fetch
fetch_flash_page = flash.fetch_tag_page
fetch_flash_text = flash.fetch_article_text
fetch_forum_listing = forum.fetch_listing
fetch_forum_date = forum.fetch_topic_date


def read_sheet(key: str, headers: list[str]) -> list[dict]:
    url = os.environ.get(key)
    return sheet.read_csv(url, headers) if url else []


def fetch_link(platform: str, vid: str, url: str) -> RawUpload | None:
    if platform == "x":
        return fetch_x(vid)
    if platform == "youtube":
        r = http.get("https://www.youtube.com/oembed", params={"url": url, "format": "json"})
        return RawUpload("youtube", vid, url, r.json()["title"], None) if r.status_code == 200 else None
    if platform == "bilibili":
        r = http.get("https://api.bilibili.com/x/web-interface/view", params={"bvid": vid},
                     headers={"User-Agent": http.BROWSER_UA})
        js = r.json() if r.status_code == 200 else {}
        if js.get("code") == 0:
            ts = datetime.fromtimestamp(js["data"]["pubdate"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return RawUpload("bilibili", vid, url, js["data"]["title"], ts)
    return None


def build_site(data_dir: Path, today: str) -> None:
    from .build import build_all
    build_all(data_dir, Path("site"), today)


def _today() -> str:
    return datetime.now(JST).date().isoformat()


def _app_key(a: Appearance) -> tuple:
    return (a.date, a.broadcaster, a.program, a.time)


def _store_letters(letters: list[Letter], flash: list[FlashIssue], fetched, d) -> tuple[list, list]:
    by_url = {lt.url: lt for lt in letters}
    pairs = []
    for lt, body in fetched:
        lt.mentions = mentions(lt.title + " " + body, d)
        by_url[lt.url] = lt
        pairs.append((lt, body))
    fl = {f.letter_url: f for f in flash}
    for f in flash_from_letters(pairs):
        fl[f.letter_url] = f
    return sorted(by_url.values(), key=lambda x: (x.date, x.url)), sorted(fl.values(), key=lambda f: f.issue_date)


def _update_readings(updates: dict[str, str]) -> None:
    if not updates:
        return
    p = DATA / "songs.yaml"
    songs = yaml.safe_load(p.read_text("utf-8"))
    for s in songs:
        if s["id"] in updates:
            s["yomi"], s["reviewed"] = updates[s["id"]], True
    p.write_text(yaml.safe_dump(songs, allow_unicode=True, sort_keys=False, width=200), "utf-8")


def _store_flash(articles: list[FlashArticle], fetched: list[FlashArticle]) -> list[FlashArticle]:
    by_url = {a.url: a for a in articles}
    for a in fetched:
        if a.url in by_url:
            a.mentions = by_url[a.url].mentions
        by_url[a.url] = a
    return sorted(by_url.values(), key=lambda a: (a.date, a.url))


def _read_flash_mentions(articles: list[FlashArticle], d, limit: int) -> None:
    """Read up to `limit` unread articles (newest first) to find songs; the text itself is not kept."""
    todo = sorted((a for a in articles if a.mentions is None), key=lambda a: a.date, reverse=True)[:limit]
    for a in todo:
        try:
            a.mentions = mentions(a.title + " " + fetch_flash_text(a.url), d)
        except Exception as e:  # noqa: BLE001 — try again on a later run
            print(f"FLASH article {a.url}: {e}")


def _store_topics(topics: list[ForumTopic], fetched: list[ForumTopic]) -> list[ForumTopic]:
    by_url = {t.url: t for t in topics}
    for t in fetched:
        if t.url not in by_url:
            by_url[t.url] = t
    return list(by_url.values())


def _read_topic_dates(topics: list[ForumTopic], limit: int) -> None:
    for t in [t for t in topics if t.date is None][:limit]:
        try:
            t.date = fetch_forum_date(t.url)
        except Exception as e:  # noqa: BLE001 — try again on a later run
            print(f"forum topic {t.url}: {e}")


def daily(today: str | None = None) -> None:
    today = today or _today()
    picker.SPECIAL_DAYS = DATA / "special_days.yaml"
    status.PATH = DATA / "status.json"
    status.load()
    review.load(DATA / "review.json")
    d = Dictionaries.load(DATA)
    clips = load(DATA / "clips.json", Clip)
    apps = load(DATA / "appearances.json", Appearance)
    letters = load(DATA / "letters.json", Letter)
    flash = load(DATA / "flash.json", FlashIssue)
    articles = load(DATA / "flash_articles.json", FlashArticle)
    topics = load(DATA / "forum_topics.json", ForumTopic)
    picks = load(DATA / "picks.json", Pick)

    # 1. owner's answers and links from the sheet
    answers = status.guard("sheet_review", lambda: read_sheet("SHEET_REVIEW_CSV", sheet.REVIEW_HEADERS), 0) or []
    _update_readings(sheet.apply_answers(answers, clips, d))
    if answers:
        d = Dictionaries.load(DATA)
    known = {(s.platform, s.id) for c in clips for s in c.sources}
    links = status.guard("sheet_add", lambda: read_sheet("SHEET_ADD_CSV", sheet.ADD_HEADERS), 0) or []
    raws = []
    new_links = [lk for lk in sheet.links_to_sources(links) if lk[:2] not in known]
    partial: list[RawUpload] = []

    def _fetch_links():
        got, errors = [], []
        for platform, vid, url in new_links:
            try:
                if raw := fetch_link(platform, vid, url):
                    got.append(raw)
            except Exception as e:  # noqa: BLE001 — one bad link must not stop the daily update
                errors.append(f"{url}: {e}")
        if errors:
            partial.extend(got)
            raise SourceError("; ".join(errors)[:500])
        return got
    raws += status.guard("sheet_links", _fetch_links, 0) or partial

    # 2. automatic sources
    raws += status.guard("youtube", fetch_youtube, 0) or []
    raws += status.guard("bilibili", fetch_bilibili, 0) or []
    clips = merge(clips, [to_clip(r, d) for r in raws], d.program)

    # 3. fan club
    by_key = {_app_key(a): a for a in apps}
    for a in status.guard("fc_schedule", fetch_schedule, 0) or []:
        by_key[_app_key(a)] = a
    year = int(today[:4])
    prev = [a for a in by_key.values() if a.date.startswith(str(year))]
    got = status.guard("fc_bk_tv", lambda: fetch_bk_tv(year), len(prev))
    if got is not None:  # add-only: the backnumber lags the schedule page by days
        by_key.update({_app_key(a): a for a in got})
    apps = sorted(by_key.values(), key=_app_key)
    months = [(year, int(today[5:7]))]
    if int(today[8:10]) <= 3:
        prevm = date.fromisoformat(today).replace(day=1) - timedelta(days=1)
        months.append((prevm.year, prevm.month))
    for y, m in months:
        prev_n = len([lt for lt in letters if lt.date.startswith(f"{y}-{m:02d}")])
        got = status.guard("fc_letters", lambda: fetch_letters(y, m), prev_n)
        if got is not None:
            letters, flash = _store_letters(letters, flash, got, d)

    got = status.guard("flash", lambda: fetch_flash_page(1)[0], 0)
    if got is not None:
        articles = _store_flash(articles, got)
    _read_flash_mentions(articles, d, limit=10)
    got = status.guard("forum", lambda: fetch_forum_listing(1)[0], 0)
    if got is not None:
        topics = _store_topics(topics, got)
    _read_topic_dates(topics, limit=20)

    # 4. derive
    verify(clips, apps, d, forum=topics)
    pick_rows = status.guard("sheet_pick", lambda: read_sheet("SHEET_PICK_CSV", sheet.PICK_HEADERS), 0) or []
    overrides = sheet.overrides(pick_rows, clips)
    for day in (today, (date.fromisoformat(today) + timedelta(days=1)).isoformat()):
        # always recompute (deterministic per day), so rule or name changes apply at once
        picks = [p for p in picks if p.date != day]
        picks.append(picker.pick(day, clips, apps, letters, overrides, picks, d))
    for s in d.songs:
        if not s.get("reviewed"):
            review.add("reading_unreviewed", s["id"], f"「{s['title']}」の読み方は「{s['yomi']}」で合っていますか")

    # 5. save + build
    save(DATA / "clips.json", sorted(clips, key=lambda c: (c.broadcast_date, c.id)))
    save(DATA / "appearances.json", apps)
    save(DATA / "letters.json", letters)
    save(DATA / "flash.json", flash)
    save(DATA / "flash_articles.json", articles)
    save(DATA / "forum_topics.json", sorted(topics, key=lambda t: (t.date or "", t.url)))
    save(DATA / "picks.json", sorted(picks, key=lambda p: p.date)[-400:])
    review.save(DATA / "review.json")
    status.save()
    build_site(DATA, today)


def weekly(today: str | None = None) -> None:
    status.PATH = DATA / "status.json"
    status.load()
    clips = load(DATA / "clips.json", Clip)
    cur = status.data()["cursors"]
    cur["liveness"] = liveness.check(clips, offset=cur.get("liveness", 0))
    save(DATA / "clips.json", clips)
    status.save()
    build_site(DATA, today or _today())


def import_fanclub_history(max_requests: int = 40) -> None:
    """Back-catalogue of TV records (2006–) and 冬美便り (2004–), resumable, spread over several runs."""
    status.PATH = DATA / "status.json"
    status.load()
    d = Dictionaries.load(DATA)
    done = set(status.data()["cursors"].get("fc_history_done", []))
    year = int(_today()[:4])
    jobs = [f"tv:{y}" for y in range(year, 2005, -1)]
    jobs += [f"letter:{y}:{m}" for y in range(year, 2003, -1) for m in range(12, 0, -1)
             if f"{y}-{m:02d}" <= _today()[:7]]
    apps = {_app_key(a): a for a in load(DATA / "appearances.json", Appearance)}
    letters, flash = load(DATA / "letters.json", Letter), load(DATA / "flash.json", FlashIssue)
    n = 0
    for job in jobs:
        if job in done or n >= max_requests:
            continue
        n += 1
        parts = job.split(":")
        try:
            if parts[0] == "tv":
                apps.update({_app_key(a): a for a in fetch_bk_tv(int(parts[1]))})
            else:
                letters, flash = _store_letters(letters, flash, fetch_letters(int(parts[1]), int(parts[2])), d)
            done.add(job)
        except Exception as e:  # noqa: BLE001
            print(f"{job}: {e}")
    status.data()["cursors"]["fc_history_done"] = sorted(done)
    save(DATA / "appearances.json", sorted(apps.values(), key=_app_key))
    save(DATA / "letters.json", letters)
    save(DATA / "flash.json", flash)
    status.save()
    print(f"{n} pages fetched, {len(jobs) - len(done)} remaining")


def import_flash_history(max_articles: int = 40) -> None:
    """All FLASH tag pages, then song mentions for up to `max_articles` articles per run."""
    d = Dictionaries.load(DATA)
    articles = load(DATA / "flash_articles.json", FlashArticle)
    first, last = fetch_flash_page(1)
    articles = _store_flash(articles, first)
    for n in range(2, last + 1):
        try:
            articles = _store_flash(articles, fetch_flash_page(n)[0])
        except Exception as e:  # noqa: BLE001
            print(f"FLASH page {n}: {e}")
    _read_flash_mentions(articles, d, limit=max_articles)
    save(DATA / "flash_articles.json", articles)
    left = sum(a.mentions is None for a in articles)
    print(f"{len(articles)} FLASH articles, {left} still to read")


def import_forum_history(max_topics: int = 150) -> None:
    """All forum listing pages, then the post date of up to `max_topics` topics per run (2 s apart)."""
    topics = load(DATA / "forum_topics.json", ForumTopic)
    first, last = fetch_forum_listing(1)
    topics = _store_topics(topics, first)
    for n in range(2, last + 1):
        try:
            topics = _store_topics(topics, fetch_forum_listing(n)[0])
        except Exception as e:  # noqa: BLE001
            print(f"forum page {n}: {e}")
    _read_topic_dates(topics, limit=max_topics)
    save(DATA / "forum_topics.json", sorted(topics, key=lambda t: (t.date or "", t.url)))
    print(f"{len(topics)} forum topics, {sum(t.date is None for t in topics)} dates still to read")


def cmd_import_seed() -> None:
    d = Dictionaries.load(DATA)
    review.load(DATA / "review.json")
    clips = import_seed(DATA / "seed" / "x_table.md", d)
    save(DATA / "clips.json", sorted(clips, key=lambda c: (c.broadcast_date, c.id)))
    review.save(DATA / "review.json")
    print(f"{len(clips)} clips, {len(review.items())} review items")


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
    clips = load(DATA / "clips.json", Clip)
    before = len(clips)
    clips = merge(clips, [to_clip(r, d) for r in raws], d.program)
    save(DATA / "clips.json", sorted(clips, key=lambda c: (c.broadcast_date, c.id)))
    review.save(DATA / "review.json")
    print(f"{len(raws)} uploads fetched, {len(clips) - before} new clips")


def main(argv=None) -> None:
    cmds = {"daily": daily, "weekly": weekly, "import-seed": cmd_import_seed,
            "import-backcatalogue": cmd_import_backcatalogue, "import-fanclub-history": import_fanclub_history,
            "import-flash-history": import_flash_history, "import-forum-history": import_forum_history}
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=list(cmds))
    a = ap.parse_args(argv)
    cmds[a.command]()


if __name__ == "__main__":
    main()
