/* 曲名でさがす (songs.html) and one song (song.html?id=...). */
(async function () {
  const main = document.getElementById("main");
  const id = new URLSearchParams(location.search).get("id");
  if (location.pathname.endsWith("/song.html")) {
    let s;
    try { s = await F.json(`/data/songs/${encodeURIComponent(id)}.json`); }
    catch (e) { main.innerHTML = "<p>この曲は見つかりませんでした。</p>"; F.backButton(main); F.footer(); return; }
    document.title = `「${s.title}」 | 今日の冬美`;
    main.innerHTML = `<h1>「${F.esc(s.title)}」</h1><p class="muted">${F.esc(s.yomi)}</p>` +
      `<section class="section"><h2>この曲の映像</h2>${F.cards(s.clips)}</section>` +
      (s.letters.length ? `<section class="section"><h2>この曲が出てくる冬美便り</h2><ul class="list">` +
        s.letters.map((l) => `<li><a class="row" href="${F.esc(F.goHref(l.url))}"><span>${F.esc(l.title)}<br><span class="muted">${F.esc(l.date_label)}</span></span><span class="arrow">読む</span></a></li>`).join("") +
        `</ul></section>` : "") +
      `<nav class="nav"><a class="btn" href="/songs.html">曲名でさがす</a></nav>`;
  } else {
    const el = document.getElementById("songs");
    let songs = [];
    try { songs = await F.json("/data/songs.json"); } catch (e) { el.innerHTML = "<p>読み込めませんでした。</p>"; }
    const order = ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ", "英数字"];
    const groups = order.map((g) => [g, songs.filter((s) => s.gyo === g)]).filter(([, l]) => l.length);
    el.innerHTML = `<nav class="gyo" aria-label="行">${groups.map(([g]) => `<a class="btn" href="#gyo-${g}">${g}</a>`).join("")}</nav>` +
      groups.map(([g, list]) => `<section class="section" id="gyo-${g}"><h2>${g === "英数字" ? "英数字" : g + "行"}</h2><ul class="list">` +
        list.map((s) => `<li><a class="row" href="/song.html?id=${encodeURIComponent(s.id)}"><span><span class="song-title">「${F.esc(s.title)}」</span>` +
          `<span class="yomi">${F.esc(s.yomi)}</span></span><span class="count">${s.count}本</span></a></li>`).join("") +
        `</ul></section>`).join("");
  }
  F.backButton(main);
  F.lineBanner(main);
  F.footer();
})();
