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

  const otd = t.on_this_day;
  if (otd && otd.years.length) {
    const head = otd.exact ? "あの年の今日" : "この頃の映像";
    const body = otd.years.map((y) => `<p class="year">${F.esc(y.year_label)}</p>${F.cards(y.clips)}`).join("");
    out.push(`<section class="section"><h2>${head}</h2>${body}</section>`);
  }

  if (t.letters && t.letters.length) {
    const body = t.letters.map((l) => `<div><a class="card nothumb" href="${F.esc(F.goHref(l.url))}"><span><span class="t">${F.esc(l.title)}</span><br>` +
      `<span class="m">${F.esc(l.date_label)}・ファンクラブのページへ</span></span></a>` +
      (l.clips.length ? `<p class="muted">関連する映像</p>${F.cards(l.clips)}` : "") + `</div>`).join("<hr>");
    out.push(`<section class="section"><h2>冬美便り</h2>${body}</section>`);
  }

  if (t.flash) {
    const f = t.flash;
    out.push(`<section class="section"><h2>週刊FLASH 対談（火曜発売）</h2>` +
      `<p>${F.esc(f.issue_label)}${f.guest ? `　ゲスト：${F.esc(f.guest)}さん` : ""}</p>` +
      `<a class="btn" href="${F.esc(F.goHref(f.letter_url))}">冬美さんの便りを読む</a>` +
      (f.clips.length ? `<p class="muted" style="margin-top:.6rem">対談相手との共演映像</p>${F.cards(f.clips)}` : "") + `</section>`);
  }

  if (t.new && t.new.length) out.push(`<section class="section"><h2>新しい映像</h2>${F.cards(t.new)}</section>`);

  out.push(`<nav class="nav" aria-label="ほかのページ"><a class="btn primary" href="/calendar.html">カレンダー</a>` +
    `<a class="btn" href="/songs.html">曲名でさがす</a><a class="btn" href="/usage.html">使い方</a></nav>`);
  main.innerHTML = out.join("");
  if (t.pick) F.mountYouTubeQueue(document.getElementById("queue"), t.pick.clips);
  F.lineBanner(main);
})();
