// Renders site/icon-512.png and site/og-default.png (no photos; neutral typographic marks).
import { createRequire } from "node:module";
const { chromium } = createRequire(import.meta.url)("playwright");
const b = await chromium.launch();
const p = await b.newPage();
const font = `'Hiragino Mincho ProN','Noto Serif CJK JP','Noto Serif JP',serif`;
await p.setViewportSize({ width: 512, height: 512 });
await p.setContent(`<body style="margin:0"><div style="width:512px;height:512px;background:linear-gradient(160deg,#7FC6F2,#2C6DB4 60%,#C2306A);display:flex;align-items:center;justify-content:center;color:#fff;font:700 300px ${font}">冬</div></body>`);
await p.screenshot({ path: "site/icon-512.png" });
await p.setViewportSize({ width: 1200, height: 630 });
await p.setContent(`<body style="margin:0"><div style="width:1200px;height:630px;background:linear-gradient(135deg,#EAF6FE,#FFF0F5);display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:${font}">
<div style="width:120px;height:8px;background:linear-gradient(90deg,#7FC6F2,#FFAEC5);margin-bottom:40px"></div>
<div style="font:700 120px ${font};color:#1C2733">今日の冬美</div>
<div style="font:400 40px ${font};color:#4E5D6C;margin-top:24px">坂本冬美さんの映像を、毎日ひとつの場所で</div></div></body>`);
await p.screenshot({ path: "site/og-default.png" });
await b.close();
