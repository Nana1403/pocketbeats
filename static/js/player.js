/* PocketBeats player engine
 * Drives the HTML5 <audio> element from the custom device controls.
 */
(function () {
  "use strict";

  const device = document.getElementById("player");
  if (!device) return;

  const audio = document.getElementById("audio");
  const cfg = device.dataset;
  const isAuthed = cfg.authenticated === "true";

  // --- Element handles ---
  const el = {
    disc: document.getElementById("disc"),
    discArt: document.getElementById("discArt"),
    title: document.getElementById("trackTitle"),
    artist: document.getElementById("trackArtist"),
    meta: document.getElementById("trackMeta"),
    seek: document.getElementById("seek"),
    timeCurrent: document.getElementById("timeCurrent"),
    timeTotal: document.getElementById("timeTotal"),
    play: document.getElementById("playBtn"),
    prev: document.getElementById("prevBtn"),
    next: document.getElementById("nextBtn"),
    restart: document.getElementById("restartBtn"),
    shuffle: document.getElementById("shuffleBtn"),
    repeat: document.getElementById("repeatBtn"),
    fav: document.getElementById("favBtn"),
    mute: document.getElementById("muteBtn"),
    volume: document.getElementById("volume"),
    drawerToggle: document.getElementById("drawerToggle"),
    drawer: document.getElementById("drawer"),
    queue: document.getElementById("queue"),
    queueSearch: document.getElementById("queueSearch"),
    tabs: document.querySelectorAll(".tab"),
  };

  // --- State ---
  let songs = [];        // full loaded list
  let view = [];         // filtered/ordered view used for playback
  let current = -1;      // index into `view`
  let shuffle = false;
  let repeat = "off";    // off | all | one
  let source = "library";
  let seeking = false;

  // --- Helpers ---
  function fmt(seconds) {
    seconds = Math.max(0, Math.floor(seconds || 0));
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  function getCookie(name) {
    const match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return match ? match.pop() : "";
  }

  function postJSON(url, body) {
    return fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify(body || {}),
    });
  }

  // --- Rendering ---
  function renderScreen(song) {
    if (!song) {
      el.title.textContent = "No track loaded";
      el.artist.textContent = "—";
      el.meta.textContent = "";
      el.discArt.style.backgroundImage = "";
      return;
    }
    el.title.textContent = song.title;
    el.artist.textContent = song.artist || "Unknown artist";
    el.meta.textContent = [song.album, song.genre].filter(Boolean).join(" · ");
    el.discArt.style.backgroundImage = song.coverUrl ? `url("${song.coverUrl}")` : "";
    updateFavButton(song);
  }

  function updateFavButton(song) {
    const on = !!(song && song.isFavorite);
    el.fav.setAttribute("aria-pressed", on ? "true" : "false");
    el.fav.textContent = on ? "❤️ Favorite" : "🤍 Favorite";
    el.fav.disabled = !isAuthed;
  }

  function renderQueue() {
    el.queue.innerHTML = "";
    const term = (el.queueSearch.value || "").toLowerCase();
    const items = view.filter((s) =>
      !term ||
      [s.title, s.artist, s.album, s.genre]
        .filter(Boolean)
        .some((f) => f.toLowerCase().includes(term))
    );
    if (!items.length) {
      const li = document.createElement("li");
      li.className = "queue-empty";
      li.textContent = isAuthed ? "No songs yet — upload some music!" : "Sample track only.";
      el.queue.appendChild(li);
      return;
    }
    items.forEach((song) => {
      const idx = view.indexOf(song);
      const li = document.createElement("li");
      li.className = "queue-item" + (idx === current ? " active" : "");
      const thumb = document.createElement("div");
      thumb.className = "queue-thumb";
      if (song.coverUrl) thumb.style.backgroundImage = `url("${song.coverUrl}")`;
      const text = document.createElement("div");
      text.className = "queue-text";
      text.innerHTML = `<div class="t"></div><div class="a"></div>`;
      text.querySelector(".t").textContent = song.title;
      text.querySelector(".a").textContent = song.artist || "Unknown artist";
      const dur = document.createElement("span");
      dur.className = "queue-dur";
      dur.textContent = song.durationDisplay || fmt(song.duration);
      li.append(thumb, text, dur);
      li.addEventListener("click", () => loadAndPlay(idx));
      el.queue.appendChild(li);
    });
  }

  // --- Playback ---
  function loadAndPlay(index, autoplay = true) {
    if (index < 0 || index >= view.length) return;
    current = index;
    const song = view[current];
    audio.src = song.audioUrl;
    renderScreen(song);
    renderQueue();
    if (autoplay) {
      audio.play().catch(() => {/* autoplay may be blocked until interaction */});
    }
  }

  function togglePlay() {
    if (!audio.src) {
      if (view.length) loadAndPlay(0);
      return;
    }
    if (audio.paused) audio.play(); else audio.pause();
  }

  function nextIndex() {
    if (!view.length) return -1;
    if (shuffle) {
      if (view.length === 1) return current;
      let n;
      do { n = Math.floor(Math.random() * view.length); } while (n === current);
      return n;
    }
    if (current + 1 < view.length) return current + 1;
    return repeat === "all" ? 0 : -1;
  }

  function playNext() {
    const n = nextIndex();
    if (n === -1) { audio.pause(); return; }
    loadAndPlay(n);
  }

  function playPrev() {
    if (audio.currentTime > 3) { audio.currentTime = 0; return; }
    if (current > 0) loadAndPlay(current - 1);
    else audio.currentTime = 0;
  }

  // --- Audio events ---
  audio.addEventListener("play", () => {
    device.classList.add("playing");
    el.play.textContent = "⏸";
  });
  audio.addEventListener("pause", () => {
    device.classList.remove("playing");
    el.play.textContent = "▶";
    recordPlay();
  });
  audio.addEventListener("loadedmetadata", () => {
    el.timeTotal.textContent = fmt(audio.duration);
  });
  audio.addEventListener("timeupdate", () => {
    if (!seeking) {
      const pct = audio.duration ? (audio.currentTime / audio.duration) * 1000 : 0;
      el.seek.value = pct;
    }
    el.timeCurrent.textContent = fmt(audio.currentTime);
  });
  audio.addEventListener("ended", () => {
    recordPlay();
    if (repeat === "one") { audio.currentTime = 0; audio.play(); return; }
    playNext();
  });

  function recordPlay() {
    if (!isAuthed || current < 0) return;
    const song = view[current];
    if (!song || !song.id) return;
    postJSON(cfg.playUrl + song.id + "/", {
      position: Math.floor(audio.currentTime || 0),
    }).catch(() => {});
  }

  // --- Control wiring ---
  el.play.addEventListener("click", togglePlay);
  el.next.addEventListener("click", playNext);
  el.prev.addEventListener("click", playPrev);
  el.restart.addEventListener("click", () => { audio.currentTime = 0; audio.play(); });

  el.seek.addEventListener("input", () => { seeking = true; });
  el.seek.addEventListener("change", () => {
    if (audio.duration) audio.currentTime = (el.seek.value / 1000) * audio.duration;
    seeking = false;
  });

  el.volume.addEventListener("input", () => {
    audio.volume = parseFloat(el.volume.value);
    audio.muted = false;
    syncMute();
  });
  function syncMute() {
    const muted = audio.muted || audio.volume === 0;
    el.mute.setAttribute("aria-pressed", muted ? "true" : "false");
    el.mute.textContent = muted ? "🔈" : "🔊";
  }
  el.mute.addEventListener("click", () => { audio.muted = !audio.muted; syncMute(); });

  el.shuffle.addEventListener("click", () => {
    shuffle = !shuffle;
    el.shuffle.setAttribute("aria-pressed", shuffle ? "true" : "false");
  });

  el.repeat.addEventListener("click", () => {
    repeat = repeat === "off" ? "all" : repeat === "all" ? "one" : "off";
    el.repeat.setAttribute("aria-pressed", repeat === "off" ? "false" : "true");
    el.repeat.textContent =
      repeat === "off" ? "🔁 Off" : repeat === "all" ? "🔁 All" : "🔂 One";
  });

  el.fav.addEventListener("click", () => {
    if (!isAuthed || current < 0) return;
    const song = view[current];
    postJSON(cfg.favoriteUrl + song.id + "/", {})
      .then((r) => r.json())
      .then((data) => { song.isFavorite = data.isFavorite; updateFavButton(song); })
      .catch(() => {});
  });

  el.drawerToggle.addEventListener("click", () => {
    const open = el.drawer.classList.toggle("open");
    el.drawerToggle.setAttribute("aria-expanded", open ? "true" : "false");
  });

  el.queueSearch.addEventListener("input", renderQueue);

  el.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      el.tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      source = tab.dataset.source;
      loadSongs();
    });
  });

  // Keyboard: space toggles play when not typing in a field.
  document.addEventListener("keydown", (e) => {
    if (e.code === "Space" && !/input|textarea|button/i.test(e.target.tagName)) {
      e.preventDefault();
      togglePlay();
    }
  });

  // --- Data loading ---
  function applySongs(list) {
    songs = list || [];
    view = songs.slice();
    current = -1;
    renderQueue();
    if (view.length) {
      loadAndPlay(0, false); // load first track without autoplaying
    } else {
      renderScreen(null);
    }
  }

  function loadSongs() {
    if (!isAuthed) {
      applySongs([{
        id: null,
        title: "PocketBeats Sample",
        artist: "Demo",
        album: "Getting Started",
        genre: "",
        duration: 0,
        durationDisplay: "0:00",
        audioUrl: cfg.sampleUrl,
        coverUrl: cfg.sampleCover,
        isFavorite: false,
      }]);
      return;
    }
    const url = source === "favorites" ? cfg.favoritesUrl : cfg.libraryUrl;
    fetch(url)
      .then((r) => r.json())
      .then((data) => applySongs(data.songs))
      .catch(() => applySongs([]));
  }

  // --- Init ---
  audio.volume = parseFloat(el.volume.value);
  syncMute();
  loadSongs();
})();
