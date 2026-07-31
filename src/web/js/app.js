// app.js — 載入課程資料、渲染、互動與進度追蹤
import { mountIcons, icon } from "./icons.js";
import {
  renderChapter, renderStance, renderHome, setDrillEvidence, setConfig, esc,
} from "./render.js";
import { renderMusclePanel, syncMuscleChips, applyFilters as runFilters } from "./filters.js";
import {
  buildPlaylist, renderPlaylist, playlistItemMatches, play, stop, fitFrame, watchFrame,
  initResizer, setLanguages,
} from "./player.js";
import { bindKeys, listen as ytListen } from "./keys.js";
import * as discuss from "./discuss.js";

let LESSON_NOUN = "堂主課";
let DRILL_NOUN = "支精選影片";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const STORE = {
  done: "susc:done",
  theme: "susc:theme",
  open: "susc:open",
  tab: "susc:tab",
  playing: "susc:playing",
  wide: "susc:wide",
  listW: "susc:listW",
};

/** playlist 的 url -> index，讓課程內容的影片連結能導向站內播放 */
const urlIndex = new Map();

const state = {
  course: null,
  done: new Set(),
  filter: "all",
  learningTier: "all",
  query: "",
  muscles: new Set(),
  tab: "course",
  playlist: [],
  playing: -1,
  playlistQuery: "",
  onlyTodo: false,
};

function courseReviewLabel(data) {
  const valid = new Set(["draft", "medical-review", "approved"]);
  const statuses = (data?.chapters || []).flatMap((ch) =>
    (ch.units || []).map((unit) =>
      valid.has(unit.review_status) ? unit.review_status : "draft",
    ),
  );
  if (!statuses.length) return "尚無審閱資料";
  if (statuses.every((status) => status === "approved")) return "內容已核准";
  if (statuses.some((status) => status === "draft")) return "含內容草稿";
  return "醫療審閱中";
}

/* --- 儲存 ---------------------------------------------------------------- */

function load(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function save(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* 隱私模式下寫入會失敗，靜默忽略 */
  }
}

/** 把 course.config.json 的文案寫進 header、Hero 與頁尾 */
function applyChrome(data) {
  const c = data.config || {};
  const site = c.site || {};
  const set = (sel, html) => {
    const el = $(sel);
    if (el && html != null) el.innerHTML = html;
  };

  document.title = site.title || site.name || document.title;
  document.documentElement.lang = site.locale || "zh-Hant";
  LESSON_NOUN = c.ui?.lessonNoun || LESSON_NOUN;
  DRILL_NOUN = c.ui?.drillNoun || DRILL_NOUN;
  set(".AppHeader__brandName", esc(site.name || ""));
  // brandIcon 由設定檔決定，index.html 裡的是換主題前的預設值
  if (site.brandIcon) {
    $(".AppHeader__brand use")?.setAttribute("href", `#i-${site.brandIcon}`);
  }

  // 篩選鈕跟著 kinds 走，換主題不用改 HTML
  const group = $(".FilterBar__group");
  if (group && c.kinds?.length) {
    group.innerHTML =
      `<button class="FilterBar__btn is-active" data-filter="all" type="button">${esc(c.ui?.filterAll || "全部")}</button>` +
      c.kinds
        .map(
          (k) =>
            `<button class="FilterBar__btn" data-filter="${esc(k.id)}" type="button">` +
            `<span class="Drill__marker" style="background:var(--fgColor-${esc(k.tone || "accent")})"></span>` +
            `${esc(k.label)}</button>`,
        )
        .join("");
  }
  $("#search")?.setAttribute("placeholder", c.ui?.searchPlaceholder || "搜尋…");
  set(".ProgressPanel__title", esc(c.ui?.progressLabel || ""));
  set("#muscleToggle span:first-of-type", esc(c.ui?.facetLabel || ""));

  for (const [key, label] of Object.entries(c.ui?.tabs || {})) {
    set(`.TabNav__item[data-tab="${key}"] .TabNav__label`, esc(label));
    $(`.TabNav__item[data-tab="${key}"]`)?.setAttribute("aria-label", label);
  }

  set(".Hero__eyebrow", `${$(".Hero__eyebrow svg")?.outerHTML || ""} ${esc(c.hero?.eyebrow || "")}`);
  set(".Hero h1", esc(c.hero?.heading || ""));
  set(
    ".Hero__lede",
    (c.hero?.lede || "")
      .replace("{units}", data.meta.units)
      .replace("{problems}", data.meta.problem_units),
  );
  set(".AppFooter__disclaimer", c.footer?.disclaimer || "");
  set(".AppFooter__credits", esc(c.footer?.credits || ""));
  set("#railChapterCount", `${data.chapters?.length || 0} CHAPTERS · ${data.meta?.units || 0} UNITS`);
  set("#consoleUnitCount", `${data.meta?.units || 0} UNITS`);
  set("#consoleVideoCount", `${data.meta?.video_unique || 0} VIDEOS`);
  const coreCount = data.meta?.drill_tier_counts?.core || 0;
  if (coreCount) set("#consoleVideoCount", `${data.meta?.video_unique || 0} VIDEOS · ${coreCount} CORE`);
  set("#consoleReviewStatus", esc(courseReviewLabel(data)));

  const coreToggle = $("#corePathToggle");
  const playlistCore = $("#playlistCoreOnly");
  if (coreToggle) {
    coreToggle.hidden = !coreCount;
    coreToggle.querySelector("span").textContent = `${c.ui?.coreOnlyLabel || "只看核心必看"} · ${coreCount}`;
  }
  if (playlistCore) playlistCore.hidden = !coreCount;
}

