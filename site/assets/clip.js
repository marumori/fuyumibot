/* One clip: player, details, share, other videos of the song, letters from around the broadcast. */
(function () {
  const main = document.getElementById("main");
  const c = JSON.parse(document.getElementById("clip-data").textContent);
  const verified = c.verified ? `<span class="badge">✓ 放送日確認済み</span>` +
    (c.verified_info ? `<p class="muted">ファンクラブの記録：${F.esc(c.verified_info.broadcaster)}「${F.esc(c.verified_info.program)}」</p>` : "") : "";
  const dateNote = c.date_source === "post_time" ? `<p class="muted">※放送日は投稿日からの推定です</p>` : "";
  const others = c.sources.filter((s) => s.platform !== c.source.platform)
    .map((s) => `<a class="btn" href="${F.esc(F.goHref(s.url))}">${F.esc(F.siteLabel(s.url))}で見る</a>`).join("");
  main.innerHTML =
    `<h1>${F.esc(c.title_label)}</h1>` +
    `<p>${F.esc(c.date_label)}</p>${dateNote}` +
    (c.program ? `<p>${F.esc(c.program)}</p>` : "") +
    (c.performers_label ? `<p class="muted">${F.esc(c.performers_label)}</p>` : "") + verified +
    `<div id="player"></div>` + (others ? `<div class="section"><h2>ほかの場所で見る</h2>${others}</div>` : "") +
    `<section class="section" id="share"></section>` +
    (c.others.length ? `<section class="section"><h2>この曲の他の映像</h2>${F.cards(c.others)}</section>` : "") +
    (c.letters.length ? `<section class="section"><h2>この頃の冬美便り</h2><ul class="list">` +
      c.letters.map((l) => `<li><a class="row" href="${F.esc(F.goHref(l.url))}"><span>${F.esc(l.title)}<br><span class="muted">${F.esc(l.date_label)}</span></span><span class="arrow">読む</span></a></li>`).join("") +
      `</ul></section>` : "") +
    `<nav class="nav"><a class="btn" href="/">今日の冬美へ</a></nav>`;
  F.mountSingle(document.getElementById("player"), c.source);
  F.shareButtons(document.getElementById("share"), { url: c.url, title: `${c.title_label} ${c.date_label}｜今日の冬美` });
  F.backButton(main);
  F.lineBanner(main);
})();
