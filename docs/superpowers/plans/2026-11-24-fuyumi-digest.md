# 今日の冬美 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A free, link-only, Japanese-only, senior-friendly static site that gathers the owner's 坂本冬美 clips from X, Bilibili and YouTube into a daily digest (今日のおすすめ, あの年の今日, TV appearances, 冬美便り, FLASH 対談, calendar, song index), updated daily by GitHub Actions.

**Architecture:** A Python pipeline (`pipeline/`) imports the seed list, ingests YouTube/Bilibili/Sheet/fan-club data, parses titles with a song dictionary, merges and fact-checks clips, picks the daily playlist, and writes small JSON files plus one static HTML page per clip into `site/`. The front end is plain HTML/CSS/vanilla JS reading that JSON. A GitHub Actions workflow runs the pipeline daily and deploys `site/` to Cloudflare Pages from a private repo.

**Tech Stack:** Python 3.12, requests, beautifulsoup4, pykakasi, PyYAML, pytest; HTML/CSS/vanilla JS (no framework, no build step); Playwright (pre-installed) for UI checks; GitHub Actions; Cloudflare Pages (`cloudflare/wrangler-action`).

**Spec:** `docs/superpowers/specs/2026-11-24-fuyumi-digest-design.md` and `萬事屋請review.md` (the review wins on conflicts; spec §13–14 summarise).

## Global Constraints

