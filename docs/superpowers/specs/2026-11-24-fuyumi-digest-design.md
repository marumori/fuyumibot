# 今日の冬美 — Daily digest site for 坂本冬美 fans (design)

Date: 2026-11-24
Status: revised after 萬事屋 review (see `/萬事屋請review.md`), pending owner approval

## 1. Intent and why

The owner uploads TV clips of 坂本冬美 (and related singers: 藤あや子, 伍代夏子, 演歌5人娘, etc.) to X (@jounotakeuchi), Bilibili (space 6972913) and YouTube (@fuyumibot, channel `UC6qAQ5HtWW6h-Wl0bmPabag`). Fans — Japanese, aged roughly 50–80, almost all on iPhone/Android — currently have to dig through three platforms, two of which (Bilibili's Chinese UI, X's login walls) are hostile to them.

The site is **one place, one page a day**: open it, press one big ▶, listen. Everything else about Fuyumi that day (her TV appearances, her own 冬美便り posts, FLASH 対談) is gathered around the videos, like a daily newspaper digest.

Success = an elderly fan can open the site from a home-screen icon and be listening within one tap, without ever needing to understand X, Bilibili or YouTube.

## 2. Goals, non-goals, anti-goals

Goals
- Daily home page 「今日の冬美」: today's TV appearances, 今日のおすすめ playlist, あの年の今日, latest 冬美便り / FLASH 対談, new uploads.
- Calendar (カレンダー) to browse any day's 当年今日: videos, 冬美便り and FLASH 対談 from that month-day across all years.
- Song index in 五十音順, and per-song pages.
- Automatic updates from YouTube and Bilibili daily; X posts added by the owner pasting links into the sheet (owner decision: **free only**, no paid X API).
- **Running cost ¥0** (owner decision).
- **Use only what is already uploaded** on the three platforms; no re-uploading is asked of the owner (owner decision).
- Fact-check each clip against the fan club TV/radio record (date + program) and show a ✓ badge.
- Free hosting (private GitHub repo + Cloudflare Pages), link-only (not indexed by search engines); maintained by GitHub Actions.

Non-goals
- Hosting video files ourselves (we embed / link the platform players only).
- User accounts, comments, likes, personal history, search-history personalisation.
- Reading fans' Google/Yahoo searches or Spotify/Amazon Music data.
- English or Chinese UI.

Anti-goals (would be a failure even if it "works")
- Small text, icon-only buttons, hidden gestures (swipe-only, long-press), hamburger menus as the only navigation.
- Autoplay with sound on page load, pop-ups, cookie banners, ads.
- Landing the fan on a Bilibili/X page with no way back, or without warning that they are leaving.
- Showing raw data noise: duplicates, Chinese notes (「X獨有」「日期取自發文時間」), BV ids, UTC times.
- Anything that implies an official relationship with 坂本冬美 or the fan club (this is a fan site; it links to, never copies, fan-club content).

## 3. Users and accessibility rules

