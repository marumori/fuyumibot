/* 共有する / LINEで送る / Xでポスト / リンクをコピー */
(function () {
  window.F = window.F || {};
  F.shareButtons = (el, { url, title }) => {
    const abs = new URL(url, location.origin).toString();
    const lineUrl = abs + (abs.includes("?") ? "&" : "?") + "openExternalBrowser=1";
    const lineHref = "https://line.me/R/share?text=" + encodeURIComponent(title + "\n" + lineUrl);
    const xHref = "https://x.com/intent/post?text=" + encodeURIComponent(title) + "&url=" + encodeURIComponent(abs);
    el.innerHTML = `<h2>家族や友だちに送る</h2>` +
      (navigator.share ? `<button class="btn primary" type="button" id="share-native">共有する</button>` : "") +
      `<div class="btn-row" style="margin-top:.6rem"><a class="btn" id="share-line" href="${F.esc(lineHref)}">LINEで送る</a>` +
      `<a class="btn" id="share-x" href="${F.esc(xHref)}">Xでポスト</a></div>` +
      `<button class="btn" type="button" id="share-copy">リンクをコピー</button>`;
    const n = el.querySelector("#share-native");
    if (n) n.addEventListener("click", () => navigator.share({ title, text: title, url: abs }).catch(() => {}));
    el.querySelector("#share-copy").addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(abs); F.toast("コピーしました"); }
      catch (e) { window.prompt("このリンクをコピーしてください", abs); }
    });
  };
})();