/* --- 瀏覽次數 -------------------------------------------------------------
   設定檔沒有 counter 區塊就整個不做。API 失敗（沒綁 D1、離線、本機預覽）
   就讓徽章維持隱藏——寧可沒有這個功能，也不要顯示一個壞掉的空殼。 */

async function renderHits(cfg) {
  const conf = cfg?.counter;
  if (!conf) return;

  const box = $("#hitCounter");
  if (!box) return;

  try {
    const res = await fetch("/api/hits", {
      method: "POST",
      headers: { "content-type": "application/json" },
      cache: "no-store",
    });
    if (!res.ok) return;
    const { hits } = await res.json();
    if (typeof hits !== "number") return;

    $("#hitCount").textContent = hits.toLocaleString();
    $("#hitLabel").textContent = conf.label || "";
    box.title = conf.title || "";
    box.hidden = false;
  } catch {
    /* 靜默失敗：計數器不該影響課程本身 */
  }
}

/* --- 統計 ---------------------------------------------------------------- */

function renderStats() {
  const { meta, config } = state.course;
  // 顯示哪些數字由 course.config.json 決定，全部是能從資料實際算出來的
  $("#heroStats").innerHTML = (config.ui?.stats || [])
    .map(
      (s) => `
        <div class="Stat">
          <span class="Stat__value">${icon(s.icon, 16)}<span>${esc(meta[s.field] ?? "")}</span></span>
          <span class="Stat__label">${esc(s.label)}</span>
        </div>`,
    )
    .join("");

  $("#heroNote").innerHTML =
    `${meta.lesson_units} ${LESSON_NOUN}，已建檔 ${meta.video_unique} 支不重複影片，` +
    `${meta.drill_tier_counts?.core || 0} 支核心必看、${meta.drill_tier_counts?.extension || 0} 支延伸學習，` +
    `影片總長 ${meta.duration}。課程狀態：${esc(courseReviewLabel(state.course))}。`;
}

/* --- 側欄 ---------------------------------------------------------------- */

function renderNav() {
  const groups = (state.course.config.nav || []).map((g) => ({
    title: g.title,
    codes: g.chapters,
  }));

  $("#nav").innerHTML = groups
    .map(
      (g) => `
      <div class="NavList__group-title">${g.title}</div>
      ${g.codes
        .map((code) => {
          const ch = state.course.chapters.find((c) => c.code === code);
          if (!ch) return "";
          const done = ch.units.filter((u) => state.done.has(u.id)).length;
          return `
            <a class="NavList__item" href="#${esc(code)}" data-nav="${esc(code)}">
              <span class="NavList__icon">${icon(ch.icon || "circle-dot", 16)}</span>
              <span class="NavList__main">
                <span class="NavList__code">${esc(code)}</span>
                <span class="NavList__label">${esc(ch.title)}</span>
              </span>
              <span class="Counter">${done}/${ch.units.length}</span>
            </a>`;
        })
        .join("")}`,
    )
    .join("");
}

/* --- 進度 ---------------------------------------------------------------- */

function totalUnits() {
  return state.course.chapters.reduce((n, c) => n + c.units.length, 0);
}

function renderProgress() {
  const total = totalUnits();
  const done = state.done.size;
  $("#progressValue").textContent = `${done} / ${total}`;
  $("#progressFill").style.width = total ? `${(done / total) * 100}%` : "0%";
}

