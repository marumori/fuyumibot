// Browser checks. Usage: node tests/ui/run.mjs <baseUrl>   (exit code 1 on any failure)
import { createRequire } from "node:module";
const { chromium, devices } = createRequire(import.meta.url)("playwright");
import assert from "node:assert/strict";

const BASE = process.argv[2];
const only = process.argv[3];
const browser = await chromium.launch();
let failed = 0;

const YT_STUB = `
window.__yt = { calls: [], syncPlay: false };
window.YT = { PlayerState: { ENDED: 0, PLAYING: 1 }, Player: function (el, opts) {
  const self = this; window.__ytPlayer = this; this.opts = opts;
  this.playVideo = () => { window.__yt.calls.push("playVideo"); window.__yt.syncPlay = !!window.__inClick; };
  this.loadVideoById = (id) => window.__yt.calls.push("load:" + id);
  this.cueVideoById = (id) => window.__yt.calls.push("cue:" + id);
  setTimeout(() => opts.events && opts.events.onReady && opts.events.onReady({ target: self }), 10);
}};
setTimeout(() => window.onYouTubeIframeAPIReady && window.onYouTubeIframeAPIReady(), 20);`;

async function page(device = "iPhone 13", extra = {}) {
  const ctx = await browser.newContext({ ...devices[device], ...extra });
  await ctx.route("https://www.youtube.com/iframe_api", (r) => r.fulfill({ contentType: "text/javascript", body: YT_STUB }));
  await ctx.route(/fonts\.(googleapis|gstatic)\.com/, (r) => r.abort());
  await ctx.route(/i\.ytimg\.com/, (r) => r.abort());
  await ctx.route(/player\.bilibili\.com/, (r) => r.fulfill({ contentType: "text/html", body: "<html>bili</html>" }));
  await ctx.addInitScript(() => { Date.now = ((n) => () => n)(new Date("2026-12-31T08:00:00+09:00").getTime()); });
  const p = await ctx.newPage();
  p.ctx = ctx;
  return p;
}

async function test(name, fn) {
  if (only && !name.includes(only)) return;
  try { await fn(); console.log("ok   " + name); }
  catch (e) { failed++; console.log("FAIL " + name + "\n     " + String(e.message).split("\n").slice(0, 6).join("\n     ")); }
}

for (const device of ["iPhone 13", "Pixel 7"]) {
  await test(`[${device}] home sections and labels`, async () => {
    const p = await page(device);
    await p.goto(BASE + "/");
    await p.getByText("今日のおすすめ").first().waitFor();
    for (const t of ["今日のおすすめ", "大みそかのうた", "4曲つづけて聴く", "この頃の映像", "今日の出演", "冬美便り", "大みそかの便り",
                     "週刊FLASH", "紅白の舞台裏を語る", "記事に出てくる曲", "非公式ファンサイト", "カレンダー", "曲名でさがす", "使い方"])
      assert.ok(await p.getByText(t).first().isVisible(), t);
    assert.equal(await p.getByText("新しい映像").count(), 0);
    assert.ok(await p.getByText("「夜桜お七」").first().isVisible());
    assert.ok(await p.getByText("2025年（令和7年）").first().isVisible());
    await p.ctx.close();
  });

  await test(`[${device}] tap targets at least 56px`, async () => {
    const p = await page(device);
    await p.goto(BASE + "/");
    await p.getByText("4曲つづけて聴く").waitFor();
    const small = await p.$$eval("main a, main button", (els) => els.filter((e) => e.offsetParent && e.getBoundingClientRect().height < 55.5).map((e) => e.textContent.trim().slice(0, 30)));
    assert.deepEqual(small, []);
    await p.ctx.close();
  });

  await test(`[${device}] 200% text: no horizontal scroll`, async () => {
    const p = await page(device);
    await p.goto(BASE + "/");
    await p.getByText("4曲つづけて聴く").waitFor();
    await p.addStyleTag({ content: "html{font-size:250% !important}" });
    const [sw, iw] = await p.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
    assert.ok(sw <= iw, `${sw} > ${iw}`);
    await p.ctx.close();
  });
}

await test("play button calls playVideo inside the tap", async () => {
  const p = await page();
  await p.goto(BASE + "/");
  const btn = p.getByRole("button", { name: /4曲つづけて聴く/ });
  await btn.waitFor();
  await p.waitForFunction(() => window.__ytPlayer);
  await p.waitForTimeout(50);
  await p.evaluate(() => document.addEventListener("click", () => {}, true));
  await p.evaluate(() => { const b = [...document.querySelectorAll("button")].find((x) => x.textContent.includes("4曲つづけて聴く"));
    b.addEventListener("click", () => { window.__inClick = true; }, { capture: true }); });
  await btn.click();
  const yt = await p.evaluate(() => window.__yt);
  assert.ok(yt.calls.includes("playVideo"), JSON.stringify(yt));
  assert.equal(yt.syncPlay, true);
  await p.evaluate(() => window.__ytPlayer.opts.events.onStateChange({ data: 0 }));
  const calls = await p.evaluate(() => window.__yt.calls);
  assert.ok(calls.some((c) => c.startsWith("load:")), JSON.stringify(calls));
  assert.ok(await p.getByText("（2/4）").isVisible());
  await p.ctx.close();
});

