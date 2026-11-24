"""Write the static site's data (site/data/*.json) and one share page per clip (site/v/<id>/)."""
from __future__ import annotations

import html
import json
import os
import random
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

from . import jp
from .dictionary import Dictionaries
from .factcheck import program_matches
from .model import Appearance, Clip, FlashArticle, Letter, Pick, load

TEMPLATE = Path(__file__).parent / "templates" / "clip.html"
RERUN = {"再放送", "VTR", "VTR出演"}
MOODS = [("恋", "恋のうた"), ("酒", "お酒のうた"), ("祝", "お祝いのうた"), ("母", "母のうた"), ("祭", "お祭りのうた"),
         ("故郷", "ふるさとのうた"), ("桜", "桜のうた"), ("雪", "雪のうた"), ("月", "月のうた")]
PREFS = ("北海道 青森 岩手 宮城 秋田 山形 福島 茨城 栃木 群馬 埼玉 千葉 東京 神奈川 新潟 富山 石川 福井 山梨 長野 岐阜 静岡 愛知 三重 "
         "滋賀 京都 大阪 兵庫 奈良 和歌山 鳥取 島根 岡山 広島 山口 徳島 香川 愛媛 高知 福岡 佐賀 長崎 熊本 大分 宮崎 鹿児島 沖縄").split()
THEME_SIZE = 8


def site_url() -> str:
    return os.environ.get("SITE_URL", "https://fuyumi.pages.dev").rstrip("/")


def _md_label(mmdd: str) -> str:
    return f"{int(mmdd[:2])}月{int(mmdd[3:])}日"


def _thumb(c: Clip) -> str | None:
    s = c.best_source()
    return f"https://i.ytimg.com/vi/{s.id}/hqdefault.jpg" if s and s.platform == "youtube" else None