- All visible UI text Japanese. Dates `2025年12月31日（水）`; year labels add 和暦 `1994年（平成6年）` (not on today's date). Era starts: 平成 1989-01-08, 令和 2019-05-01.
- Song titles always displayed inside 「」. Performers joined with 「、」.
- Wording (exact): 4曲つづけて聴く (N曲 as count), 曲名でさがす, ✓ 放送日確認済み, 映像はまだありません, 新しい映像, トーク・その他, 週刊FLASH 対談（火曜発売）, あの年の今日, 今日のおすすめ, 今日の出演, 使い方, 共有する, LINEで送る, Xでポスト, リンクをコピー, Xで見る, ← 戻る, 非公式ファンサイト.
- Base font ≥ 20px in rem (`html{font-size:125%}` → 1rem = 20px), line-height ≥ 1.7, tap targets ≥ 56px, layout survives 200% text scale, accent `#A3002B` (light) / `#FF6B8A` (dark), no text over thumbnails, no autoplay, no emoji as sole meaning.
- `<meta name="robots" content="noindex,nofollow">` on every page; `robots.txt` = `User-agent: *\nDisallow: /`; no sitemap.
- From 冬美便り store only `date,title,url,mentions` — never body text or raw HTML in the repo.
- All date logic in `Asia/Tokyo`.
- Playlist (4曲つづけて聴く) uses only clips with a live YouTube source.
- Running cost ¥0: no paid APIs. Secrets: `YT_API_KEY` (one-time import only), `SHEET_ADD_CSV`, `SHEET_PICK_CSV`, `SHEET_REVIEW_CSV`, `CF_API_TOKEN`, `CF_ACCOUNT_ID`.
- Polite scraping: one request per page per run, UA `fuyumi-digest-bot (fan site; contact on site)`, ≥ 2s between fan-club requests.
- Unparseable or uncertain things go to the 確認 queue (`data/review.json` → shown to owner via the Sheet); never guessed silently.

## Review Focus

1. **A scrape returns 200 but zero/garbled rows** (fan club redesign, Bilibili -352/412 from GitHub IPs) → keep last-good data, record failure in `status.json`; reject results whose row count drops > 20%. Test in Task 9.
2. **Day with no content at all** (no appearance, no あの年の今日 within ±3 days, no YouTube-playable clips for a theme) → home still renders sensible sections; picker falls through to 珍しい映像 and finally any 3 YouTube clips. Tests in Tasks 7 and 11.
3. **Title with only a date or （無曲名）, or a song not in the dictionary** → clip shown as 「トーク・その他」 with program name; unknown song text added to review queue, not invented as a song. Test in Task 3.
4. **Post-time date late in UTC evening** (15:00–24:00 UTC) → broadcast date shifts +1 day in JST and is marked `date_source="post_time"`, never ✓. Test in Task 4.
5. **Opened inside LINE's in-app browser / X embed blocked by login** → banner with 「Safari（Chrome）で開く」 guidance; X card falls back to 「Xで見る」 after 4s with no rendered iframe. Tests in Task 12.

---

## File Structure

```
pyproject.toml
pipeline/
  model.py          dataclasses + JSON (de)serialisation
  jp.py             normalise text, yomi sort key, 和暦, Japanese date formatting
  dictionary.py     songs / performers / programs dictionaries + alias lookup
  title_parser.py   parse upload titles (X/YouTube style and Bilibili style)
  seed_import.py    x_table.md → clips
  merge.py          cross-platform merge/dedup
  sources/youtube.py  sources/bilibili.py  sources/sheet.py  sources/xembed.py
  sources/fanclub.py  (schedule, bk_tv, bk_magazine, letters)
  factcheck.py      clip ↔ appearance matching
  linking.py        letter mentions, FLASH issues
  picker.py         今日のおすすめ rules
  liveness.py       weekly dead-source check
  build.py          write site/data/*.json and site/v/<id>/index.html
  run.py            CLI: `python -m pipeline.run daily|weekly|import-seed|import-backcatalogue`
data/
  seed/x_table.md   (exists)
  songs.yaml performers.yaml programs.yaml special_days.yaml   (owner-facing dictionaries)
  clips.json appearances.json letters.json flash.json picks.json review.json status.json  (pipeline state)
site/
  index.html calendar.html songs.html song.html usage.html robots.txt manifest.webmanifest icon-512.png
  assets/app.css assets/common.js assets/home.js assets/calendar.js assets/songs.js assets/player.js assets/share.js
  data/            (generated)
  v/<clip-id>/index.html   (generated clip pages)
tests/              pytest per module; tests/ui/ Playwright checks
.github/workflows/daily.yml weekly.yml
docs/setup.md       owner setup guide (Japanese)
```

---

### Task 1: Project skeleton, model, Japanese text utilities

**Files:**
- Create: `pyproject.toml`, `pipeline/__init__.py`, `pipeline/model.py`, `pipeline/jp.py`, `.gitignore`
- Test: `tests/test_jp.py`, `tests/test_model.py`

**Interfaces:**
- Produces:
  - `model.Source(platform: Literal["youtube","bilibili","x"], id: str, url: str, uploaded_at: str|None, has_video: bool=True, alive: bool=True)`
  - `model.Clip(id: str, broadcast_date: str, date_source: Literal["title","post_time"], program: str|None, songs: list[str], performers: list[str], title_raw: str, sources: list[Source], verified: dict|None=None, tags: list[str]=[], hidden: bool=False)`; `Clip.best_source() -> Source|None` (alive, youtube > bilibili > x); `Clip.youtube() -> Source|None`
  - `model.Appearance(date, time, broadcaster, program, kind, note)`; `model.Letter(date, title, url, mentions: dict)`; `model.FlashIssue(issue_date, guest, letter_url)`; `model.Pick(date, theme_title, reason, clip_ids)`
  - `model.load(path, cls) -> list`, `model.save(path, items)` — UTF-8 JSON, `ensure_ascii=False`, sorted keys, stable order (so unchanged data produces identical bytes).
  - `jp.normalize(s) -> str` — NFKC except keep 〜 (map U+FF5E/U+007E between CJK → U+301C), collapse whitespace incl. U+3000, unify `!`/`！` to `！`, `&`/`＆` to `＆`.
  - `jp.sort_key(yomi: str) -> tuple` — katakana→hiragana, small→full, ー→preceding vowel, strip punctuation 「」・！〜 and anything after 〜; primary key on 清音 (dakuten stripped), secondary on original.
  - `jp.gyo(yomi) -> str` — one of あ か さ た な は ま や ら わ 英数字.
  - `jp.wareki(year:int, month:int=12, day:int=31) -> str` e.g. `平成6年`, `平成元年`.
  - `jp.format_date(iso: str, with_wareki=False) -> str` e.g. `2025年12月31日（水）`, `1994年12月31日（土）（平成6年）`.

- [ ] **Step 1: Write failing tests**

```python
def test_sort_key_orders_gojuon():
    words = ["れーざーびーむ", "あばれだいこ", "がんばれ", "かもめ", "ぱぴぷ", "はな"]
    assert sorted(words, key=jp.sort_key) == ["あばれだいこ","かもめ","がんばれ","はな","ぱぴぷ","れーざーびーむ"]
def test_long_vowel_takes_previous_vowel():
    assert jp.sort_key("れーざー")[0] == jp.sort_key("れえざあ")[0]
def test_gyo():
    assert jp.gyo("よざくらおしち") == "や"; assert jp.gyo("TATTOO") == "英数字"; assert jp.gyo("がんばれ") == "か"
def test_wareki_boundaries():
    assert jp.wareki(1989,1,7) == "昭和64年"; assert jp.wareki(1989,1,8) == "平成元年"
    assert jp.wareki(2019,4,30) == "平成31年"; assert jp.wareki(2019,5,1) == "令和元年"
def test_format_date():
    assert jp.format_date("2025-12-31") == "2025年12月31日（水）"
    assert jp.format_date("1994-12-31", with_wareki=True) == "1994年12月31日（土）（平成6年）"
def test_normalize_wave_dash_and_spaces():
    assert jp.normalize("森口博子でしょう～　花のワルツ") == "森口博子でしょう〜 花のワルツ"
def test_best_source_prefers_alive_youtube():  # in test_model.py
    ...  # Clip with x, bilibili, youtube(alive=False) → bilibili
def test_save_is_stable(tmp_path): ...  # save twice → identical bytes
```

- [ ] **Step 2:** `pytest tests/test_jp.py tests/test_model.py -v` → FAIL (module not found)
- [ ] **Step 3:** Implement `model.py`, `jp.py`; `pyproject.toml` with deps `requests beautifulsoup4 pykakasi pyyaml pytest`, Python `>=3.12`.
- [ ] **Step 4:** Run tests → PASS
- [ ] **Step 5:** `git init`, commit `feat: project skeleton, data model, Japanese text utils`

---

### Task 2: Dictionaries (songs, performers, programs) with seeded readings

**Files:**
- Create: `pipeline/dictionary.py`, `data/songs.yaml`, `data/performers.yaml`, `data/programs.yaml`, `scripts/draft_dictionary.py`
- Test: `tests/test_dictionary.py`

**Interfaces:**
- Consumes: `jp.normalize`, `jp.sort_key`
- Produces:
  - YAML shapes: `songs.yaml`: list of `{id, title, yomi, aliases: [..], original_artist?, season: [春|夏|秋|冬], themes: [酒|祝|故郷|恋|母|祭|桜|雪|月], reviewed: bool}`; `performers.yaml`: list of `{name, aliases: [..], unit: bool}`; `programs.yaml`: list of `{name, aliases: [..]}` where `name` is the fan-club spelling.
  - `dictionary.Dictionaries.load(data_dir) -> Dictionaries`
  - `.match_songs_longest(text) -> list[tuple[int,int,str]]` (start, end, song_id) — longest-match over normalized titles+aliases, non-overlapping.
  - `.performer(name) -> str|None` (canonical), `.match_performers_from_right(text) -> (list[str], rest: str)`
  - `.program(name) -> str|None` canonical fan-club name.
  - `.song(id) -> dict`

- [ ] **Step 1: Write failing tests**

```python
def test_longest_match_prefers_full_title(d):
    assert [m[2] for m in d.match_songs_longest("夜桜お七 千本桜")] == ["yozakura-oshichi","senbonzakura"]
def test_alias_variants(d):
    assert d.match_songs_longest("ほろよい満月")[0][2] == d.match_songs_longest("ほろ酔い満月")[0][2]
    assert d.match_songs_longest("まだ君に恋してる")[0][2] == "mata-kimi-ni-koishiteru"
def test_space_inside_song(d):
    assert [m[2] for m in d.match_songs_longest("SWEET MEMORIES")] == ["sweet-memories"]
def test_performer_units_and_aliases(d):
    assert d.match_performers_from_right("心の糸 演歌5人娘") == (["演歌5人娘"], "心の糸")
def test_program_alias(d):
    assert d.program("人生歌") == "人生、歌がある"; assert d.program("紅白") == "NHK紅白歌合戦"
def test_required_readings(d):
    for sid, y in {"yozakura-oshichi":"よざくらおしち","yuki-shinshin":"ゆきしんしん","iwaizake":"いわいざけ",
                   "amagigoe":"あまぎごえ","meoto-zenzai":"めおとぜんざい","hanagatami":"はながたみ"}.items():
        assert d.song(sid)["yomi"] == y
```

- [ ] **Step 2:** Run → FAIL
- [ ] **Step 3:** Implement `dictionary.py`. Write `scripts/draft_dictionary.py` that extracts candidate song strings from all seed titles (strip `[..]`, trailing date, known performers), groups variants by `jp.normalize` + edit distance ≤ 1, drafts `yomi` with pykakasi, and writes `songs.yaml` with `reviewed: false`. Then hand-edit `songs.yaml`: apply every reading listed in `萬事屋請review.md` "Readings", add the alias groups listed there (ほろ酔い/ほろよい満月, お七→夜桜お七, Laser Beam/レーザービーム, 丸ノ内/丸の内サディスティック, ロンリー・/ロンリーチャップリン, 風に立つ/風に立つ!, 再会酒場(セリフ入り)→再会酒場, まだ→また君に恋してる, ひぱり→ひばりの佐渡情話, 黃色い→黄色いさくらんぼ), remove non-songs (My, SWEET, LIVE, Dancing, Electro, 乙女座, venue names, 新曲紹介), and draft season/theme tags. Mark 雨夜酒 and 恋花 `reviewed: false`. Seed `performers.yaml` from names in the seed (坂本冬美, 藤あや子, 伍代夏子, 大塚宝, 中森明菜, 演歌5人娘(unit), 演歌三人娘(unit), M!LK(unit), アグネス・チャン …) and `programs.yaml` from all `[..]` prefixes mapped to fan-club spellings.
- [ ] **Step 4:** Run tests → PASS
- [ ] **Step 5:** Commit `feat: song/performer/program dictionaries with reviewed readings`

---

### Task 3: Title parser

**Files:**
- Create: `pipeline/title_parser.py`
- Test: `tests/test_title_parser.py`, `tests/test_title_parser_seed.py`

**Interfaces:**
- Consumes: `Dictionaries`
- Produces: `ParsedTitle(program: str|None, songs: list[str], performers: list[str], date: str|None, leftover: str, ok: bool)`; `parse_title(title: str, d: Dictionaries, platform: str = "x") -> ParsedTitle`. `ok=False` when `leftover` contains non-trivial text (anything but spaces/、/w/ /＆) or date missing.

Algorithm: normalize → peel all leading `[..]`/`【..】` groups (first group that maps via `d.program` is the program; others go to tags) → peel trailing `\d{8}` → `match_performers_from_right` (split on ＆, w/, 、, space; handle glued `TATTOO藤あや子` by suffix match against performer names) → `match_songs_longest` on the rest → leftover = rest minus matched spans. `（無曲名）` → `songs=[]`, `ok=True`. Bilibili platform: also strip `cut`, `(含talking)`, convert 彥→彦 before matching.

- [ ] **Step 1: Write failing tests**

```python
CASES = [
 ("[徹子の部屋] 再会酒場(セリフ入り)、また君に恋してる、夜桜お七 坂本冬美 20240116",
   ("徹子の部屋", ["saikai-sakaba","mata-kimi-ni-koishiteru","yozakura-oshichi"], ["坂本冬美"], "2024-01-16", True)),
 ("あばれ太鼓　坂本冬美 w/大塚宝　20230101", (None, ["abare-daiko"], ["坂本冬美","大塚宝"], "2023-01-01", True)),
 ("[紅白歌合戦お正月SP] （無曲名） 坂本冬美＆M!LK 20260103", ("紅白歌合戦お正月SP", [], ["坂本冬美","M!LK"], "2026-01-03", True)),
 ("心の糸 演歌5人娘 20240104", (None, ["kokoro-no-ito"], ["演歌5人娘"], "2024-01-04", True)),
 ("（無曲名） 20250104", (None, [], [], "2025-01-04", True)),
 ("謎の新曲 坂本冬美 20260101", (None, [], ["坂本冬美"], "2026-01-01", False)),   # unknown song → review
]
@pytest.mark.parametrize("title,exp", CASES)
def test_parse(title, exp, d): ...

def test_all_seed_titles_parse_or_flag(d):  # test_title_parser_seed.py
    rows = read_seed_titles("data/seed/x_table.md")
    results = [parse_title(t, d) for t in rows]
    assert len(rows) == 669
    assert all(r.date for r in results)
    assert sum(r.ok for r in results) / len(results) >= 0.95
    assert not any(s in BANNED for r in results for s in r.songs)  # BANNED = {"My","SWEET","LIVE","Dancing","Electro","乙女座"}
```

- [ ] **Step 2:** Run → FAIL
- [ ] **Step 3:** Implement. Iterate on `songs.yaml`/`performers.yaml` (not on parser special-cases) until the seed test passes.
- [ ] **Step 4:** Run → PASS; print the remaining `ok=False` titles for the commit message.
- [ ] **Step 5:** Commit `feat: dictionary-based title parser (≥95% of seed titles)`

---

### Task 4: Seed import and merge

**Files:**
- Create: `pipeline/seed_import.py`, `pipeline/merge.py`, `pipeline/review.py`
- Test: `tests/test_seed_import.py`, `tests/test_merge.py`

**Interfaces:**
- Consumes: `parse_title`, `Clip`, `Source`
- Produces:
  - `seed_import.read_rows(path) -> list[dict]` (columns: mmdd, yyyy, title, x_url, posted_utc, relation, bili_url, note)
  - `seed_import.row_to_clip(row, d) -> Clip` — `date_source="post_time"` when note contains `日期取自發文時間`; then `broadcast_date` = post time converted to Asia/Tokyo date. `has_video=False` when note contains `未偵測到原生影片` → `hidden=True`. `relation in (同一條, 疑似同一條)` adds a bilibili Source to the same clip.
  - `merge.clip_id(c) -> str` = `f"{date}-{first_song or 'talk'}-{hash6(title_raw)}"`
  - `merge.merge(existing: list[Clip], incoming: list[Clip]) -> list[Clip]` — same source id → update; else same date + same non-empty first song + (same program or overlapping performers) → add source; exact same `title_raw` with x posts < 24h apart → keep one clip, both sources. Never merge on empty songs.
  - `review.add(kind: str, ref: str, detail: str)`; `review.save()` → `data/review.json` items `{kind, ref, detail, created}` with kinds `title_unparsed|merge_uncertain|date_post_time|no_video|reading_unreviewed`.
  - CLI: `python -m pipeline.run import-seed` → writes `data/clips.json`, `data/review.json`.

- [ ] **Step 1: Write failing tests**

```python
def test_post_time_late_utc_shifts_to_next_jst_day():
    row = {..., "title": "（無曲名） 20230107", "posted_utc": "2023-01-07 22:32 UTC", "note": "日期取自發文時間"}
    c = row_to_clip(row, d); assert c.broadcast_date == "2023-01-08" and c.date_source == "post_time"
def test_title_date_kept_when_not_post_time(): ...  # 2023-01-01 03:54 UTC, no note → "2023-01-01", "title"
def test_bilibili_same_post_becomes_second_source(): ...  # relation 同一條 → 2 sources
def test_no_video_rows_hidden(): ...
def test_merge_never_on_empty_song():
    a = clip("2026-04-03", songs=[], program="うたコン"); b = clip("2026-04-03", songs=[], program="うたコン")
    assert len(merge([a],[b])) == 2
def test_merge_same_song_needs_program_or_performer(): ...  # same date+song, disjoint performers & different program → 2 clips
def test_duplicate_x_posts_minutes_apart_collapse(): ...  # 雪深深 藤あや子 20260120 ×2 → 1 clip, 2 sources
def test_import_seed_counts(tmp_path):
    clips = import_seed(...); assert 560 <= len(clips) <= 669
    assert sum(c.date_source == "post_time" for c in clips) == 164
```

- [ ] **Step 2:** Run → FAIL
- [ ] **Step 3:** Implement; `run.py` with `import-seed` subcommand.
- [ ] **Step 4:** Run → PASS; run `python -m pipeline.run import-seed`, check `data/clips.json` exists.
- [ ] **Step 5:** Commit `feat: seed import, merge rules, review queue`

---

### Task 5: YouTube and Bilibili sources

**Files:**
- Create: `pipeline/sources/__init__.py`, `pipeline/sources/youtube.py`, `pipeline/sources/bilibili.py`, `pipeline/http.py`
- Test: `tests/test_youtube.py`, `tests/test_bilibili.py`, fixtures `tests/fixtures/yt_feed.xml`, `tests/fixtures/bili_page1.json` (record real responses once)

**Interfaces:**
- Produces:
  - `http.get(url, **kw) -> requests.Response` — shared session, UA from Global Constraints, timeout 20s, 2 retries.
  - `youtube.CHANNEL_ID = "UC6qAQ5HtWW6h-Wl0bmPabag"`; `youtube.parse_feed(xml: str) -> list[RawUpload]`; `youtube.fetch_recent() -> list[RawUpload]`; `youtube.fetch_all(api_key) -> list[RawUpload]` (uploads playlist via Data API `playlistItems`, paged).
  - `bilibili.MID = 6972913`; `bilibili.parse_page(js: dict) -> list[RawUpload]`; `bilibili.fetch_recent(pages=1)`; `bilibili.fetch_all()` (pages until empty, 3s apart). Endpoint `https://api.bilibili.com/x/series/recArchivesByKeywords?mid=6972913&keywords=&ps=50&pn={n}`; raise `SourceError` when `code != 0`.
  - `RawUpload(platform, id, url, title, uploaded_at)` in `sources/__init__.py`; `to_clip(raw, d) -> Clip` (parse with platform-specific rules).
  - CLI: `python -m pipeline.run import-backcatalogue` (needs `YT_API_KEY`).

- [ ] **Step 1:** Tests on fixtures: feed → 15 uploads with first title `あばれ太鼓　坂本冬美 w/大塚宝　20230101`; bilibili page → BV ids and `https://www.bilibili.com/video/<bvid>`; `code=-352` → `SourceError`.
- [ ] **Step 2:** Run → FAIL
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS. Then (needs network + key) run `import-backcatalogue`, confirm clips gained YouTube sources, commit updated `data/clips.json`.
- [ ] **Step 5:** Commit `feat: YouTube and Bilibili ingestion + back-catalogue import`

---

### Task 6: Fan-club scrapers (schedule, TV backnumber, magazine, 冬美便り)

**Files:**
- Create: `pipeline/sources/fanclub.py`
- Test: `tests/test_fanclub.py`, fixtures `tests/fixtures/fc_schedule.html`, `fc_bk_tv_2026.html`, `fc_bk_magazine.html`, `fc_letter_2026_11.html` (saved once; the letters fixture is **trimmed to 3 entries with bodies replaced by placeholder text** before committing)

**Interfaces:**
- Produces:
  - `parse_schedule(html) -> list[Appearance]` (TV/radio only); `parse_bk_tv(html) -> list[Appearance]`; `parse_magazine(html) -> list[FlashIssue]` (only entries containing `FLASH`; guest from title text when present); `parse_letters(html) -> list[tuple[Letter, str]]` — returns body text **in memory only** for linking.
  - `fetch_bk_tv(year)`, `fetch_letters(year, month)`, `fetch_schedule()`, `fetch_magazine()`; check `https://fuyumi-fc.com/robots.txt` once per run and abort fan-club fetches if disallowed.
  - Date parsing handles `2026/11/24（火）`, `2027/1/15（金）`, ranges `2026/04/07（火）～04/10（金）` (→ one Appearance per day), full-width colons in times; `note` ∈ `再放送|VTR|生放送|VTR出演|電話出演|""`.
  - CLI `import-fanclub-history` fetches bk_tv 2006–current and letters 2004–current, max 40 requests per run (resumable via `status.json` cursor) so the history arrives over several days.

- [ ] **Step 1:** Tests: schedule fixture includes `2026/12/31` NHK総合「第77回ＮＨＫ紅白歌合戦」 19:20; bk_tv range entry expands to 4 days; `※再放送` note parsed; letter `2026/11/19` title `モゴモゴ対談(^^)` URL under `/wp/letter/2026/11/19/`; `Letter` objects have no body attribute.
- [ ] **Step 2:** Run → FAIL
- [ ] **Step 3:** Implement with BeautifulSoup.
- [ ] **Step 4:** Run → PASS
- [ ] **Step 5:** Commit `feat: fan club schedule, backnumber, magazine and letters scrapers`

---

### Task 7: Fact-check, letter linking, FLASH, picker

**Files:**
- Create: `pipeline/factcheck.py`, `pipeline/linking.py`, `pipeline/picker.py`, `data/special_days.yaml`
- Test: `tests/test_factcheck.py`, `tests/test_linking.py`, `tests/test_picker.py`

**Interfaces:**
- Consumes: `Clip`, `Appearance`, `Letter`, `FlashIssue`, `Dictionaries`
- Produces:
  - `factcheck.verify(clips, appearances, d) -> None` sets `clip.verified = {broadcaster, program, note}` only when `date_source=="title"` and an appearance on the same date has `d.program(clip.program) == appearance.program` (alias-normalised substring match allowed).
  - `linking.mentions(body: str, d) -> dict(songs=[ids], programs=[names], people=[names])`; `linking.flash_from_letters(letters) -> list[FlashIssue]` (title or body contains モゴモゴ対談).
  - `special_days.yaml`: list of `{rule: "MM-DD" | "mothers_day" | "respect_aged_day" | "chushu", title, reason, songs: [ids], tone: festive|gentle|memorial}`. Seed: 03-04 デビュー記念日 (あばれ太鼓), 03-30 お誕生日, 12-31 紅白・年忘れ, 01-01 お正月 (祝い酒; 能登はいらんかいね tone gentle), 11-08 島倉千代子さんを偲んで (人生いろいろ, memorial), 06-10 猪俣公章さんを偲んで, 12-30 八代亜紀さんを偲んで, 08-22 夜桜お七 発売記念日, 01-14 また君に恋してる 発売記念日, 02-06 お燈まつり (男の火祭り), mothers_day (岸壁の母, おかあさん), respect_aged_day (祝い酒), chushu (ほろ酔い満月). Memorial titles always `○○さんを偲んで`.
  - `picker.pick(date: str, clips, appearances, letters, overrides: dict[str, list[str]], history: list[Pick], d) -> Pick` — rules in order (spec §7): override → special day → TV today (non-再放送/VTR) same program → letter mention in last 3 days → season (month→season: 3–5 春, 6–8 夏, 9–11 秋, 12–2 冬) → 珍しい映像 (year ≤ 2005 or not picked in 90 days) → any. Only clips with alive YouTube source; not picked in last 30 days; 3–5 clips; deterministic per date (seeded RNG with date string). Reason strings: `冬美さんが便りで触れた曲`, `今夜の放送の前に`, `珍しい映像`, etc.
  - Movable dates: 母の日 = 2nd Sunday of May, 敬老の日 = 3rd Monday of Sep, 中秋 = table for 2026–2035 in code.

- [ ] **Step 1: Write failing tests**

```python
def test_verify_requires_program_match(): ...  # same date, different program → None
def test_verify_never_on_post_time_dates(): ...
def test_alias_program_matches(): ...  # [人生歌] vs BS朝日「人生、歌がある」 → verified
def test_pick_override_wins(): ...
def test_pick_birthday(): assert pick("2027-03-30", ...).theme_title.startswith("お誕生日")
def test_pick_memorial_wording(): assert "偲んで" in pick("2027-11-08", ...).theme_title
def test_pick_tv_today_uses_same_program(): ...
def test_pick_skips_vtr_appearance(): ...
def test_pick_only_youtube_and_no_repeat_30_days(): ...
def test_pick_deterministic(): assert pick(d1,...) == pick(d1,...)
def test_pick_falls_back_when_theme_has_too_few(): ...  # → still 3 clips
def test_mothers_day_2027(): assert movable("mothers_day", 2027) == "2027-05-09"
```

- [ ] **Step 2:** Run → FAIL
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS
- [ ] **Step 5:** Commit `feat: fact-check, letter/FLASH linking, daily picker`

---

### Task 8: Sheet input and X embed data

**Files:**
- Create: `pipeline/sources/sheet.py`, `pipeline/sources/xembed.py`, `docs/sheet-template.md`
- Test: `tests/test_sheet.py`, `tests/test_xembed.py`

**Interfaces:**
- Produces:
  - Sheet tabs, published as CSV (URLs in secrets). Headers exact: 追加 = `リンク,メモ`; おすすめ = `日付,テーマ,リンク1,リンク2,リンク3,リンク4,リンク5`; 確認 = `種類,対象,内容,答え` (pipeline writes questions into `data/review.json`; owner copies via a provided Apps Script — see Task 13 docs — and answers in `答え`).
  - `sheet.read_csv(url, expected_headers) -> list[dict]` raises `SheetError` if headers differ.
  - `sheet.links_to_sources(rows) -> list[tuple[platform, id, url]]` — accepts x.com / twitter.com / youtu.be / youtube.com / bilibili.com URLs, strips query strings.
  - `sheet.overrides(rows, clips) -> dict[date, list[clip_id]]`.
  - `sheet.apply_answers(rows, clips, d)` — `種類=title_unparsed` answer `曲名; 出演者; YYYYMMDD` updates clip; `no_video` answer `表示` unhides; `reading_unreviewed` answer = reading updates `songs.yaml`.
  - `xembed.fetch(tweet_id) -> RawUpload|None` via `https://cdn.syndication.twimg.com/tweet-result?id={id}&token=a`; returns None on any failure (never raises).

- [ ] **Step 1:** Tests: wrong headers → `SheetError`; `https://x.com/jounotakeuchi/status/2006396667155919096?s=20` → `("x","2006396667155919096", "https://x.com/jounotakeuchi/status/2006396667155919096")`; xembed fixture → title starts with `[紅白] 夜桜お七`; xembed HTTP 404 → None.
- [ ] **Step 2:** Run → FAIL
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS
- [ ] **Step 5:** Commit `feat: Google Sheet input and X post lookup`

---

### Task 9: Daily/weekly orchestration with safety checks

**Files:**
- Create: `pipeline/run.py` (extend), `pipeline/liveness.py`, `pipeline/status.py`
- Test: `tests/test_run.py`, `tests/test_liveness.py`

**Interfaces:**
- Consumes: everything above
- Produces:
  - `run.daily(today: str|None=None)` — steps: sheet answers → sheet 追加 → youtube.fetch_recent → bilibili.fetch_recent → fanclub (schedule, bk_tv current year, magazine, letters current month) → merge → factcheck → linking → picker for today and tomorrow → `build.build_all()`. Each source step wrapped by `status.guard(name, fn, previous_count)`.
  - `status.guard(name, fn, previous_count) -> result|None` — on exception, or `previous_count >= 5 and new_count < 0.8 * previous_count`, returns None (caller keeps last-good) and records `{name: {last_ok, last_error, consecutive_failures}}` in `data/status.json`.
  - `status.needs_alert() -> list[str]` sources with `consecutive_failures >= 3`.
  - `liveness.check(clips) -> None` — YouTube `https://www.youtube.com/oembed?url=...&format=json` (404/401 → alive=False); Bilibili `https://api.bilibili.com/x/web-interface/view?bvid=` (`code != 0` → alive=False); X via xembed (None → alive=False). Clips with no alive source → `hidden=True`. Max 300 checks per run, oldest-checked first.
  - `run.weekly()` = `liveness.check` + `build.build_all()`.

- [ ] **Step 1:** Tests (monkeypatched sources): bilibili raises → clips from bilibili unchanged, `status.json` failure count 1; fan-club bk_tv returns 3 rows when previous was 120 → rejected; three consecutive failures → `needs_alert()` contains source; liveness 404 on only source → clip hidden; youtube dead but bilibili alive → `best_source()` is bilibili.
- [ ] **Step 2:** Run → FAIL
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS
- [ ] **Step 5:** Commit `feat: daily/weekly runs with last-good fallback and liveness check`

---

### Task 10: Static data and clip-page build

**Files:**
- Create: `pipeline/build.py`, `pipeline/templates/clip.html`
- Test: `tests/test_build.py`

**Interfaces:**
- Produces files under `site/data/`:
  - `today.json` (< 20 KB): `{date, date_label, appearances:[{time_label, broadcaster, program, note, state: before|aired|clip, clip_id?}], pick:{theme_title, reason, clips:[ClipCard]}, on_this_day:{exact: bool, years:[{year, year_label, clips:[ClipCard]}]}, letters:[{date_label,title,url,clips:[ClipCard]}], flash:{issue_label, guest, letter_url, clips:[ClipCard]}|null, new:[ClipCard×6]}`
  - `ClipCard = {id, title_label (「…」「…」 or トーク・その他), date_label (with 和暦), program, performers_label (joined 、), platform, thumb, verified: bool, url: "/v/<id>/"}`
  - `days/MM-DD.json` — `{label, years:[{year, year_label, clips, letters, flash}]}`; `calendar.json` — `{ "MM-DD": {videos:n, letters:n, flash:n} }`.
  - `songs.json` — `[{id, title, yomi, gyo, count}]` sorted by `jp.sort_key`; `songs/<id>.json` — clips + letter mentions.
  - `site/v/<id>/index.html` from template: OGP (`og:title` = `「曲」坂本冬美 2025年12月31日`, `og:image` = thumbnail, `og:url`, `twitter:card=summary_large_image`), robots noindex, loads `/assets/player.js` with clip JSON inline.
  - TV card `state`: `before` if now < start time, `aired` after start with no matching clip, `clip` when a clip with same date+program exists; VTR/再放送 never `aired`, they show note label.
  - あの年の今日: exact MM-DD across years newest first; if empty, ±3 days with `exact:false`.
  - Hidden clips excluded everywhere.
  - `review.json` — items from `data/review.json` reduced to `{種類, 対象, 内容}` (for the Sheet's 確認 tab).
- Base URL from env `SITE_URL` (default `https://fuyumi.pages.dev`).

- [ ] **Step 1:** Tests on a small fixture dataset: `today.json` < 20 000 bytes for full seed data; on_this_day for 12-31 lists 2025 first; empty day → `exact:false`; songs sorted (`あばれ太鼓` before `いわいざけ`… by yomi); clip page contains `noindex`, `og:title` with 「」, and `/v/<id>/`; post-time clip card `verified=false`; performers label uses `、`.
- [ ] **Step 2:** Run → FAIL
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS; `python -m pipeline.run daily --offline` builds `site/data` from committed data.
- [ ] **Step 5:** Commit `feat: static JSON and per-clip share pages`

---

### Task 11: Front end — home, player, share, LINE handling

**Files:**
- Create: `site/index.html`, `site/usage.html`, `site/robots.txt`, `site/manifest.webmanifest`, `site/icon-512.png` (neutral 〜 wave/mic glyph on crimson, no photo), `site/assets/app.css`, `site/assets/common.js`, `site/assets/home.js`, `site/assets/player.js`, `site/assets/share.js`
- Test: `tests/ui/test_home.py` (Playwright, iPhone 13 + Pixel 7 emulation, served via `python -m http.server`)

**Interfaces:**
- Consumes: `site/data/today.json`, clip page inline JSON
- Produces:
  - `common.js`: `isLine()`, `showLineBanner()` (text 「Safari（Chrome）で開くと、ホーム画面に置けて見やすくなります」 + button that reloads with `?openExternalBrowser=1`), `backButton()` (「← 戻る」 on every page, uses history or goes to `/`), footer 「非公式ファンサイト ・ 削除のご依頼はこちら」 (mailto from `site/config.js`).
  - `player.js`: `mountYouTubeQueue(el, videoIds)` — loads IFrame API and creates player for first id on page load (no autoplay); big ▶ 「4曲つづけて聴く」 calls `player.playVideo()` synchronously in the click handler; `onStateChange ENDED` → next; shows 「次の曲へ」 and current 「曲名」. `mountBilibili(el, bvid)` with `player.bilibili.com/player.html?bvid=…&danmaku=0&high_quality=1&autoplay=0`. `mountX(el, url)` — X `blockquote` + widgets.js; if no iframe after 4000ms → card with 「Xで見る」 linking via `/go.html?to=`.
  - `go.html` interstitial: 「Xのページへ移動します」 + big 「移動する」 + 「← 戻る」; same tab.
  - `share.js`: `shareButtons(el, {url, title})` — 「共有する」 uses `navigator.share` when available (hidden otherwise); 「LINEで送る」 → `https://line.me/R/share?text=` + encoded `title + "\n" + url + "?openExternalBrowser=1"`; 「Xでポスト」 → `https://x.com/intent/post?text=…&url=…`; 「リンクをコピー」 → clipboard + toast 「コピーしました」.
  - Home renders sections from `today.json` in spec order, each only if non-empty, plus big buttons 「カレンダー」「曲名でさがす」「使い方」.

- [ ] **Step 1: Write failing Playwright tests**

```python
def test_home_sections_and_labels(page): ...      # 今日のおすすめ, 4曲つづけて聴く, あの年の今日 visible
def test_play_button_starts_inside_tap(page): ... # stub YT API; click → playVideo called synchronously
def test_tap_targets_at_least_56px(page): ...     # all buttons/links in main ≥ 56px tall
def test_200_percent_text_no_horizontal_scroll(page): ...  # set html font-size 250% → scrollWidth <= innerWidth
def test_line_banner(page_with_line_ua): ...      # UA contains "Line/" → banner visible
def test_share_line_url(page): ...                # LINE button href contains openExternalBrowser%3D1
def test_x_fallback_after_timeout(page): ...      # block platform.twitter.com → 「Xで見る」 appears
def test_noindex_everywhere(page): ...
```

- [ ] **Step 2:** Run `pytest tests/ui -v` → FAIL
- [ ] **Step 3:** Implement. Style: system Japanese font stack + Noto Sans JP; one column, max-width 720px; cards with 16px radius; generous whitespace; dark mode via `prefers-color-scheme`.
- [ ] **Step 4:** Run → PASS. Take screenshots (deviceScaleFactor 2) of home on iPhone and Android for the owner.
- [ ] **Step 5:** Commit `feat: home page, players, sharing, LINE handling`

---

### Task 12: Front end — calendar, song index, song page, clip page polish

**Files:**
- Create: `site/calendar.html`, `site/songs.html`, `site/song.html`, `site/assets/calendar.js`, `site/assets/songs.js`
- Test: `tests/ui/test_calendar.py`, `tests/ui/test_songs.py`

**Interfaces:**
- Consumes: `calendar.json`, `days/MM-DD.json`, `songs.json`, `songs/<id>.json`, `share.js`, `player.js`
- Produces:
  - Calendar default = **list view** of the current month showing only days with content, e.g. 「12月31日（映像5本・冬美便り1件）」; toggle 「カレンダー表示」 shows grid (cells ≥ 56px, one dot + text count, no emoji-only meaning). 「前の月」「次の月」「今日」 buttons. Tapping a day loads `days/MM-DD.json` below and scrolls to it: grouped by `year_label` (e.g. 「2025年（令和7年）」) newest first, each with clips (▶ cards), 冬美便り titles (link via go.html 「ファンクラブのページへ」), FLASH.
  - Songs: 行 buttons あ か さ た な は ま や ら わ 英数字; list rows 「夜桜お七」 + small よざくらおしち + 「12本」; song page lists clips newest first, related 冬美便り.
  - Clip page (`/v/<id>/`): player, 「曲」, date with 和暦, program, performers, ✓ 放送日確認済み (if verified), share buttons, 「この曲の他の映像」, 「この頃の冬美便り」 (±7 days).

- [ ] **Step 1:** Playwright tests: calendar list shows 12月31日 entry for December; tapping it shows 2025年（令和7年） before 2024年; grid toggle cells ≥ 56px; songs page あ-section contains 「あばれ太鼓」 before 「いわいざけ」-row; や button scrolls to 「夜桜お七」; clip page shows share buttons and ✓ only for verified fixture clip.
- [ ] **Step 2:** Run → FAIL
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS
- [ ] **Step 5:** Commit `feat: calendar, song index, clip pages`

---

### Task 13: Deployment, workflows, owner setup guide

**Files:**
- Create: `.github/workflows/daily.yml`, `.github/workflows/weekly.yml`, `.github/workflows/test.yml`, `docs/setup.md` (Japanese), `docs/sheet-apps-script.gs`, `site/config.js`
- Test: `tests/test_workflows.py`

**Interfaces:**
- `daily.yml`: `schedule: cron "0 20 * * *"` (05:00 JST) + `workflow_dispatch`; `TZ=Asia/Tokyo`; steps: checkout → setup-python 3.12 → `pip install .` → `pytest -q` (unit only) → `python -m pipeline.run daily` → commit `data/` and `site/` **only if `git diff --quiet` fails** → `cloudflare/wrangler-action@v3` `pages deploy site --project-name=fuyumi` → if `status.needs_alert()` non-empty, open/update a GitHub issue titled 「データ取得エラー」.
- `weekly.yml`: Sunday `0 21 * * 6` → `python -m pipeline.run weekly` → same commit/deploy.
- `test.yml`: on push → pytest incl. UI tests.
- `docs/sheet-apps-script.gs`: daily time-triggered Apps Script that fetches `SITE_URL/data/review.json` and appends rows not yet in the 確認 tab. (`build.py` writes `site/data/review.json` with only `{種類,対象,内容}` because the repo is private; add this to Task 10's outputs.)
- `docs/setup.md` (Japanese, step by step with screenshots placeholders): GitHub account + private repo; Cloudflare account + Pages project `fuyumi` + API token; Google Sheet from template, publish each tab as CSV, put URLs in GitHub secrets; install Apps Script; YouTube API key for one-time import; how to paste X links (共有 → リンクをコピー → 追加 tab); how to set おすすめ; how to answer 確認.

- [ ] **Step 1:** `tests/test_workflows.py`: parse YAML; daily cron is `0 20 * * *`; env TZ is `Asia/Tokyo`; deploy step present; commit step guarded by diff check; `site/robots.txt` disallows all.
- [ ] **Step 2:** Run → FAIL
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run full suite `pytest -v` → PASS. Run `python -m pipeline.run daily` locally with network → site builds; serve `site/` and spot-check on iPhone emulation.
- [ ] **Step 5:** Commit `chore: GitHub Actions, Cloudflare deploy, owner setup guide`

---

## Self-review notes

- Spec coverage: data sources §4 → Tasks 5, 6, 8; model §5 → 1, 4; automation §6 → 9, 13; picker §7 → 7; pages §8 → 10–12; review fixes §13 → LINE (11), date_source (4), parser (2–3), YouTube-only playlist (7, 11), link-only (11, 13), liveness (9), letters storage (6), Sheet-only owner (8, 13), calendar list (12), same-tab links (11), wording (Global Constraints), Actions mechanics (13); §14 sharing/OGP → 10, 11.
- Fixed during self-review: the 確認 tab needs a path from the private repo to the Sheet — resolved by publishing a field-limited `site/data/review.json` that the Apps Script reads.