await test("theme buttons switch the playlist", async () => {
  const p = await page();
  await p.goto(BASE + "/");
  await p.getByText("テーマを選ぶ").waitFor();
  for (const g of ["季節", "気持ち"]) assert.ok(await p.getByText(g, { exact: true }).first().isVisible(), g);
  await p.getByRole("button", { name: "お祭りのうた" }).click();
  assert.equal(await p.locator(".theme").textContent(), "お祭りのうた");
  assert.ok(await p.getByRole("button", { name: /2曲つづけて聴く/ }).isVisible());
  await p.getByRole("button", { name: "今日のおすすめに戻す" }).click();
  assert.equal(await p.locator(".theme").textContent(), "大みそかのうた");
  await p.ctx.close();
});

await test("mixed playlist: next button moves from YouTube to Bilibili", async () => {
  const p = await page();
  await p.goto(BASE + "/");
  await p.getByRole("button", { name: "お祭りのうた" }).click();
  await p.waitForFunction(() => window.__ytPlayer);
  await p.getByRole("button", { name: /2曲つづけて聴く/ }).click();
  await p.getByRole("button", { name: /次の曲へ/ }).click();
  assert.ok(await p.getByText("（2/2）").isVisible());
  const src = await p.locator("#queue iframe").first().getAttribute("src");
  assert.match(src, /player\.bilibili\.com/);
  await p.ctx.close();
});

await test("FLASH: co-star videos", async () => {
  const p = await page();
  await p.goto(BASE + "/");
  await p.getByText("M!LKさんとの共演映像").waitFor();
  await p.ctx.close();
});