function toggleDone(unitId) {
  state.done.has(unitId) ? state.done.delete(unitId) : state.done.add(unitId);
  save(STORE.done, [...state.done]);

  const el = $(`[data-unit="${CSS.escape(unitId)}"]`);
  if (el) {
    const done = state.done.has(unitId);
    el.classList.toggle("is-done", done);
    $(".Unit__check", el)?.setAttribute("aria-checked", String(done));
  }

  renderProgress();
  renderNav();
  updateChapterMeta();
}

function updateChapterMeta() {
  state.course.chapters.forEach((ch) => {
    const el = $(`[data-chapter="${CSS.escape(ch.code)}"]`);
    if (!el) return;
    const done = ch.units.filter((u) => state.done.has(u.id)).length;
    const pct = ch.units.length ? (done / ch.units.length) * 100 : 0;
    $(".Chapter__progress .ProgressBar__fill", el).style.width = `${pct}%`;
    const drillTotal = ch.units.reduce((n, u) => n + (u.drills?.length || 0), 0);
    $(".Chapter__meta", el).textContent =
      `${ch.units.length} 個單元${drillTotal ? ` · ${drillTotal} ${DRILL_NOUN}` : ""}${done ? ` · 已完成 ${done}` : ""}`;
  });
}

/* --- 搜尋與篩選（實作在 filters.js） -------------------------------------- */

function applyFilters() {
  runFilters(state, state.course);
  syncMuscleChips(state.muscles);
}

function syncTierControls() {
  const active = state.learningTier === "core";
  for (const el of [$("#corePathToggle"), $("#playlistCoreOnly")]) {
    if (!el) continue;
    el.classList.toggle("is-active", active);
    el.setAttribute("aria-pressed", String(active));
  }
}

function toggleCorePath() {
  state.learningTier = state.learningTier === "core" ? "all" : "core";
  syncTierControls();
  applyFilters();
  alignPlayingToVisible();
}

/* --- 分頁 ---------------------------------------------------------------- */

function setTab(tab) {
  state.tab = tab;
  save(STORE.tab, tab);
  document.body.dataset.tab = tab; // 給 CSS 用（上課模式要吃滿版、隱藏頁尾）

  $$(".TabNav__item").forEach((b) => {
    const on = b.dataset.tab === tab;
    b.classList.toggle("is-selected", on);
    on ? b.setAttribute("aria-current", "page") : b.removeAttribute("aria-current");
  });

  $("#view-home").hidden = tab !== "home";
  $("#main").hidden = tab !== "course";
  $("#view-stance").hidden = tab !== "stance";
  $("#view-player").hidden = tab !== "player";
  scrollTo({ top: 0 });

  if (tab === "player") {
    refreshPlaylist();
    requestAnimationFrame(fitFrame);
  }
  else stop(); // 離開上課模式就卸掉 iframe，不要背景播放
}

/* --- 上課模式 ------------------------------------------------------------ */

function playlistFilterState() {
  return {
    doneSet: state.done,
    query: state.playlistQuery,
    onlyTodo: state.onlyTodo,
    learningTier: state.learningTier,
  };
}

function refreshPlaylist() {
  renderPlaylist(state.playlist, {
    ...playlistFilterState(),
    currentIndex: state.playing,
  });
}

function alignPlayingToVisible() {
  const filters = playlistFilterState();
  const current = state.playlist[state.playing];
  if (current && playlistItemMatches(current, filters)) {
    refreshPlaylist();
    return;
  }

  const matches = state.playlist
    .map((item, i) => ({ item, i }))
    .filter(({ item }) => playlistItemMatches(item, filters));
  if (!matches.length) {
    refreshPlaylist();
    return;
  }

  const origin = state.playing >= 0 ? state.playing : 0;
  const next = matches.reduce((best, candidate) =>
    Math.abs(candidate.i - origin) < Math.abs(best.i - origin) ? candidate : best,
  ).i;

  if (state.tab === "player") {
    playAt(next);
  } else {
    state.playing = next;
    save(STORE.playing, next);
    refreshPlaylist();
  }
}

function playAt(i) {
  if (i < 0 || i >= state.playlist.length) return;
  state.playing = i;
  save(STORE.playing, i);
  play(state.playlist[i], { total: state.playlist.length });
  setTimeout(ytListen, 900); // iframe 載入後才收得到 infoDelivery
  if (load(STORE.wide, false)) {
    $(".Player").classList.add("is-wide");
    $("[data-list-label]").textContent = "顯示清單";
  }
  refreshPlaylist();
  $(".PlaylistItem.is-playing")?.scrollIntoView({ block: "nearest" });
}

