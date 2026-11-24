// Renders site/icon-512.png and site/og-default.png (no photos; neutral typographic marks).
import { createRequire } from "node:module";
const { chromium } = createRequire(import.meta.url)("playwright");
const b = await chromium.launch();
const p = await b.newPage();
const font = `'Hiragino Mincho ProN','Noto Serif CJK JP','Noto Serif JP',serif`;
await p.setViewportSize({ width: 512, height: 512 });
await p.setContent(`<body style="margin:0"><div style="width:512px;height:512px;background:#A3002B;display:flex;align-items:center;justify-content:center;color:#fff;font:700 300px ${font}">冬</div></body>`);
await p.screenshot({ path: "site/icon-512.png" });
await p.setViewportSize({ width: 1200, height: 630 });
await p.setContent(`<body style="margin:0"><div style="width:1200px;height:630px;background:#FAF7F2;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:${font}">
<div style="width:120px;height:8px;background:#A3002B;margin-bottom:40px"></div>
<div style="font:700 120px ${font};color:#1F1A17">今日の冬美</div>
<div style="font:400 40px ${font};color:#5E5650;margin-top:24px">坂本冬美さんの映像を、毎日ひとつの場所で</div></div></body>`);
await p.screenshot({ path: "site/og-default.png" });
await b.close();
