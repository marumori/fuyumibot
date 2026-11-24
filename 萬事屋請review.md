# 萬事屋 review — 「今日の冬美」 design

Reviewed: `docs/superpowers/specs/2026-11-24-fuyumi-digest-design.md`
Date: 2026-11-24 · Four reviewers in parallel: ① seniors & phones ② data & automation ③ rights & platforms ④ Japanese editing

Owner decisions made during review: **¥0 running cost**, **no paid X API** (X links via the paste sheet), **use only what's already uploaded** (no re-uploads).

---

## Must fix (changes the design)

| # | Issue | Fix adopted |
|---|---|---|
| 1 | **Most fans arrive from LINE.** LINE's in-app browser can't add to home screen, and players are unreliable. ① | Share links with `?openExternalBrowser=1`; detect LINE and show a big 「Safari（Chrome）で開くと、ホーム画面に置けます」 banner. Test every player inside LINE. |
| 2 | **25% of seed dates are post dates, not broadcast dates** (164 rows; 73 are a day off in JST). ② | Add `date_source: title / post_time`, convert to JST, never show ✓ on post-time dates, and send them to the 確認 tab. |
| 3 | **Splitting titles on spaces breaks real titles** (SWEET MEMORIES, 乙女座 宮, 夜桜お七 千本桜, TATTOO藤あや子…). ②④ | Use longest-match against a song dictionary plus alias table, a known-performer list read from the right, and a separate Bilibili parser. Add a test over all 669 rows. |
| 4 | **"Same date + first song" merges wrong clips** (225 no-song rows; 55 colliding keys). ② | Never merge on an empty song; require the program or performers to match too; the seed's 同一條 is the strongest hint. |
| 5 | **✓ is too loose.** Program names are short forms (人生歌 vs 「人生、歌がある」). ② | Program alias table; ✓ only when **date and program both** match; label it 「✓ 放送日確認済み」. |
| 6 | **Mixed-platform playlists stall on iPhone.** ① | 「4曲つづけて聴く」 uses **YouTube only**. The first player loads on page open, and ▶ calls `playVideo()` inside the tap. Bilibili clips get their own cards; X clips get a 「Xで見る」 card (no embed). |
| 7 | **Takedown / リーチサイト risk** from gathering TV clips in one public place. ③ | **Link-only**: `noindex`, robots disallow, no sitemap. **Private repo + Cloudflare Pages** (free). 「非公式ファンサイト」 footer, a 削除依頼 contact, no ads, neutral icon (no official photos). |
| 8 | **Dead channels / deleted videos** would leave broken players. ③ | Weekly liveness check (YouTube oEmbed, Bilibili view API): fall back to another platform's copy, or hide the clip. |
| 9 | **Fan-club text in the repo.** ③ | Commit only date / title / URL / mentions from 冬美便り; no body text, no raw HTML; check robots.txt and 利用規約 first; spread the back-catalogue pull over several days. |
| 10 | **The owner won't edit YAML or GitHub issues.** ② | Everything the owner touches lives in the **Google Sheet**: 追加 (X links), おすすめ (overrides), 確認 (review queue answered in columns). Column headers are checked before reading. |

## Should fix

- **Readings:** pre-fill and hand-check the kanji titles (夜桜お七 よざくらおしち, 雪深深 ゆきしんしん, 祝い酒 いわいざけ, 天城越え あまぎごえ, 夫婦善哉 めおとぜんざい, 花筐 はながたみ…). Readings of 雨夜酒 and 恋花 are unconfirmed. ④
- **Sort key:** katakana → hiragana, small kana treated as full-size, ー takes the preceding vowel, 清 < 濁 < 半濁 only as a tie-break, punctuation and 〜 subtitles ignored, plus an 英数字 section. ④
- **Names:** join performers with 「、」, not 「・」 (アグネス・チャン). Units (演歌5人娘) count as one performer. ④
- **和暦:** show it on year labels, e.g. 「1994年（平成6年）」, but not on today's date. ④
- **Special days to add** (confirm the dates): 夜桜お七 release 8月22日; また君に恋してる release 1月14日; 猪俣公章 6月10日; 八代亜紀 12月30日; 母の日 → 岸壁の母; 中秋の名月 → ほろ酔い満月; 2月6日 お燈まつり → 男の火祭り. Label memorials 「○○さんを偲んで」. On 1月1日, give 能登はいらんかいね a gentle frame, not a festive one. ④
- **Calendar:** the default view is a list of only the days with content (「12月31日（紅白ほか5本）」), with the grid as an option. Tap targets ≥ 56px, and words rather than emoji to show meaning. ①
- **Links:** open in the same tab after a short 「Xのページへ移動します」 page, with a big 「← 戻る」 on every page (home-screen mode has no back button). ①
- **Large-text settings:** use rem units, test at 200% font scale, keep crimson at ≥ 4.5:1 contrast (e.g. #A3002B), never put text over thumbnails. ①
- **Performance:** a small `today.json` (< 20KB), calendar split by month-day, song files split. ②
- **Actions:** compute all dates in Asia/Tokyo; deploy in the same job; commit only on content change; reject a scrape if its row count drops by more than 20%. ②
- **Bilibili may block GitHub's servers.** If it does, Bilibili links also go through the sheet. ②③
- **YouTube back-catalogue:** import it with the YouTube Data API (free key), not yt-dlp. ③

## Wording changes ①④

| Before | After |
|---|---|
| まとめて再生 | 4曲つづけて聴く |
| 曲名から | 曲名でさがす |
| 放送確認済み | 放送日確認済み |
| 動画は準備中です | 映像はまだありません |
| 新着動画 | 新しい映像 |
| 曲名なし | トーク・その他 |
| FLASH 対談 | 週刊FLASH 対談（火曜発売） |
| 当年今日 | あの年の今日 |
| 11/23 | 11月23日 |

Also: show song titles in 「」; store the wave dash as 〜 (U+301C); add a 「使い方」 button on the home page; tell users 「画面を消すと止まります」.

## Still open for the owner
- None. Owner chose: link-only but public (anyone with the link), videos watchable on the site, share buttons to LINE, X and others.