function stepPlaylist(delta) {
  let i = state.playing;
  const filters = playlistFilterState();
  while (i + delta >= 0 && i + delta < state.playlist.length) {
    i += delta;
    if (playlistItemMatches(state.playlist[i], filters)) {
      playAt(i);
      return;
    }
  }
}

/* --- 事件 ---------------------------------------------------------------- */

function bindEvents() {
  // 分頁切換
  $$(".TabNav__item").forEach((b) =>
    b.addEventListener("click", () => setTab(b.dataset.tab)),
  );

  // 品牌與首頁上的按鈕都走同一個入口
  document.addEventListener("click", (e) => {
    const link = e.target.closest("[data-tab-link]");
    if (link) {
      e.preventDefault();
      return setTab(link.dataset.tabLink);
    }
    const goCh = e.target.closest("[data-goto-chapter]");
    if (goCh) {
      setTab("course");
      const el = $(`[data-chapter="${CSS.escape(goCh.dataset.gotoChapter)}"]`);
      el?.classList.add("is-open");
      el?.scrollIntoView({ block: "start" });
    }
  });

  // 肌群篩選：側欄 chip 與動作內的標籤共用同一組 data-muscle
  document.addEventListener("click", (e) => {
    const chip = e.target.closest("[data-muscle]");
    if (!chip) return;
    e.preventDefault();
    e.stopPropagation();
    const m = chip.dataset.muscle;
    state.muscles.has(m) ? state.muscles.delete(m) : state.muscles.add(m);
    if (state.tab !== "course") setTab("course");
    applyFilters();
  });

  $("#muscleToggle")?.addEventListener("click", () =>
    $("#musclePanel").classList.toggle("is-open"),
  );

  $("#muscleBody")?.addEventListener("click", (e) => {
    if (!e.target.closest("#muscleClear")) return;
    state.muscles.clear();
    applyFilters();
  });

  // 播放清單
  $("#playlist").addEventListener("click", (e) => {
    const item = e.target.closest("[data-play]");
    if (item) playAt(+item.dataset.play);
  });

  $("#playerInfo").addEventListener("click", (e) => {
    const step = e.target.closest("[data-step]");
    if (step) return stepPlaylist(+step.dataset.step);

    const mark = e.target.closest("[data-mark-unit]");
    if (mark) {
      toggleDone(mark.dataset.markUnit);
      refreshPlaylist();
      return;
    }

    const wide = e.target.closest("[data-toggle-list]");
    if (wide) {
      const on = $(".Player").classList.toggle("is-wide");
      save(STORE.wide, on);
      $("[data-list-label]").textContent = on ? "顯示清單" : "收起清單";
      requestAnimationFrame(fitFrame);
      return;
    }

    const disc = e.target.closest("[data-toggle-discuss]");
    if (disc) {
      const panel = $("#discussPanel");
      panel.hidden = !panel.hidden;
      if (!panel.hidden) {
        discuss.mount(state.playlist[state.playing]);
        panel.scrollIntoView({ block: "nearest" });
      } else {
        discuss.close();
      }
      requestAnimationFrame(fitFrame);
      return;
    }

    const goto = e.target.closest("[data-goto-unit]");
    if (goto) {
      e.preventDefault();
      setTab("course");
      const el = $(`[data-unit="${CSS.escape(goto.dataset.gotoUnit)}"]`);
      el?.classList.add("is-open");
      el?.closest(".Chapter")?.classList.add("is-open");
      el?.scrollIntoView({ block: "center" });
    }
  });

  let plDebounce;
  $("#playlistSearch").addEventListener("input", (e) => {
    state.playlistQuery = e.target.value;
    clearTimeout(plDebounce);
    plDebounce = setTimeout(refreshPlaylist, 120);
  });

  $("#playlistOnlyTodo").addEventListener("click", (e) => {
    state.onlyTodo = !state.onlyTodo;
    e.currentTarget.classList.toggle("is-active", state.onlyTodo);
    refreshPlaylist();
  });

  $("#corePathToggle")?.addEventListener("click", toggleCorePath);
  $("#playlistCoreOnly")?.addEventListener("click", toggleCorePath);

  // 課程內容裡點影片 → 切到上課模式站內播放，而不是跳去 YouTube。
  // 按住 ⌘/Ctrl/Shift 或中鍵時尊重瀏覽器原本行為（開新分頁）。
  $("#chapters").addEventListener("click", (e) => {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    const link = e.target.closest('a[href*="youtube.com"], a[href*="youtu.be"]');
    if (!link) return;
    const i = urlIndex.get(link.href);
    if (i == null) return; // 不在播放清單裡就讓它正常開連結
    e.preventDefault();
    setTab("player");
    playAt(i);
  });

  // 主課語言切換
  $("#chapters").addEventListener("click", (e) => {
    const langBtn = e.target.closest("[data-lesson]");
    if (!langBtn) return;
    e.preventDefault();
    e.stopPropagation();
    const box = langBtn.closest(".LessonBox");
    const i = langBtn.dataset.lesson;
    $$(".LessonBox__lang", box).forEach((b) => {
      const on = b === langBtn;
      b.classList.toggle("is-active", on);
      b.setAttribute("aria-selected", String(on));
    });
    $$("[data-lesson-pane]", box).forEach((p) => {
      p.hidden = p.dataset.lessonPane !== i;
    });
  });

  // 展開／收合 + 完成標記，統一走事件委派
  $("#chapters").addEventListener("click", (e) => {
    const check = e.target.closest('[data-action="toggle-done"]');
    if (check) {
      e.stopPropagation();
      toggleDone(check.closest(".Unit").dataset.unit);
      return;
    }

    const toggle = e.target.closest("[data-toggle]");
    if (!toggle) return;

    const kind = toggle.dataset.toggle;
    const host =
      kind === "chapter"
        ? toggle.closest(".Chapter")
        : kind === "unit"
          ? toggle.closest(".Unit")
          : toggle.closest(".Evidence"); // evidence 與 drillev 共用 .Evidence 外框
    host.classList.toggle("is-open");
  });

  // 完成標記的鍵盤操作
  $("#chapters").addEventListener("keydown", (e) => {
    if (e.key !== " " && e.key !== "Enter") return;
    const check = e.target.closest('[data-action="toggle-done"]');
    if (!check) return;
    e.preventDefault();
    e.stopPropagation();
    toggleDone(check.closest(".Unit").dataset.unit);
  });

  // 搜尋
  const searchInput = $("#search");
  let debounce;
  searchInput.addEventListener("input", () => {
    state.query = searchInput.value;
    $("#searchBox").classList.toggle("has-value", !!state.query);
    clearTimeout(debounce);
    debounce = setTimeout(applyFilters, 120);
  });

  $("#searchClear").addEventListener("click", () => {
    searchInput.value = "";
    state.query = "";
    $("#searchBox").classList.remove("has-value");
    applyFilters();
    searchInput.focus();
  });

  // "/" 聚焦搜尋
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && !/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)) {
      e.preventDefault();
      searchInput.focus();
    }
    if (e.key === "Escape" && document.activeElement === searchInput) {
      searchInput.blur();
    }
  });

  // 類型篩選
  $$(".FilterBar__btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      $$(".FilterBar__btn").forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      state.filter = btn.dataset.filter;
      applyFilters();
    });
  });

  // 全部展開／收合
  $("#expandAll").addEventListener("click", () => {
    const anyClosed = $$(".Chapter").some((c) => !c.classList.contains("is-open"));
    $$(".Chapter").forEach((c) => c.classList.toggle("is-open", anyClosed));
    save(STORE.open, anyClosed);
  });

  // 重設進度
  $("#resetProgress").addEventListener("click", () => {
    if (!state.done.size) return;
    if (!confirm(`確定要清除 ${state.done.size} 個單元的完成紀錄嗎？`)) return;
    state.done.clear();
    save(STORE.done, []);
    $$(".Unit").forEach((u) => {
      u.classList.remove("is-done");
      $(".Unit__check", u)?.setAttribute("aria-checked", "false");
    });
    renderProgress();
    renderNav();
    updateChapterMeta();
  });

  // 主題
  $("#themeToggle").addEventListener("click", () => {
    const current =
      document.documentElement.dataset.theme ||
      (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    save(STORE.theme, next);
    syncThemeIcon();
    discuss.syncTheme();
  });

  // 點側欄章節：讓對應的卡片閃一下描邊。
  // 大螢幕上整份大綱一眼看完，單純捲動等於沒有回饋，所以要指出「是這一張」。
  // 用事件委派，因為 renderNav() 會整個重畫 #nav 的 innerHTML。
  let flashTimer;
  $("#nav")?.addEventListener("click", (e) => {
    const link = e.target.closest("[data-nav]");
    if (!link) return;
    const card = $(`.Chapter[data-chapter="${CSS.escape(link.dataset.nav)}"]`);
    if (!card) return;

    clearTimeout(flashTimer);
    $$(".Chapter--flash").forEach((c) => c.classList.remove("Chapter--flash"));
    void card.offsetWidth; // 強制重排，連點同一章才會重新播放動畫
    card.classList.add("Chapter--flash");
    flashTimer = setTimeout(() => card.classList.remove("Chapter--flash"), 1150);
  });

  // 側欄高亮
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const code = entry.target.dataset.chapter;
        $$("[data-nav]").forEach((a) =>
          a.classList.toggle("is-active", a.dataset.nav === code),
        );
      });
    },
    { rootMargin: "-72px 0px -70% 0px" },
  );
  $$(".Chapter").forEach((c) => observer.observe(c));
}

