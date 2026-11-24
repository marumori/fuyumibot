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

  /* A playlist of any platform. YouTube clips advance by themselves; for Bilibili/X the viewer taps 「次の曲へ」.
     A YouTube first clip is loaded (not started) on page load so the tap can call playVideo() synchronously —
     iOS only allows sound when play starts inside the tap itself. */
  F.mountQueue = (el, cards) => {
    const list = (cards || []).filter((c) => c.source);
    el.innerHTML = "";
    if (!list.length) return;
    let i = 0, player = null, ready = false, wantPlay = false, started = false;
    el.innerHTML = `<div class="stage"></div><p class="now" aria-live="polite"></p>` +
      `<button class="btn primary" type="button" data-act="play">▶ ${list.length}曲つづけて聴く</button>` +
      `<button class="btn" type="button" data-act="next" hidden>次の曲へ ▶</button>`;
    const stage = el.querySelector(".stage"), now = el.querySelector(".now");
    const isYT = (c) => c.source.platform === "youtube";
    const showNow = () => { now.textContent = `いま：${list[i].title_label}（${i + 1}/${list.length}）`; };
    const ytInto = (id, autoplay) => {
      stage.innerHTML = `<div class="player"><div></div></div>`;
      ready = false; wantPlay = autoplay;
      return loadYT().then(() => {
        player = new YT.Player(stage.querySelector(".player > div"), {
          videoId: id, playerVars: { playsinline: 1, rel: 0 },
          events: {
            onReady: () => { ready = true; if (wantPlay) player.playVideo(); },
            onStateChange: (e) => { if (e.data === YT.PlayerState.ENDED) next(); },
          },
        });
      });
    };
    const show = (autoplay) => {
      const c = list[i];
      if (isYT(c)) {
        if (player && ready && stage.querySelector(".player")) { player.loadVideoById(c.source.id); }
        else ytInto(c.source.id, autoplay);
      } else {
        if (player && player.destroy) player.destroy();
        player = null; ready = false;
        F.mountSingle(stage, c.source);
      }
    };
    function next() {
      if (i + 1 >= list.length) { now.textContent = "最後まで聴きました。"; return; }
      i++; showNow(); show(true);
    }
    show(false);
    el.querySelector('[data-act="play"]').addEventListener("click", () => {
      showNow();
      el.querySelector('[data-act="next"]').hidden = false;
      if (!started && isYT(list[i])) { if (ready) player.playVideo(); else wantPlay = true; }
      started = true;
    });
    el.querySelector('[data-act="next"]').addEventListener("click", next);
  };
  F.mountYouTubeQueue = F.mountQueue;

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
