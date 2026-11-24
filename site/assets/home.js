/* Home 「今日の冬美」 */
(async function () {
  const main = document.getElementById("main");
  let t;
  try { t = await F.json("/data/today.json"); }
  catch (e) { main.innerHTML = `<p>読み込めませんでした。少し待ってから、もう一度開いてください。</p>`; return; }

  const out = [];
  out.push(`<header class="top"><p class="site-name">今日の冬美</p><h1 class="today">${F.esc(t.date_label)}</h1></header>`);

  if (t.appearances && t.appearances.length) {
    const rows = t.appearances.map((a) => {
      let state = a.state;
      if (state === "before" && a.is_today && a.start && F.nowHM() >= a.start.padStart(5, "0")) state = "aired";
      const when = a.is_today ? (a.start ? `今日 ${F.esc(a.start)}から` : "今日") : `${F.esc(a.date_label)}`;
      const note = a.note ? `（${F.esc(a.note === "再放送" ? "再放送" : a.note.startsWith("VTR") ? "VTR出演" : a.note)}）` : "";
      let st = "";
      if (state === "clip") st = `<div class="state">放送の映像があります</div>${F.card(a.clip)}`;
      else if (state === "aired") st = `<div class="state">放送されました。映像はまだありません。</div>`;
      return `<div class="tv"><p class="when">${when}</p><p class="prog">${F.esc(a.broadcaster)}「${F.esc(a.program)}」${note}</p>${st}</div>`;
    }).join("<hr>");
    out.push(`<section class="section accent"><h2>今日の出演</h2>${rows}</section>`);
  }

  if (t.pick && t.pick.clips.length) {
    out.push(`<section class="section"><h2>今日のおすすめ</h2><p class="theme">${F.esc(t.pick.theme_title)}</p>` +
      `<p class="muted">${F.esc(t.pick.reason)}</p><div id="queue"></div><div>${F.cards(t.pick.clips)}</div></section>`);
  }

  const sub = (exact, what) => `<p class="sub">${exact ? "あの年の今日" : "この頃（前後3日）"}の${what}</p>`;
  const byYear = (items, render) => {
    let last = "", html = "";
    for (const it of items) {
      if (it.year_label !== last) { html += `<p class="year">${F.esc(it.year_label)}</p>`; last = it.year_label; }
      html += render(it);
    }
    return html;
  };

  const otd = t.on_this_day;
  if (otd && otd.years.length) {
    const body = otd.years.map((y) => `<p class="year">${F.esc(y.year_label)}</p>${F.cards(y.clips)}`).join("");
    out.push(`<section class="section"><h2>この頃の映像</h2>${sub(otd.exact, "映像")}${body}</section>`);
  }

  if (t.letters && t.letters.items.length) {
    const body = byYear(t.letters.items, (l) => `<a class="card nothumb" href="${F.esc(F.goHref(l.url))}"><span><span class="t">${F.esc(l.title)}</span><br>` +
      `<span class="m">${F.esc(l.date_label)}・ファンクラブのページへ</span></span></a>` +
      (l.clips.length ? `<p class="muted">便りに出てくる曲の映像</p>${F.cards(l.clips)}` : ""));
    out.push(`<section class="section"><h2>冬美便り</h2>${sub(t.letters.exact, "便り")}${body}</section>`);
  }

  if (t.flash && t.flash.items.length) {
    out.push(`<section class="section" id="flash"><h2>週刊FLASH</h2>${sub(t.flash.exact, "記事")}${byYear(t.flash.items, F.flashItem)}</section>`);
  }

  out.push(`<nav class="nav" aria-label="ほかのページ"><a class="btn primary" href="/calendar.html">カレンダー</a>` +
    `<a class="btn" href="/songs.html">曲名でさがす</a><a class="btn" href="/usage.html">使い方</a></nav>`);
  main.innerHTML = out.join("");
  if (t.pick) F.mountYouTubeQueue(document.getElementById("queue"), t.pick.clips);
  F.lineBanner(main);
})();
