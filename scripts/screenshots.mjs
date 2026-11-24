// node scripts/screenshots.mjs <baseUrl> <outDir> — full-page phone screenshots for review.
import { createRequire } from "node:module";
const { chromium, devices } = createRequire(import.meta.url)("playwright");
const [base, out] = process.argv.slice(2);
const b = await chromium.launch();
for (const [dev, name] of [["iPhone 13", "iphone"], ["Pixel 7", "android"]]) {
  const ctx = await b.newContext({ ...devices[dev] });
  await ctx.route(/i\.ytimg\.com|youtube\.com|platform\.twitter\.com|bilibili\.com/, (r) => r.abort());
  const p = await ctx.newPage();
  for (const [path, tag] of [["/", "home"], ["/calendar.html", "calendar"], ["/songs.html", "songs"]]) {
    const r = await p.goto(base + path);
    if (!r || !r.ok()) continue;
    await p.waitForTimeout(800);
    await p.screenshot({ path: `${out}/${name}-${tag}.png`, fullPage: true });
  }
  const href = await p.goto(base + "/").then(() => p.locator("a.card").first().getAttribute("href"));
  await p.goto(base + href); await p.waitForTimeout(800);
  await p.screenshot({ path: `${out}/${name}-clip.png`, fullPage: true });
  await ctx.close();
}
await b.close();