class Builder:
    def __init__(self, data_dir: Path, today: str, now: str | None):
        self.d = Dictionaries.load(data_dir)
        self.today = today
        self.now = now or datetime.now().strftime("%Y-%m-%dT%H:%M")
        all_clips = load(data_dir / "clips.json", Clip)
        self.clips = [c for c in all_clips if not c.hidden and c.best_source()]
        self.apps = load(data_dir / "appearances.json", Appearance)
        self.letters = sorted(load(data_dir / "letters.json", Letter), key=lambda x: x.date, reverse=True)
        self.flash = sorted(load(data_dir / "flash_articles.json", FlashArticle), key=lambda a: a.date, reverse=True)
        self.picks = {p.date: p for p in load(data_dir / "picks.json", Pick)}
        rp = data_dir / "review.json"
        self.review = json.loads(rp.read_text("utf-8")) if rp.exists() else []
        self.by_id = {c.id: c for c in self.clips}

    # ---- cards -------------------------------------------------------------------------
    def title_label(self, c: Clip) -> str:
        names = [self.d.song(s)["title"] for s in c.songs if s in self.d._song_by_id]
        return "".join(f"「{n}」" for n in names) or "トーク・その他"

    def card(self, c: Clip) -> dict:
        s = c.best_source()
        return {"id": c.id, "title_label": self.title_label(c),
                "date_label": jp.format_date(c.broadcast_date, with_wareki=True),
                "program": self.d.program(c.program) or c.program, "performers_label": "、".join(c.performers),
                "platform": s.platform, "source": {"platform": s.platform, "id": s.id, "url": s.url},
                "thumb": _thumb(c), "verified": bool(c.verified), "url": f"/v/{c.id}/"}

    def cards(self, clips, limit=None):
        clips = sorted(clips, key=lambda c: c.broadcast_date, reverse=True)
        return [self.card(c) for c in clips[:limit]]

    def letter_item(self, lt: Letter) -> dict:
        return {"date_label": jp.format_date(lt.date), "title": lt.title, "url": lt.url}

    def clips_for_mentions(self, m: dict, limit=3):
        songs, progs = set(m.get("songs", [])), m.get("programs", [])
        out = [c for c in self.clips if set(c.songs) & songs or any(program_matches(c.program, p, self.d) for p in progs)]
        return self.cards(out, limit)

    def song_links(self, song_ids) -> list[dict]:
        """Each mentioned song, with our newest playable video of it when we have one."""
        out = []
        for sid in song_ids or []:
            if sid not in self.d._song_by_id:
                continue
            have = [c for c in self.clips if sid in c.songs]
            have.sort(key=lambda c: (c.youtube() is not None, c.broadcast_date), reverse=True)
            out.append({"title": self.d.song(sid)["title"], "clip": self.card(have[0]) if have else None})
        return out

    def flash_item(self, a: FlashArticle) -> dict:
        people = list(dict.fromkeys([*a.people, *(a.mentions or {}).get("people", [])]))
        with_people = [{"name": p, "clips": cl} for p in people if p != "坂本冬美"
                       and (cl := self.cards([c for c in self.clips if p in c.performers], 3))]
        return {"date_label": jp.format_date(a.date), "year_label": jp.year_label(int(a.date[:4])), "title": a.title,
                "url": a.url, "issue": a.issue, "people": a.people,
                "songs": self.song_links((a.mentions or {}).get("songs")), "with_people": with_people}

    def themes(self) -> list[dict]:
        """Theme playlists the viewer can switch to: 季節 / 気持ち / ふるさと. YouTube clips first (they play in a row)."""
        rng = random.Random(self.today)

        def pick(pred):
            pool = [c for c in self.clips if any(pred(self.d.song(s)) for s in c.songs if s in self.d._song_by_id)]
            pool.sort(key=lambda c: c.id)
            rng.shuffle(pool)
            pool.sort(key=lambda c: c.youtube() is None)
            return [self.card(c) for c in pool[:THEME_SIZE]]

        groups = [("季節", [(s, s, lambda x, s=s: s in x.get("season", [])) for s in "春夏秋冬"]),
                  ("気持ち", [(k, label, lambda x, k=k: k in x.get("themes", [])) for k, label in MOODS]),
                  ("ふるさと", [(p, p, lambda x, p=p: p in x.get("places", [])) for p in PREFS])]
        out = []
        for label, defs in groups:
            themes = [{"key": k, "label": lab, "clips": cl} for k, lab, pred in defs if (cl := pick(pred))]
            if themes:
                out.append({"label": label, "themes": themes})
        return out

    def this_day(self, items, date_of) -> tuple[list, bool]:
        """Items from today's month-day in past years, newest first (that day only)."""
        exact = [i for i in items if date_of(i)[5:] == self.today[5:] and date_of(i) < self.today]
        return sorted(exact, key=date_of, reverse=True), True

    # ---- sections ----------------------------------------------------------------------
    def appearances(self) -> list[dict]:
        yday = (date.fromisoformat(self.today) - timedelta(days=1)).isoformat()
        out = []
        for a in sorted(self.apps, key=lambda a: (a.date, a.time)):
            if a.date not in (yday, self.today):
                continue
            start = a.time.split("〜")[0] if a.time else ""
            clip = next((c for c in self.clips if c.broadcast_date == a.date
                         and program_matches(c.program, a.program, self.d)), None)
            if clip:
                state = "clip"
            elif a.note in RERUN:
                state = "rerun"
            elif a.date == self.today and start and self.now[11:16] < start.zfill(5):
                state = "before"
            else:
                state = "aired"
            if a.date == yday and state not in ("clip", "aired"):
                continue
            out.append({"date_label": jp.format_date(a.date), "is_today": a.date == self.today, "start": start,
                        "time_label": a.time, "broadcaster": a.broadcaster, "program": a.program, "note": a.note,
                        "kind": a.kind, "state": state, "clip": self.card(clip) if clip else None})
        return out

    def on_this_day(self) -> dict:
        chosen, is_exact = self.this_day(self.clips, lambda c: c.broadcast_date)
        years: dict[int, list] = {}
        for c in chosen:
            years.setdefault(int(c.broadcast_date[:4]), []).append(c)
        return {"exact": is_exact, "years": [{"year": y, "year_label": jp.year_label(y), "clips": self.cards(years[y], 4)}
                                             for y in sorted(years, reverse=True)[:8]]}

    def today_json(self) -> dict:
        p = self.picks.get(self.today)
        pick = None
        if p:
            pick = {"theme_title": p.theme_title, "reason": p.reason,
                    "clips": [self.card(self.by_id[i]) for i in p.clip_ids if i in self.by_id]}
        lts, l_exact = self.this_day(self.letters, lambda x: x.date)
        letters = {"exact": l_exact, "items": [dict(self.letter_item(lt), year_label=jp.year_label(int(lt.date[:4])),
                                                    clips=self.clips_for_mentions(lt.mentions, 2)) for lt in lts[:6]]}
        arts, f_exact = self.this_day(self.flash, lambda a: a.date)
        flash = {"exact": f_exact, "items": [self.flash_item(a) for a in arts[:4]]}
        return {"date": self.today, "date_label": jp.format_date(self.today)[5:].lstrip("0"),
                "appearances": self.appearances(), "pick": pick, "on_this_day": self.on_this_day(),
                "letters": letters, "flash": flash}

    def days(self) -> tuple[dict, dict]:
        cal, days = {}, {}
        for c in self.clips:
            days.setdefault(c.broadcast_date[5:], {}).setdefault(int(c.broadcast_date[:4]), {"clips": [], "letters": [], "flash": []})["clips"].append(c)
        for lt in self.letters:
            days.setdefault(lt.date[5:], {}).setdefault(int(lt.date[:4]), {"clips": [], "letters": [], "flash": []})["letters"].append(self.letter_item(lt))
        for a in self.flash:
            days.setdefault(a.date[5:], {}).setdefault(int(a.date[:4]), {"clips": [], "letters": [], "flash": []})["flash"].append(
                self.flash_item(a))
        out = {}
        for md, ys in days.items():
            cal[md] = {k: sum(len(v[k2]) for v in ys.values()) for k, k2 in (("videos", "clips"), ("letters", "letters"), ("flash", "flash"))}
            out[md] = {"label": _md_label(md), "years": [
                {"year": y, "year_label": jp.year_label(y), "clips": self.cards(ys[y]["clips"]),
                 "letters": ys[y]["letters"], "flash": ys[y]["flash"]} for y in sorted(ys, reverse=True)]}
        return dict(sorted(cal.items())), out

    def songs(self) -> tuple[list, dict]:
        per: dict[str, list] = {}
        for c in self.clips:
            for s in c.songs:
                per.setdefault(s, []).append(c)
        index, pages = [], {}
        for sid, cl in per.items():
            s = self.d.song(sid)
            index.append({"id": sid, "title": s["title"], "yomi": s["yomi"], "gyo": jp.gyo(s["yomi"]), "count": len(cl)})
            pages[sid] = {"title": s["title"], "yomi": s["yomi"], "clips": self.cards(cl),
                          "letters": [self.letter_item(lt) for lt in self.letters if sid in lt.mentions.get("songs", [])][:10]}
        index.sort(key=lambda s: jp.sort_key(s["yomi"]))
        return index, pages

    def clip_page(self, c: Clip) -> str:
        card = self.card(c)
        others = [o for o in self.clips if o.id != c.id and set(o.songs) & set(c.songs)]
        lo = (date.fromisoformat(c.broadcast_date) - timedelta(days=7)).isoformat()
        hi = (date.fromisoformat(c.broadcast_date) + timedelta(days=7)).isoformat()
        data = dict(card, sources=[{"platform": s.platform, "id": s.id, "url": s.url} for s in c.sources if s.alive],
                    verified_info=c.verified, date_source=c.date_source,
                    others=self.cards(others, 6),
                    letters=[self.letter_item(lt) for lt in self.letters if lo <= lt.date <= hi][:5])
        y, m, dd = c.broadcast_date.split("-")
        who = c.performers[0] if c.performers else "坂本冬美"
        og_title = f"{card['title_label'] if c.songs else card['program'] or 'トーク・その他'}{who} {int(y)}年{int(m)}月{int(dd)}日"
        url = f"{site_url()}/v/{c.id}/"
        rep = {"{{TITLE}}": card["title_label"], "{{OG_TITLE}}": og_title,
               "{{OG_DESC}}": "、".join(x for x in [card["program"], card["performers_label"]] if x) or "今日の冬美",
               "{{URL}}": url, "{{IMAGE}}": card["thumb"] or f"{site_url()}/og-default.png"}
        out = TEMPLATE.read_text("utf-8")
        for k, v in rep.items():
            out = out.replace(k, html.escape(v, quote=True))
        return out.replace("{{DATA}}", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    if not path.exists() or path.read_text("utf-8") != text:
        path.write_text(text, "utf-8")


def build_all(data_dir, out_dir, today: str, now: str | None = None) -> None:
    data_dir, out_dir = Path(data_dir), Path(out_dir)
    b = Builder(data_dir, today, now)
    od = out_dir / "data"
    _write(od / "today.json", b.today_json())
    cal, days = b.days()
    _write(od / "calendar.json", cal)
    _write(od / "themes.json", b.themes())
    shutil.rmtree(od / "days", ignore_errors=True)
    for md, v in days.items():
        _write(od / "days" / f"{md}.json", v)
    index, pages = b.songs()
    _write(od / "songs.json", index)
    shutil.rmtree(od / "songs", ignore_errors=True)
    for sid, v in pages.items():
        _write(od / "songs" / f"{sid}.json", v)
    _write(od / "review.json", [{"種類": r["kind"], "対象": r["ref"], "内容": r["detail"]} for r in b.review])
    vdir = out_dir / "v"
    keep = {c.id for c in b.clips}
    if vdir.exists():
        for p in vdir.iterdir():
            if p.name not in keep:
                shutil.rmtree(p)
    for c in b.clips:
        _write(vdir / c.id / "index.html", b.clip_page(c))
