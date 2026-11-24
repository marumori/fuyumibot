/* Shared helpers: escaping, cards, LINE handling, back button, footer. */
(function () {
  const F = (window.F = {});
  const cfg = window.FUYUMI_CONFIG || {};
  const ALLOWED = ["smart-flash.jp", "x.com", "twitter.com", "fuyumi-fc.com", "www.bilibili.com", "bilibili.com", "www.youtube.com", "youtube.com", "youtu.be"];

  F.esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  F.json = async (url) => { const r = await fetch(url, { cache: "no-cache" }); if (!r.ok) throw new Error(url); return r.json(); };
  F.isLine = () => /\bLine\//i.test(navigator.userAgent);

  const SITE_LABEL = { "smart-flash.jp": "週刊FLASH", "x.com": "X（旧ツイッター）", "twitter.com": "X（旧ツイッター）", "fuyumi-fc.com": "坂本冬美 公式ファンクラブ",
    "www.bilibili.com": "ビリビリ動画", "bilibili.com": "ビリビリ動画", "www.youtube.com": "YouTube", "youtube.com": "YouTube", "youtu.be": "YouTube" };
  F.siteLabel = (url) => { try { return SITE_LABEL[new URL(url).host] || "外部のサイト"; } catch (e) { return "外部のサイト"; } };
  F.allowed = (url) => { try { const u = new URL(url); return u.protocol === "https:" && ALLOWED.includes(u.host); } catch (e) { return false; } };
  F.goHref = (url) => "/go.html?to=" + encodeURIComponent(url);

  F.card = (c, opts = {}) => {
    const day = String(c.date_label || "").replace(/（.*$/, "");
    const meta = [[day, c.program].filter(Boolean).join("・"), c.performers_label].filter(Boolean).map(F.esc).join("<br>");
    const img = c.thumb ? `<img src="${F.esc(c.thumb)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.removeAttribute('src');this.alt=''">` : "";
    const badge = c.verified ? `<span class="badge">✓ 放送日確認済み</span>` : "";
    return `<a class="card${img ? "" : " nothumb"}" href="${F.esc(c.url)}">${img}<span><span class="t">${F.esc(c.title_label)}</span><br>` +
      `<span class="m">${meta}</span><br>${badge}<span class="go">${opts.go || "▶ 見る"}</span></span></a>`;
  };
  F.cards = (list, opts) => (list || []).map((c) => F.card(c, opts)).join("");

  /* A FLASH article: title (to the article), issue, and the songs it mentions — linked to our video when we have one. */
  F.flashItem = (a) => {
    const songs = (a.songs || []).map((s) => s.clip
      ? `<li><a class="row" href="${F.esc(s.clip.url)}"><span>「${F.esc(s.title)}」</span><span class="arrow">▶ 映像</span></a></li>`
      : `<li><span class="row">「${F.esc(s.title)}」<span class="muted">映像なし</span></span></li>`).join("");
    return `<a class="card nothumb" href="${F.esc(F.goHref(a.url))}"><span><span class="t">${F.esc(a.title)}</span><br>` +
      `<span class="m">${F.esc([a.date_label, a.issue].filter(Boolean).join("・"))}</span><br><span class="go">記事を読む</span></span></a>` +
      (songs ? `<p class="muted">記事に出てくる曲</p><ul class="list">${songs}</ul>` : "");
  };

  F.lineBanner = (root) => {
    if (!F.isLine()) return;
    const div = document.createElement("div");
    div.className = "banner";
    div.id = "line-banner";
    div.innerHTML = `<p><strong>LINEの中で開いています。</strong></p><p>Safari（Chrome）で開くと、ホーム画面に置けて見やすくなります。</p>` +
      `<a class="btn" id="open-external">Safari（Chrome）で開く</a>`;
    root.prepend(div);
    const u = new URL(location.href);
    u.searchParams.set("openExternalBrowser", "1");
    div.querySelector("#open-external").href = u.toString();
  };

  F.backButton = (root) => {
    const a = document.createElement("a");
    a.className = "btn back";
    a.href = "/";
    a.textContent = "← 戻る";
    a.addEventListener("click", (e) => {
      if (history.length > 1 && document.referrer && new URL(document.referrer).host === location.host) { e.preventDefault(); history.back(); }
    });
    root.prepend(a);
  };

  F.footer = () => {
    const f = document.createElement("footer");
    const contact = cfg.contactUrl ? `<a href="${F.esc(cfg.contactUrl)}">削除のご依頼はこちら</a>` : `<a href="/usage.html#contact">削除のご依頼はこちら</a>`;
    f.innerHTML = `<p>非公式ファンサイト ・ ${contact}</p><p>坂本冬美さん・所属事務所・公式ファンクラブとは関係ありません。</p>`;
    document.body.appendChild(f);
  };

  F.toast = (msg) => {
    const t = document.createElement("div");
    t.className = "toast";
    t.setAttribute("role", "status");
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 2200);
  };

  F.nowHM = () => { const d = new Date(); return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0"); };
})();