function syncThemeIcon() {
  const dark =
    (document.documentElement.dataset.theme ||
      (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")) === "dark";
  $("#themeToggle svg use").setAttribute("href", dark ? "#i-moon" : "#i-sun");
}

/* --- 啟動 ---------------------------------------------------------------- */

async function init() {
  mountIcons();
  syncThemeIcon();

  let data;
  try {
    const res = await fetch("course.json");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    $("#chapters").innerHTML = `
      <div class="Blankslate">
        ${icon("triangle-alert", 32)}
        <p class="Blankslate__heading">課程資料載入失敗</p>
        <p>${esc(err.message)}</p>
      </div>`;
    return;
  }

  state.course = data;
  state.done = new Set(load(STORE.done, []));

  setConfig(data.config);
  setLanguages(data.config?.languages);
  discuss.setDiscussions(data.config?.discussions);
  applyChrome(data);
  renderHits(data.config); // 不 await，取數慢不該擋住畫面
  setDrillEvidence(data.drillEvidence);

  $("#chapters").innerHTML = data.chapters
    .map((ch) => renderChapter(ch, state.done))
    .join("");

  const stanceEl = $("#view-stance");
  if (data.stance?.length) {
    stanceEl.innerHTML = renderStance(data.stance);
    $("#tabStanceCount").textContent = data.stance.length;
  } else {
    stanceEl.remove();
    $('.TabNav__item[data-tab="stance"]')?.remove();
  }

  $("#tabCourseCount").textContent = data.meta.units;

  state.playlist = buildPlaylist(data);
  state.playlist.forEach((it, i) => urlIndex.set(it.url, i));
  state.playing = load(STORE.playing, -1);

  $("#landingBody").innerHTML = renderHome(data);
  renderStats();
  renderNav();
  renderMusclePanel(data);
  renderProgress();
  bindEvents();
  watchFrame();
  initResizer(load(STORE.listW, 0), (w) => save(STORE.listW, w));
  bindKeys({
    next: () => {
      if (state.tab !== "player") setTab("player");
      stepPlaylist(1);
    },
    prev: () => {
      if (state.tab !== "player") setTab("player");
      stepPlaylist(-1);
    },
    isPlayerTab: () => state.tab === "player",
  });
  applyFilters();
  syncTierControls();

  // ?tab=player&play=12 可直接開到指定分頁與影片，也方便分享連結
  const params = new URLSearchParams(location.search);
  const wanted = params.get("tab");
  setTab(
    ["home", "course", "player", "stance"].includes(wanted)
      ? wanted
      : load(STORE.tab, "home"),
  );

  const deepPlay = Number(params.get("play"));
  if (state.tab === "player" && Number.isInteger(deepPlay) && state.playlist[deepPlay]) {
    state.playing = deepPlay;
  }
  // 還原上次看到哪，但不自動播放，回來時先看到資訊就好
  if (state.tab === "player" && state.playlist[state.playing]) {
    playAt(state.playing);
  }

  // 首次造訪展開觀念篇第一章，讓畫面不是一片收合
  if (load(STORE.open, null) === null) {
    $('[data-chapter="CH0"]')?.classList.add("is-open");
  }

  // 深連結：#ch5-u1 直接展開該單元
  if (location.hash) {
    const target = $(CSS.escape(location.hash.slice(1)) ? location.hash : "");
    if (target?.classList.contains("Unit")) {
      target.classList.add("is-open");
      target.closest(".Chapter")?.classList.add("is-open");
      target.scrollIntoView({ block: "center" });
    } else if (target?.classList.contains("Chapter")) {
      target.classList.add("is-open");
    }
  }
}

init();
