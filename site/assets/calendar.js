/* カレンダー: list of days with content (default) or a month grid; tapping a day shows every year. */
(async function () {
  const main = document.getElementById("main");
  const calEl = document.getElementById("cal");
  const dayEl = document.getElementById("day");
  let cal = {};
  try { cal = await F.json("/data/calendar.json"); } catch (e) { calEl.innerHTML = "<p>読み込めませんでした。</p>"; }
  const now = new Date(Date.now());
  let y = now.getFullYear(), m = now.getMonth() + 1;
  let mode = "list";
  const pad = (n) => String(n).padStart(2, "0");

  const summary = (c) => [c.videos ? `映像${c.videos}本` : "", c.letters ? `冬美便り${c.letters}件` : "", c.flash ? "週刊FLASH 対談" : ""].filter(Boolean).join("・");

  function render() {
    const days = new Date(y, m, 0).getDate();
    let body = "";
    if (mode === "list") {
      const rows = [];
      for (let d = 1; d <= days; d++) {
        const c = cal[`${pad(m)}-${pad(d)}`];
        if (c) rows.push(`<li><button class="btn" type="button" data-md="${pad(m)}-${pad(d)}">${m}月${d}日（${summary(c)}）</button></li>`);
      }
      body = rows.length ? `<ul class="list" style="display:grid;gap:.5rem">${rows.join("")}</ul>` : `<p>この月はまだありません。</p>`;
    } else {
      const first = new Date(y, m - 1, 1).getDay();
      const cells = "日月火水木金土".split("").map((w) => `<div class="dow">${w}</div>`);
      for (let i = 0; i < first; i++) cells.push(`<button disabled aria-hidden="true"></button>`);
      const today = now.getMonth() + 1 === m && now.getFullYear() === y ? now.getDate() : -1;
      for (let d = 1; d <= days; d++) {
        const md = `${pad(m)}-${pad(d)}`, c = cal[md];
        const label = c ? `${m}月${d}日 ${summary(c)}` : `${m}月${d}日 なし`;
        cells.push(`<button type="button" data-md="${md}" class="${c ? "has" : ""} ${d === today ? "today" : ""}" aria-label="${label}">` +
          `${d}${c ? '<span class="dot"></span>' : ""}</button>`);
      }
      body = `<div class="grid">${cells.join("")}</div><p class="muted">赤い点のある日に、映像や便りがあります。</p>`;
    }
    calEl.innerHTML =
      `<div class="tabs"><button class="btn" type="button" data-mode="list" aria-pressed="${mode === "list"}">一覧表示</button>` +
      `<button class="btn" type="button" data-mode="grid" aria-pressed="${mode === "grid"}">カレンダー表示</button></div>` +
      `<div class="monthbar"><span class="label">${y}年${m}月</span><button class="btn" type="button" id="prev">◀ 前の月</button>` +
      `<button class="btn" type="button" id="next">次の月 ▶</button></div>` +
      `<button class="btn" type="button" id="today" style="margin-bottom:.8rem">今日</button>` + body;
  }

  async function showDay(md) {
    dayEl.innerHTML = "<p>読み込み中…</p>";
    let d;
    try { d = await F.json(`/data/days/${md}.json`); } catch (e) { dayEl.innerHTML = "<p>この日はまだありません。</p>"; return; }
    const years = d.years.map((yr) => {
      const letters = yr.letters.map((l) => `<li><a class="row" href="${F.esc(F.goHref(l.url))}"><span>冬美便り「${F.esc(l.title)}」</span><span class="arrow">読む</span></a></li>`).join("");
      const flash = yr.flash.map((f) => `<li><a class="row" href="${F.esc(F.goHref(f.letter_url))}"><span>週刊FLASH 対談${f.guest ? `（${F.esc(f.guest)}さん）` : ""}</span><span class="arrow">読む</span></a></li>`).join("");
      return `<p class="year">${F.esc(yr.year_label)}</p>${F.cards(yr.clips)}${letters || flash ? `<ul class="list">${letters}${flash}</ul>` : ""}`;
    }).join("");
    dayEl.innerHTML = `<section class="section"><h2>${F.esc(d.label)}の冬美</h2>${years}</section>`;
    dayEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  calEl.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.mode) { mode = b.dataset.mode; render(); }
    else if (b.id === "prev") { m--; if (m < 1) { m = 12; y--; } render(); }
    else if (b.id === "next") { m++; if (m > 12) { m = 1; y++; } render(); }
    else if (b.id === "today") { y = now.getFullYear(); m = now.getMonth() + 1; render(); }
    else if (b.dataset.md) showDay(b.dataset.md);
  });
  render();
  F.backButton(main);
  F.lineBanner(main);
  F.footer();
})();
