/* Home 「今日の冬美」 */
async function mountThemes(today, queue) {
  const box = document.getElementById("themes");
  let groups = [];
  try { groups = await F.json("/data/themes.json"); } catch (e) { return; }
  if (!groups.length) return;
  const title = (g, th) => (g.label === "気持ち" ? th.label : `${th.label}のうた`);
  box.innerHTML = `<h3>テーマを選ぶ</h3><p class="muted">押すと、そのテーマの曲に入れかわります。</p>` +
    groups.map((g, gi) => `<p class="group">${F.esc(g.label)}</p><div class="chips">` +
      g.themes.map((th, ti) => `<button class="btn" type="button" aria-pressed="false" data-g="${gi}" data-t="${ti}">${F.esc(title(g, th))}</button>`).join("") +
      `</div>`).join("") +
    `<button class="btn" type="button" id="theme-reset" hidden style="margin-top:.8rem">今日のおすすめに戻す</button>`;
  const set = (name, reason, clips, pressed) => {
    document.querySelector("#pick .theme").textContent = name;
    document.getElementById("pick-reason").textContent = reason;
    document.getElementById("pick-list").innerHTML = F.cards(clips);
    F.mountQueue(queue, clips);
    box.querySelectorAll("[data-g]").forEach((b) => b.setAttribute("aria-pressed", String(b === pressed)));
    document.getElementById("theme-reset").hidden = !pressed;
    document.getElementById("pick").scrollIntoView({ behavior: "smooth", block: "start" });
  };
  box.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.id === "theme-reset") return set(today.theme_title, today.reason, today.clips, null);
    const g = groups[+b.dataset.g], th = g.themes[+b.dataset.t];
    set(title(g, th), `テーマ：${g.label}`, th.clips, b);
  });
}

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
    out.push(`<section class="section" id="pick"><h2>今日のおすすめ</h2><p class="theme">${F.esc(t.pick.theme_title)}</p>` +
      `<p class="muted" id="pick-reason">${F.esc(t.pick.reason)}</p><div id="queue"></div><div id="pick-list">${F.cards(t.pick.clips)}</div>` +
      `<div class="themes" id="themes"></div></section>`);
  }

  const sub = (what) => `<p class="sub">あの年の今日（${F.esc(t.date_label.replace(/（.*$/, ""))}）の${what}</p>`;
  const none = (what) => `<p class="empty">この日の${what}は、まだありません。</p>`;
  const byYear = (items, render) => {
    let last = "", html = "";
    for (const it of items) {
      if (it.year_label !== last) { html += `<p class="year">${F.esc(it.year_label)}</p>`; last = it.year_label; }
      html += render(it);
    }
    return html;
  };

  const otd = t.on_this_day;
  {
    const body = otd && otd.years.length ? otd.years.map((y) => `<p class="year">${F.esc(y.year_label)}</p>${F.cards(y.clips)}`).join("") : none("映像");
    out.push(`<section class="section"><h2>この頃の映像</h2>${sub("テレビの映像")}${body}</section>`);
  }

  if (t.letters) {
    const body = byYear(t.letters.items, (l) => `<a class="card nothumb" href="${F.esc(F.goHref(l.url))}"><span><span class="t">${F.esc(l.title)}</span><br>` +
      `<span class="m">${F.esc(l.date_label)}・ファンクラブのページへ</span></span></a>` +
      (l.clips.length ? `<p class="muted">便りに出てくる曲の映像</p>${F.cards(l.clips)}` : ""));
    out.push(`<section class="section"><h2>冬美便り</h2>${sub("便り")}${t.letters.items.length ? body : none("便り")}</section>`);
  }

  if (t.flash) {
    out.push(`<section class="section" id="flash"><h2>週刊FLASH</h2>${sub("記事")}` +
      `${t.flash.items.length ? byYear(t.flash.items, F.flashItem) : none("記事")}</section>`);
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
