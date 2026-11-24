/* Home 「今日の冬美」 */
async function mountThemes(today, queue) {
  const box = document.getElementById("themes");
  const openBtn = document.getElementById("theme-open");
  const reset = document.getElementById("theme-reset");
  let groups = [];
  try { groups = await F.json("/data/themes.json"); } catch (e) { openBtn.hidden = true; return; }
  if (!groups.length) { openBtn.hidden = true; return; }
  const title = (g, th) => (g.label === "気持ち" ? th.label : `${th.label}のうた`);
  let tab = 0, current = null;
  const render = () => {
    const g = groups[tab];
    box.innerHTML = `<div class="tabs" role="tablist">` +
      groups.map((x, i) => `<button class="btn" type="button" role="tab" aria-selected="${i === tab}" aria-pressed="${i === tab}" data-tab="${i}">${F.esc(x.label)}</button>`).join("") +
      `</div><div class="chips">` +
      g.themes.map((th, ti) => `<button class="btn" type="button" aria-pressed="${current === `${tab}:${ti}`}" data-t="${ti}">${F.esc(title(g, th))}</button>`).join("") +
      `</div>`;
  };
  const toggle = (open) => {
    box.hidden = !open;
    openBtn.setAttribute("aria-expanded", String(open));
    openBtn.textContent = open ? "テーマを閉じる ▲" : "テーマを選ぶ ▼";
    if (open) render();
  };
  const set = (name, reason, clips) => {
    document.querySelector("#pick .theme").textContent = name;
    document.getElementById("pick-reason").textContent = reason;
    document.getElementById("pick-list").innerHTML = F.cards(clips);
    F.mountQueue(queue, clips);
    reset.hidden = current === null;
    toggle(false);
    document.getElementById("pick").scrollIntoView({ block: "start" });  // the playlist stays in view
  };
  openBtn.addEventListener("click", () => toggle(box.hidden));
  reset.addEventListener("click", () => { current = null; set(today.theme_title, today.reason, today.clips); });
  box.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.tab) { tab = +b.dataset.tab; render(); return; }
    const g = groups[tab], th = g.themes[+b.dataset.t];
    current = `${tab}:${b.dataset.t}`;
    set(title(g, th), `テーマ：${g.label}`, th.clips);
  });
}

(async function () {
  const main = document.getElementById("main");
  let t;
  try { t = await F.json("/data/today.json"); }
  catch (e) { main.innerHTML = `<p>読み込めませんでした。少し待ってから、もう一度開いてください。</p>`; return; }

  const out = [];
  out.push(`<header class="top"><p class="site-name">今日の冬美</p><h1 class="today">${F.esc(t.date_label)}</h1></header>`);

  const md = t.date_label.replace(/（.*$/, "");
  const none = (what) => `<p class="empty">この日の${what}は、まだありません。</p>`;
  const byYear = (items, render) => {
    let last = "", html = "";
    for (const it of items) {
      if (it.year_label !== last) { html += `<p class="year">${F.esc(it.year_label)}</p>`; last = it.year_label; }
      html += render(it);
    }
    return html;
  };

  // あの年の今日: 冬美便り, 週刊FLASH, テレビの映像 from this month-day in past years
  {
    const letters = t.letters && t.letters.items.length ? byYear(t.letters.items, (l) =>
      `<a class="card nothumb" href="${F.esc(F.goHref(l.url))}"><span><span class="t">${F.esc(l.title)}</span><br>` +
      `<span class="m">${F.esc(l.date_label)}・ファンクラブのページへ</span></span></a>` +
      (l.clips.length ? `<p class="muted">便りに出てくる曲の映像</p>${F.cards(l.clips)}` : "")) : none("便り");
    const flash = t.flash && t.flash.items.length ? byYear(t.flash.items, F.flashItem) : none("記事");
    const otd = t.on_this_day;
    const videos = otd && otd.years.length ? otd.years.map((y) => `<p class="year">${F.esc(y.year_label)}</p>${F.cards(y.clips)}`).join("") : none("映像");
    out.push(`<section class="section" id="otd"><h2>あの年の今日</h2><p class="sub">${F.esc(md)}の、いろいろな年の冬美さん</p>` +
      `<h3>冬美便り</h3>${letters}<h3>週刊FLASH</h3><div id="flash">${flash}</div><h3>テレビの映像</h3>${videos}</section>`);
  }

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
    out.push(`<section class="section" id="pick"><h2>今日のおすすめ</h2><p class="theme">${F.esc(t.pick.theme_title)}</p>` +
      `<p class="muted" id="pick-reason">${F.esc(t.pick.reason)}</p>` +
      `<button class="btn" type="button" id="theme-open" aria-expanded="false" aria-controls="themes">テーマを選ぶ ▼</button>` +
      `<div class="themes" id="themes" hidden></div>` +
      `<button class="btn" type="button" id="theme-reset" hidden>今日のおすすめに戻す</button>` +
      `<div id="queue"></div><div id="pick-list">${F.cards(t.pick.clips)}</div></section>`);
  }

  out.push(`<nav class="nav" aria-label="ほかのページ"><a class="btn primary" href="/calendar.html">カレンダー</a>` +
    `<a class="btn" href="/songs.html">曲名でさがす</a><a class="btn" href="/usage.html">使い方</a></nav>`);
  main.innerHTML = out.join("");
  if (t.pick) {
    const queue = document.getElementById("queue");
    F.mountQueue(queue, t.pick.clips);
    mountThemes(t.pick, queue);
  }
  F.lineBanner(main);
})();
