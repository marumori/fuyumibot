/* Players: a YouTube queue for 「N曲つづけて聴く」, and single embeds for YouTube / Bilibili / X. */
(function () {
  window.F = window.F || {};
  let apiPromise = null;
  function loadYT() {
    if (window.YT && window.YT.Player) return Promise.resolve();
    if (!apiPromise) {
      apiPromise = new Promise((resolve) => {
        const prev = window.onYouTubeIframeAPIReady;
        window.onYouTubeIframeAPIReady = () => { prev && prev(); resolve(); };
        const s = document.createElement("script");
        s.src = "https://www.youtube.com/iframe_api";
        document.head.appendChild(s);
      });
    }
    return apiPromise;
  }

  /* The first video is loaded (not started) on page load, so the tap can call playVideo()
     synchronously — iOS only allows sound when play starts inside the tap itself. */
  F.mountYouTubeQueue = (el, cards) => {
    const list = cards.filter((c) => c.source && c.source.platform === "youtube");
    if (!list.length) return;
    let i = 0, player = null, ready = false, wantPlay = false;
    el.innerHTML = `<div class="player"><div id="yt-queue"></div></div>` +
      `<p class="now" aria-live="polite"></p>` +
      `<button class="btn primary" type="button" id="queue-play">▶ ${list.length}曲つづけて聴く</button>` +
      `<button class="btn" type="button" id="queue-next" hidden>次の曲へ ▶</button>`;
    const now = el.querySelector(".now");
    const showNow = () => { now.textContent = `いま：${list[i].title_label}（${i + 1}/${list.length}）`; };
    const next = () => {
      if (i + 1 >= list.length) { now.textContent = "最後まで聴きました。"; return; }
      i++; showNow(); player.loadVideoById(list[i].source.id);
    };
    loadYT().then(() => {
      player = new YT.Player("yt-queue", {
        videoId: list[0].source.id, playerVars: { playsinline: 1, rel: 0 },
        events: {
          onReady: () => { ready = true; if (wantPlay) player.playVideo(); },
          onStateChange: (e) => { if (e.data === YT.PlayerState.ENDED) next(); },
        },
      });
    });
    el.querySelector("#queue-play").addEventListener("click", () => {
      showNow();
      el.querySelector("#queue-next").hidden = false;
      if (ready) player.playVideo(); else wantPlay = true;
    });
    el.querySelector("#queue-next").addEventListener("click", () => player && next());
  };

  F.mountSingle = (el, src) => {
    if (src.platform === "youtube") {
      el.innerHTML = `<div class="player"><iframe src="https://www.youtube.com/embed/${encodeURIComponent(src.id)}?playsinline=1&rel=0" ` +
        `title="動画" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe></div>`;
    } else if (src.platform === "bilibili") {
      el.innerHTML = `<p class="muted">ビリビリ動画の画面です（中国語の表示が出ることがあります）。</p>` +
        `<div class="player"><iframe src="https://player.bilibili.com/player.html?bvid=${encodeURIComponent(src.id)}&page=1&danmaku=0&high_quality=1&autoplay=0" ` +
        `title="動画" allowfullscreen sandbox="allow-scripts allow-same-origin allow-presentation"></iframe></div>`;
    } else {
      mountX(el, src);
    }
  };

  function xFallback(el, src) {
    el.innerHTML = `<div class="xcard"><p>この映像は X（旧ツイッター）にあります。</p>` +
      `<p class="muted">ログインを求められることがあります。</p>` +
      `<a class="btn primary" href="${F.esc(F.goHref(src.url))}">Xで見る</a></div>`;
  }

  function mountX(el, src) {
    el.innerHTML = `<blockquote class="twitter-tweet" data-lang="ja" data-dnt="true"><a href="${F.esc(src.url)}"></a></blockquote>`;
    const s = document.createElement("script");
    s.src = "https://platform.twitter.com/widgets.js";
    s.async = true;
    s.onerror = () => xFallback(el, src);
    document.body.appendChild(s);
    setTimeout(() => { if (!el.querySelector("iframe")) xFallback(el, src); }, 4000);
  }
})();