- All UI text Japanese. Dates as `2025年12月31日（水）`; times as `19時30分` / `19:30`; era names (和暦) not used except optionally in a small secondary label (builder's call: off by default).
- Base font ≥ 20px (CSS px), headings 26–32px; line-height ≥ 1.7; Japanese font stack (`"Hiragino Sans", "Noto Sans JP", sans-serif`), Noto Sans JP via Google Fonts as fallback.
- Tap targets ≥ 56px tall, full-width primary buttons, text labels on every button (「再生する」「次の曲へ」「戻る」).
- High contrast (WCAG AA minimum, AAA for body text). Light theme by default; dark mode follows the phone setting.
- Single-column layout on phones, max-width ~720px centred on larger screens.
- No autoplay; one tap on 「まとめて再生」 starts the playlist (which is also what mobile browsers require).
- Every external link labelled with its destination and opens in a new tab: 「ファンクラブのページを開く ↗」「Xで見る ↗」.
- "Add to home screen" supported (web app manifest + icon) with a short Japanese how-to on the 使い方 page.
- Style: modern, minimal, calm — lots of whitespace, one accent colour (suggested: deep 紅 / crimson, evoking 演歌 and 紅白), thumbnails with rounded corners, no decorative clutter.

### Japanese ordering rules (並べ方)
- Song index: 五十音順 by reading (よみ). Kanji titles need a stored reading (`yomi`), since sorting by code point is wrong. Readings are generated automatically (e.g. pykakasi/SudachiPy) and can be corrected by the owner in `data/overrides/songs.yaml`. Sections headed あ行・か行・さ行…, with large index buttons for jumping.
- Long vowels, small kana, dakuten sort as in standard 五十音 (ignore dakuten at first pass, as dictionaries do).
- Lists by date: あの年の今日 newest year first; 新着 newest upload first; calendar day view grouped by year, newest first.
- Names in credits joined with 「、」 (not 「・」, which occurs inside names like アグネス・チャン); unit names count as one performer.
- Year labels show 和暦 too: 「1994年（平成6年）」 (not on today's date).

## 4. Data sources

| Source | What we get | How |
|---|---|---|
| Existing list `data/seed/x_table.md` (669 rows) | X links, some Bilibili links, titles, broadcast dates | One-time import |
| YouTube @fuyumibot | New uploads | Public RSS feed `feeds/videos.xml?channel_id=UC6qAQ5HtWW6h-Wl0bmPabag` daily (latest 15). Full back-catalogue imported once (yt-dlp flat listing or YouTube Data API key). |
| Bilibili space 6972913 | New uploads + back-catalogue | Public endpoint `api.bilibili.com/x/series/recArchivesByKeywords?mid=6972913` (works without login; tested). Back-catalogue paged once at import. |
| X @jounotakeuchi | New posts | Owner pastes the post link into the sheet; post text/date read by id from X's public embed data (free, unofficial — may stop working; existing data is kept if so). No X API. |
| Manual sheet (Google Sheet, "追加シート") | X links the bot missed; owner's おすすめ overrides | Daily read of the published-as-CSV sheet |
| Fan club TV/radio backnumber `fuyumi-fc.com/schedule/bk_tv.php?y=YYYY` (2006–2026) | Date, broadcaster, program, 再放送/VTR/生放送 notes | Scraped once for all years, then current year daily |
| Fan club upcoming schedule `fuyumi-fc.com/schedule/index.php` | Upcoming TV/radio, concerts | Daily |
| Fan club magazine backnumber `bk_magazine.php` | FLASH issue dates for モゴモゴ対談 | Daily |
| 冬美便り `fuyumi-fc.com/letter/index.php?y=YYYY&m=MM` (2004–) | Her posts: date, title, body text, permalink | Back-catalogue once, current month daily |

Fan-club content is **linked, never republished**: we store date, title, permalink and a short excerpt (≤ ~40 characters) for matching and display; the full text stays on the fan club site. Scraping is polite: once a day, one request per page, identifying User-Agent, cache everything.

FLASH モゴモゴ対談 is print-only as far as we know. Entries are built from (a) the magazine schedule and (b) 冬美便り posts mentioning 「モゴモゴ対談」; each shows issue date, guest name, 「火曜発売」 and links to her post. If an online version is found later, add its link.

## 5. Data model (JSON files in the repo, the site reads them)

`clip` — one performance/segment, possibly on several platforms
- `id`, `broadcast_date` (YYYY-MM-DD; may be partial for very old clips), `program` (e.g. 紅白), `songs[]` (song ids, in order; empty = 「曲名なし」), `performers[]`, `title_raw` (original upload title)
- `sources[]`: `{platform: youtube|bilibili|x, url, id, uploaded_at, has_video}` — playback preference **YouTube > Bilibili > X**
- `verified`: fan-club match `{broadcaster, program, note}` or `null`
- `tags[]`: season / theme tags inherited from songs plus clip-level ones (`珍しい映像` auto for broadcast year ≤ 2005)
- `hidden`: owner can hide rows (e.g. posts with no video)

`song` — `id`, `title`, `yomi`, `original_artist`, `season[]` (春夏秋冬), `themes[]` (酒・祝・故郷・恋・母 …)

`letter` — 冬美便り: `date`, `title`, `url`, `excerpt`, `mentions: {songs[], programs[], people[]}`

`appearance` — fan-club TV/radio row: `date`, `time`, `broadcaster`, `program`, `kind` (TV/radio), `note` (再放送/VTR/生放送/電話出演)

`flash` — `issue_date`, `guest`, `letter_url`

`pick` — daily おすすめ result: `date`, `theme_title`, `reason`, `clip_ids[3–5]`

### Parsing upload titles
Owner's convention: `[番組名] 曲名、曲名 出演者＆出演者 w/ゲスト YYYYMMDD`, full-width spaces common, `（無曲名）` when no song. Parser splits: optional `[program]`, songs (split on 、), performers (split on ＆, w/), trailing 8-digit date. Unparseable titles go to a review list rather than being guessed.

### De-duplication / cross-platform merge
Same `broadcast_date` + same first song (via alias table) + matching program or performers → same clip, sources merged. Never merge on an empty song list. The seed list's 同一條 / 疑似同一條 columns are used as hints. Exact-duplicate X posts (same title, minutes apart) collapse into one clip with the later post kept as an alternate source. Uncertain merges go to the review list.

## 6. Automation (GitHub Actions)

**Daily job (~05:00 JST):**
1. Fetch YouTube RSS, Bilibili uploads, manual sheet → parse → merge into clips.
2. Fetch fan-club upcoming schedule, current-year backnumber, magazine backnumber, current-month 冬美便り.
3. Fact-check: for each clip, match `broadcast_date` to an `appearance` on the same date; if one exists, also match program name (fuzzy on the `[番組名]` part) → `verified`. ✓ is shown only when date **and** program both match (program alias table), and never when the date came from the post time.
4. Link letters: find song titles, program names, performer names mentioned in each 冬美便り post → `mentions`.
5. Compute today's おすすめ (section 7) and pre-compute tomorrow's.
6. Build static JSON, commit, Pages redeploys.

**X posts (free):** no automatic discovery. After a live (non-再放送/VTR) appearance, the TV card waits for a matching clip from any source; X clips arrive when the owner pastes the link. If nothing arrives within 2 days the card quietly drops to the calendar.

**Failure behaviour:** any source failing leaves its previous data untouched; the site always builds from last-good data. A small `status.json` and a GitHub issue (opened by the workflow) notify the owner after 3 consecutive failures of the same source.

**Owner's only regular task:** paste each new X link into the sheet (about 10 seconds per post), and optionally set おすすめ overrides. YouTube and Bilibili need nothing.

## 7. 今日のおすすめ (daily playlist) rules

A playlist of 3–5 clips with a Japanese theme title and a one-line reason. Rules evaluated in order; first that yields ≥ 3 clips wins:

1. **Owner override** for the date in the sheet.
2. **Special days:** 3月4日 デビュー記念日 (1987, あばれ太鼓), 3月30日 誕生日, 12月31日 紅白・年忘れ, 1月1日 お正月 (祝い酒 etc.), the 40周年 concert days from the schedule, anniversaries of collaborators' passings when she writes about them (e.g. 島倉千代子 命日 11月8日 → 人生いろいろ) — the special-day table lives in `data/overrides/special_days.yaml`, owner-editable.
3. **She is on TV today** (non-再放送 appearance): 「今夜の放送の前に」— earlier clips from the same program.
4. **She mentioned a song in 冬美便り in the last 3 days:** 「冬美さんが便りで触れた曲」.
5. **Season:** songs tagged with the current season / month (spring 桜 songs in late March–April, 雪 songs Jan–Feb, お祭り songs Jul–Aug…).
6. **Rare:** clips from ≤ 2005 or not featured in the last 90 days: 「珍しい映像」.

Constraints: no clip repeated within 30 days; playlists use only clips with a YouTube or Bilibili source (X embeds need login on many phones and cannot auto-advance); X-only clips appear in あの年の今日, calendar and song pages with a large 「Xで見る ↗」 button; skip `hidden` and no-video clips; deterministic per date (same pick for every visitor that day).

Song season/theme tags: the builder drafts them for all songs in the list; the owner reviews once.

## 8. Pages

### 8.1 Home 「今日の冬美」
```
┌────────────────────────┐
│ 今日の冬美             │
│ 11月24日（火）         │
├────────────────────────┤
│ 📺 今日の出演          │   ← only if an appearance today
│ 19時 BS朝日            │
│ 「人生、歌がある」     │
├────────────────────────┤
│ 今日のおすすめ（4曲）  │
│ 「冬の夜に」           │
│ [ thumbnail        ]   │
│ [  ▶ まとめて再生   ]  │
│ 💌 冬美便りで触れた曲  │   ← reason line
├────────────────────────┤
│ あの年の今日           │
│ 2023年 心の糸  ▶       │
│ 2014年 ○○○    ▶       │
├────────────────────────┤
│ 冬美便り（最新）       │
│ 11/23 クリスマスツリー │
│   └ 関連映像 ▶         │
│ 📖 FLASH 対談 発売中   │
│   └ 対談相手との共演 ▶ │
├────────────────────────┤
│ 新着動画               │
├────────────────────────┤
│ [カレンダー] [曲名から]│   ← big buttons
└────────────────────────┘
```
Sections appear only when they have content. 「あの年の今日」 falls back to ±3 days (labelled 「この頃の映像」) if the exact day is empty.

**TV card states:** before air 「今夜19時 …に出演」 → after air 「放送されました。動画は準備中です」 → clip found 「▶ 放送の映像」 + ✓ 放送確認済み. VTR/再放送 shown with that label and no "準備中" state.

### 8.2 Player
- YouTube clips: IFrame Player API, playlist auto-advances.
- Bilibili: official embed player (`player.bilibili.com`), muted-autostart off; end-of-video can't be detected reliably → large 「次の曲へ ▶」 button.
- X: X embed; large 「Xで見る ↗」 fallback if the embed fails.
- Under the player: song title (large), 放送日, 番組, 出演者, ✓ badge, 「この曲の他の映像」, 「この頃の冬美便り」 (posts within ±7 days of broadcast).

### 8.3 Calendar 「カレンダー」
Month grid, large cells (7 columns fit phone width at ≥ 44px; day numbers 20px). Each day shows small marks: ▶ (videos exist on that month-day in any year), 💌 (冬美便り), 📖 (FLASH). Big 「前の月」「次の月」 buttons, 「今日」 button. Tapping a day opens the **day view**: grouped by year, newest first — for each year the videos (▶), 冬美便り posts (title + link ↗) and FLASH issue that day. Below the grid, an accessible plain list version of the month for users who find grids hard.

```
┌────────────────────────┐
│  ◀前の月  12月  次の月▶│
│ 日 月 火 水 木 金 土   │
│        1  2  3  4  5   │
│        ▶  💌    ▶     │
│ …                      │
│ 31▶💌                  │
├────────────────────────┤
│ 12月31日の冬美         │
│ ■ 2025年               │
│  紅白 夜桜お七    ▶    │
│  第58回年忘れ 祝い酒 ▶ │
│  💌 冬美便り「…」 ↗    │
│ ■ 2024年 …             │
└────────────────────────┘
```

### 8.4 Song index 「曲名から探す」
五十音 section buttons (あ か さ た な は ま や ら わ) then list: title, reading in small kana, number of clips. Song page: all clips newest first, related 冬美便り mentions.

### 8.5 使い方 (how to use) and about
Large-type guide: how to play, how to add to home screen (iPhone Safari / Android Chrome, with screenshots), note that this is a fan-made site and links to the official fan club.

## 9. Approaches considered

1. **Static site on GitHub Pages + GitHub Actions jobs (chosen).** Free, no server to maintain, history of every data change in git, owner already asked about GitHub. Data refresh is daily/hourly, which is enough for this use.
2. Hosted app with a database (e.g. Vercel/Supabase). Real-time updates and an admin UI, but ongoing cost/maintenance and more to break; nothing here needs real time.
3. No-code (Notion / Google Sites + Sheet). Easy for the owner to edit but cannot meet the accessibility, calendar, playlist and automatic-matching requirements.

X ingestion: considered (a) paste-only, (b) targeted checks via the paid X API driven by the fan-club schedule, (c) continuous paid polling. Owner chose **(a) paste-only** to keep running cost at ¥0. Unofficial X timeline scraping was tested and refused (rate-limited) — not used.

## 10. Decided by the owner
- Audience and Japanese-only UI; mobile first; modern minimal look.
- Home = 今日のおすすめ playlist + あの年の今日, digest of everything in one place.
- おすすめ: special days, season, rare, linked to TV, 冬美便り and FLASH; may be a playlist.
- TV card turns into the owner's video after broadcast.
- 冬美便り and FLASH linked to related videos (by song, program, guest).
- Free only: no paid X API; X links via the paste sheet.
- Use existing uploads on all three platforms; no re-uploads.
- Calendar for 当年今日 across videos, 冬美便り, FLASH.
- Hosted on GitHub (Pages + Actions).

## 11. Builder's calls (owner may correct)
- Tech: plain HTML/CSS/vanilla JS front end (no framework, fast on old phones); Python 3 scripts for data jobs; hosting on Cloudflare Pages from a private GitHub repo; data split into small JSON files (`today.json` < 20KB).
- Playback preference YouTube > Bilibili > X.
- Google Sheet as the manual input.
- Accent colour, exact typography, icon.
- Site name 「今日の冬美」 (placeholder).
- Seed-list cleanup rules (hide rows marked no-video only after owner review).

## 12. Open items for setup (not design questions)
- Owner creates the Google Sheet (template provided) and publishes it as CSV.
- GitHub account (private repo) and Cloudflare account (free); custom domain optional.
- Free YouTube Data API key for the one-time back-catalogue import.

## 13. Changes adopted from the 萬事屋 review

`/萬事屋請review.md` is part of this design. Where it conflicts with sections 1–12, the review wins. In short:
- LINE in-app browser handling (`?openExternalBrowser=1` + banner).
- `date_source` field; post-time dates converted to JST, never ✓, sent to review.
- Dictionary/alias-based title parser (not space-splitting), separate Bilibili parser, test over all 669 seed rows.
- Playlists YouTube-only; Bilibili as cards; X as 「Xで見る」 cards (no X embed).
- Link-only site: noindex, robots disallow, no sitemap; 「非公式ファンサイト」 footer, 削除依頼 contact, no ads, neutral icon.
- Weekly liveness check of every source; fall back or hide.
- Only date/title/URL/mentions stored from 冬美便り.
- Owner interface = Google Sheet only (tabs 追加, おすすめ, 確認).
- Calendar defaults to a list of days with content; grid optional; ≥ 56px targets.
- Same-tab external links via a short notice page; 「← 戻る」 on every page.
- Readings, sort key, special days, and wording table as listed in the review.
- Actions: Asia/Tokyo dates, deploy in the same job, commit only on change, reject scrapes whose row count drops by more than 20%.

## 14. Owner decisions after review

- **Link-only but public:** no password; anyone with the link can view. Not listed by search engines (noindex, robots disallow, no sitemap).
- **Watch on the site:** every clip has its own page on the site with the player embedded, so fans never have to leave. YouTube and Bilibili play inline. X posts are embedded inline too (X's official embed); if X asks for a login or the embed fails, a large 「Xで見る」 button is the fallback. 「4曲つづけて聴く」 stays YouTube-only so it advances on its own.
- **Sharing:** every clip page (and the day's おすすめ) has a large 「共有する」 button.
  - On phones it opens the phone's own share sheet (Web Share API), so LINE, X, メール and others all work.
  - It also shows explicit 「LINEで送る」 and 「Xでポスト」 buttons for users who find the share sheet confusing, plus 「リンクをコピー」.
  - Shared links point to the **site's clip page**, not to X/Bilibili/YouTube, so whoever opens it also stays on the site. LINE links carry `?openExternalBrowser=1`.
  - Each clip page has OGP/Twitter Card tags (song title, date, thumbnail) so LINE and X show a proper preview card. This needs one small static HTML file per clip, generated by the daily job. noindex does not block these previews.

## 15. Owner feedback (2026-11-25)

Home page order and content:
1. 今日の出演 (unchanged).
2. 今日のおすすめ — default theme name 「冬美、歌がある」 (was 冬美のうた).
3. 「この頃の映像」 — the history section: videos from this month-day in past years (±3 days if none).
4. 冬美便り — her letters from this month-day in past years (±3 days if none), each with videos of songs it mentions.
5. 週刊FLASH — articles from the smart-flash.jp 坂本冬美 tag (`/tag/坂本冬美/`, pages 1–N) from this month-day in past years (±3 days if none): title (linked), issue, and 「記事に出てくる曲」; each song links to our newest video of it when the list has one, otherwise 「映像なし」. The WordPress API returns 403, so the public tag pages (allowed by robots.txt) are read; article text is read in memory for song names only and never stored.
6. 新しい映像 — removed.
The calendar's day view shows the same three kinds (videos, letters, FLASH articles).

## 16. Owner feedback (2026-11-25, round 2)

- Colors: blue + pink from the official site fuyumi-fc.com (sky #7FC6F2, pink #FFAEC5). Text/buttons use deepened shades for contrast: blue #2C6DB4 (5.3:1 on white), pink #C2306A (5.35:1). The official pastels are decoration only (bars, borders, backgrounds).
- 今日のおすすめ: default theme 「冬美、歌がある」, reason 「いろいろな年の冬美さん」; today's and tomorrow's picks are recomputed on every daily run.
- Theme buttons under the playlist (テーマを選ぶ): 季節 (春夏秋冬), 気持ち (恋・お酒・お祝い・母・お祭り・ふるさと・桜・雪・月のうた), ふるさと (prefectures, from `places` in songs.yaml). Tapping one swaps the playlist; 「今日のおすすめに戻す」 restores it. Up to 8 clips per theme, YouTube first, shuffled per day.
- 「N曲つづけて聴く」 plays any platform: YouTube clips advance by themselves; Bilibili/X clips need 「次の曲へ」.
- この頃の映像 / 冬美便り / 週刊FLASH show **that exact month-day only** (no ±3 days). Empty → 「この日の○○は、まだありません。」
- 週刊FLASH items also show 「○○さんとの共演映像」 for people tagged/mentioned in the article.
- u-fuyumi.net 掲示板 (fan forum; owner decision: behind the scenes only, to confirm TV broadcasts). Stored: topic title, link, first-post date (`data/forum_topics.json`); never member names or post text; nothing shown on the site except 「ファンの方の情報で確認しました」 on a clip confirmed this way. A clip with no fan-club match gets ✓ when a topic whose title matches the program was posted 3 days before to 1 day after the broadcast. Listing pages: 61 × 31 topics; dates are read gently (150 per history run, 20 per daily run, 2 s apart).