await test("FLASH article: mentioned songs link to our video, others are plain", async () => {
  const p = await page();
  await p.goto(BASE + "/");
  await p.getByText("記事に出てくる曲").waitFor();
  const linked = p.locator("#flash a", { hasText: "「夜桜お七」" });
  assert.match(await linked.first().getAttribute("href"), /^\/v\//);
  assert.equal(await p.locator("#flash a", { hasText: "「千本桜」" }).count(), 0);
  assert.ok(await p.locator("#flash", { hasText: "「千本桜」" }).isVisible());
  assert.match(await p.locator("#flash a", { hasText: "紅白の舞台裏を語る" }).getAttribute("href"), /^\/go\.html\?to=https%3A%2F%2Fsmart-flash\.jp/);
  await p.ctx.close();
});

await test("go page allows FLASH", async () => {
  const p = await page();
  await p.goto(BASE + "/go.html?to=" + encodeURIComponent("https://smart-flash.jp/entertainment/entertainment-news/1/"));
  assert.ok(await p.getByText("週刊FLASHのページへ移動します").isVisible());
  await p.ctx.close();
});

await test("TV card before broadcast", async () => {
  const p = await page();
  await p.goto(BASE + "/");
  await p.getByText("今日の出演").waitFor();
  assert.ok(await p.getByText("19:20").first().isVisible());
  assert.ok(await p.getByText("第77回NHK紅白歌合戦").first().isVisible());
  await p.ctx.close();
});

await test("LINE banner shown inside LINE", async () => {
  const p = await page("iPhone 13", { userAgent: devices["iPhone 13"].userAgent + " Line/13.20.0" });
  await p.goto(BASE + "/");
  await p.locator("#line-banner").waitFor();
  assert.match(await p.locator("#open-external").getAttribute("href"), /openExternalBrowser=1/);
  await p.ctx.close();
});

await test("no LINE banner in Safari", async () => {
  const p = await page();
  await p.goto(BASE + "/");
  await p.getByText("今日のおすすめ").first().waitFor();
  assert.equal(await p.locator("#line-banner").count(), 0);
  await p.ctx.close();
});

await test("clip page: share buttons and verified badge", async () => {
  const p = await page();
  await p.goto(BASE + "/");
  const href = await p.locator("a.card", { hasText: "夜桜お七" }).first().getAttribute("href");
  await p.goto(BASE + href);
  await p.getByText("LINEで送る").waitFor();
  const line = await p.locator("#share-line").getAttribute("href");
  assert.match(line, /^https:\/\/line\.me\/R\/share\?text=/);
  assert.match(decodeURIComponent(line), /openExternalBrowser=1/);
  assert.match(await p.locator("#share-x").getAttribute("href"), /^https:\/\/x\.com\/intent\/post\?/);
  assert.ok(await p.getByText("✓ 放送日確認済み").first().isVisible());
  assert.ok(await p.getByText("← 戻る").isVisible());
  await p.ctx.close();
});

await test("clip page: X fallback after timeout", async () => {
  const p = await page();
  await p.ctx.route(/platform\.twitter\.com/, (r) => r.abort());
  await p.goto(BASE + "/");
  const href = await p.locator("a.card", { hasText: "雪深深" }).first().getAttribute("href");
  await p.goto(BASE + href);
  await p.getByText("Xで見る").waitFor({ timeout: 8000 });
  assert.match(await p.getByText("Xで見る").getAttribute("href"), /^\/go\.html\?to=https%3A%2F%2Fx\.com/);
  await p.ctx.close();
});

await test("clip page: bilibili embed without danmaku", async () => {
  const p = await page();
  await p.goto(BASE + "/");
  const href = await p.locator("a.card", { hasText: "お祭りマンボ" }).first().getAttribute("href");
  await p.goto(BASE + href);
  const src = await p.locator("iframe").first().getAttribute("src");
  assert.match(src, /player\.bilibili\.com\/player\.html\?bvid=BV1szWZ6NEDE.*danmaku=0.*autoplay=0/);
  await p.ctx.close();
});

await test("go page: same-tab notice and refuses unknown hosts", async () => {
  const p = await page();
  await p.goto(BASE + "/go.html?to=" + encodeURIComponent("https://x.com/jounotakeuchi/status/1"));
  assert.ok(await p.getByText("X（旧ツイッター）のページへ移動します").isVisible());
  assert.equal(await p.getByText("移動する").getAttribute("href"), "https://x.com/jounotakeuchi/status/1");
  assert.equal(await p.getByText("移動する").getAttribute("target"), null);
  await p.goto(BASE + "/go.html?to=" + encodeURIComponent("https://evil.example/"));
  assert.equal(await p.getByText("移動する").count(), 0);
  await p.ctx.close();
});

await test("noindex everywhere", async () => {
  const p = await page();
  for (const path of ["/", "/usage.html", "/go.html"]) {
    await p.goto(BASE + path);
    assert.equal(await p.locator('meta[name="robots"]').getAttribute("content"), "noindex,nofollow", path);
  }
  const r = await p.goto(BASE + "/robots.txt");
  assert.match(await r.text(), /Disallow: \//);
  await p.ctx.close();
});


await test("calendar: list of days with content, tap shows years", async () => {
  const p = await page();
  await p.goto(BASE + "/calendar.html");
  const row = p.getByRole("button", { name: /12月31日（映像6本・冬美便り1件・週刊FLASH1件）/ });
  await row.waitFor();
  assert.ok(await p.getByRole("button", { name: /12月29日（冬美便り1件）/ }).isVisible());
  assert.ok(await p.getByRole("button", { name: /12月22日（週刊FLASH1件）/ }).isVisible());
  await row.click();
  await p.getByText("12月31日の冬美").waitFor();
  const labels = await p.locator("#day .year").allTextContents();
  assert.deepEqual(labels.slice(0, 2), ["2025年（令和7年）", "2024年（令和6年）"]);
  await p.ctx.close();
});

await test("calendar: grid toggle, big cells, month buttons", async () => {
  const p = await page();
  await p.goto(BASE + "/calendar.html");
  await p.getByRole("button", { name: "カレンダー表示" }).click();
  const cell = p.locator(".grid button.has").first();
  await cell.waitFor();
  const h = await cell.evaluate((e) => e.getBoundingClientRect().height);
  assert.ok(h >= 55.5, String(h));
  await p.getByRole("button", { name: /前の月/ }).click();
  assert.ok(await p.getByText("2026年11月").isVisible());
  await p.getByRole("button", { name: "今日" }).click();
  assert.ok(await p.getByText("2026年12月").isVisible());
  await p.ctx.close();
});

await test("songs: gojuon sections, jump, song page", async () => {
  const p = await page();
  await p.goto(BASE + "/songs.html");
  await p.getByText("「あばれ太鼓」").waitFor();
  const titles = await p.locator(".song-title").allTextContents();
  assert.ok(titles.indexOf("「あばれ太鼓」") < titles.indexOf("「祝い酒」"), titles.join(","));
  assert.ok(titles.indexOf("「祝い酒」") < titles.indexOf("「夜桜お七」"));
  assert.ok(await p.getByText("いわいざけ").isVisible());
  await p.getByRole("link", { name: "や", exact: true }).click();
  await p.waitForTimeout(300);
  const top = await p.locator("#gyo-や").evaluate((e) => e.getBoundingClientRect().top);
  assert.ok(top < 200, String(top));
  await p.getByText("「夜桜お七」").click();
  await p.getByText("この曲の映像").waitFor();
  assert.ok(await p.locator("a.card").count() >= 1);
  assert.ok(await p.getByText("← 戻る").isVisible());
  await p.ctx.close();
});

await browser.close();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
