// app.js — 載入課程資料、渲染、互動與進度追蹤
import { mountIcons, icon } from "./icons.js";
import {
  renderChapter, renderHome, setDrillEvidence, setConfig, esc,
} from "./render.js";
import { renderMusclePanel, syncMuscleChips, applyFilters as runFilters } from "./filters.js";
import {
  buildPlaylist, renderPlaylist, playlistItemMatches, play, stop, fitFrame, watchFrame,
  initResizer, setLanguages,
  refreshSegments, seekTo,
} from "./player.js";
import { bindKeys, listen as ytListen } from "./keys.js";
import { mountPictograms } from "./pictograms.js";
import * as discuss from "./discuss.js";

let LESSON_NOUN = "堂主課";
let DRILL_NOUN = "支精選影片";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const STORE = {
  done: "susc:done",
  mastery: "susc:mastery",
  masteryRestore: "susc:mastery-restore",
  quiz: "susc:quiz",
  theme: "susc:theme",
  open: "susc:open",
  tab: "susc:tab",
  playing: "susc:playing",
  lastUnit: "susc:lastUnit",
  wide: "susc:wide",
  listW: "susc:listW",
};

/** playlist 的 url -> index，讓課程內容的影片連結能導向站內播放 */
const urlIndex = new Map();

const state = {
  course: null,
  done: new Set(),
  mastery: new Map(),
  masteryRestore: {},
  quiz: {},
  filter: "all",
  learningTier: "all",
  query: "",
  searchTerms: [],
  muscles: new Set(),
  tab: "course",
  playlist: [],
  playing: -1,
  lastUnit: null,
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

const MASTERY = {
  "not-started": { icon: "circle-dot", label: "未開始" },
  learning: { icon: "book-open", label: "學習中" },
  done: { icon: "check", label: "已完成" },
  review: { icon: "triangle-alert", label: "待複習" },
};

function masteryOf(unitId) {
  return state.mastery.get(unitId) || "not-started";
}

function saveMastery() {
  save(STORE.mastery, Object.fromEntries(state.mastery));
}

function applyMasteryToUnit(unitId) {
  const el = $(`[data-unit="${CSS.escape(unitId)}"]`);
  if (!el) return;

  const status = masteryOf(unitId);
  const view = MASTERY[status];
  for (const key of Object.keys(MASTERY)) el.classList.toggle(`is-${key}`, key === status);
  const control = $(".Unit__check", el);
  if (!control) return;
  control.innerHTML = `${icon(view.icon, 13)}<span class="Unit__checkLabel">${view.label}</span>`;
  control.setAttribute("aria-checked", String(status === "done"));
  control.setAttribute("aria-label", `掌握度：${view.label}`);
  control.title = `掌握度：${view.label}`;
}

function setMastery(unitId, status) {
  if (!MASTERY[status] || masteryOf(unitId) === status) return;
  if (status === "not-started") state.mastery.delete(unitId);
  else state.mastery.set(unitId, status);

  if (status === "done") state.done.add(unitId);
  else state.done.delete(unitId);
  saveMastery();
  applyMasteryToUnit(unitId);
  renderProgress();
  renderNav();
  updateChapterMeta();
  renderLanding();
}

function markLearning(unitId) {
  if (masteryOf(unitId) === "not-started") setMastery(unitId, "learning");
}

function loadLearningState(data) {
  const unitIds = new Set(data.chapters.flatMap((chapter) => chapter.units.map((unit) => unit.id)));
  const storedMastery = load(STORE.mastery, null);
  const source =
    storedMastery && typeof storedMastery === "object" && !Array.isArray(storedMastery)
      ? storedMastery
      : null;

  state.mastery = new Map();
  if (source) {
    for (const [unitId, status] of Object.entries(source)) {
      if (unitIds.has(unitId) && MASTERY[status] && status !== "not-started") {
        state.mastery.set(unitId, status);
      }
    }
  } else {
    // 舊版只有完成 Set；mastery key 一旦寫入，後續啟動就不再讀取舊資料。
    const legacyDone = load(STORE.done, []);
    for (const unitId of Array.isArray(legacyDone) ? legacyDone : []) {
      if (unitIds.has(unitId)) state.mastery.set(unitId, "done");
    }
    saveMastery();
  }
  state.done = new Set(
    [...state.mastery].filter(([, status]) => status === "done").map(([unitId]) => unitId),
  );

  const storedRestore = load(STORE.masteryRestore, {});
  state.masteryRestore =
    storedRestore && typeof storedRestore === "object" && !Array.isArray(storedRestore)
      ? Object.fromEntries(
          Object.entries(storedRestore).filter(
            ([unitId, status]) => unitIds.has(unitId) && ["learning", "done"].includes(status),
          ),
        )
      : {};

  const questionIds = new Set(
    data.chapters.flatMap((chapter) =>
      chapter.units.flatMap((unit) => (unit.questions || []).map((question) => question.id)),
    ),
  );
  const storedQuiz = load(STORE.quiz, {});
  state.quiz =
    storedQuiz && typeof storedQuiz === "object" && !Array.isArray(storedQuiz)
      ? Object.fromEntries(
          Object.entries(storedQuiz).filter(
            ([questionId, record]) => questionIds.has(questionId) && Array.isArray(record?.answered),
          ),
        )
      : {};
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
  document.documentElement.lang = site.locale || "zh-Hant-TW";
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
      `<button class="FilterBar__btn is-active" data-filter="all" type="button" aria-pressed="true">${esc(c.ui?.filterAll || "全部")}</button>` +
      c.kinds
        .map(
          (k) =>
            `<button class="FilterBar__btn" data-filter="${esc(k.id)}" type="button" aria-pressed="false">` +
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
  // author 含使用者自訂連結，與 disclaimer 同樣以原樣注入（來源是自家設定檔）
  set("#headerAuthor", c.footer?.author || "");
  set(".AppFooter__credits", esc(c.footer?.credits || ""));
  set("#railChapterCount", `${data.chapters?.length || 0} CHAPTERS · ${data.meta?.units || 0} UNITS`);
  set("#consoleUnitCount", `${data.meta?.units || 0} UNITS`);
  set("#consoleVideoCount", `${data.meta?.video_unique || 0} VIDEOS`);
  const coreCount = data.meta?.drill_tier_counts?.core || 0;
  if (coreCount) set("#consoleVideoCount", `${data.meta?.video_unique || 0} VIDEOS · ${coreCount} CORE`);
  set("#consoleReviewStatus", esc(courseReviewLabel(data)));
  set("#pathwayStatus", esc(courseReviewLabel(data)));
  if (data.advanced?.status === "approved") {
    const workshop = data.advanced;
    const section = document.createElement("section");
    section.className = "AdvancedEntry container";
    section.id = "advancedEntry";
    section.innerHTML = `<h2>進階判讀與報告練習</h2><p>${workshop.units.length} 個進階單元 · ${workshop.questions} 題附解析知識題 · ${workshop.cases} 個判讀與報告練習</p><p><a class="btn" href="${esc(workshop.url)}">進入進階工作坊</a></p><div class="AdvancedEntry__units">${workshop.units.map(unit => `<a href="${esc(unit.url)}"><strong>${esc(unit.title)}</strong><span>${esc(unit.summary)}</span></a>`).join("")}</div><p class="AdvancedEntry__note">本批策展審閱通過；公開圖例與虛構情境分別標示，自我評量不等於臨床能力認證。</p>`;
    document.querySelector("#landingBody").before(section);
    const courseEntry = section.cloneNode(true);
    courseEntry.id = "advancedCourseEntry";
    document.querySelector("#chapters").before(courseEntry);
  }
  set("#heroPathways", (c.nav || []).map((group) => {
    const chapters = data.chapters.filter((ch) => group.chapters.includes(ch.code));
    const units = chapters.flatMap((ch) => ch.units);
    const videos = units.flatMap((unit) => unit.drills || []);
    return chapters.length ? `<button class="Pathway" type="button" data-goto-chapter="${esc(chapters[0].code)}">
      <span class="Pathway__code">${esc(chapters[0].code.replace(/\d+$/, ""))}</span>
      <span class="Pathway__body"><strong>${esc(group.title)}</strong>
        <small>${chapters.length} 章 · ${units.length} 單元 · ${videos.length} 支影片</small></span>
      ${icon("chevron-right", 18)}</button>` : "";
  }).join(""));
  const checklist = $(".Hero__actions a[href='checklist.html']");
  if (checklist && !data.chapters.some((ch) => ch.units.some((unit) => unit.review_status === "approved"))) {
    checklist.replaceWith(Object.assign(document.createElement("span"), {
      className: "Hero__reviewNote", textContent: "判讀檢核表：待內容審閱後開放",
    }));
  }

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

function renderLanding() {
  if (!state.course) return;
  $("#landingBody").innerHTML = renderHome(state.course, {
    doneSet: state.done,
    lastUnit: state.lastUnit,
  });
}

function rememberUnit(unitId) {
  if (!state.course.chapters.some((ch) => ch.units.some((unit) => unit.id === unitId))) {
    return;
  }
  state.lastUnit = { id: unitId, timestamp: Date.now() };
  save(STORE.lastUnit, state.lastUnit);
  renderLanding();
}

function toggleDone(unitId) {
  const current = masteryOf(unitId);
  if (current === "review") {
    const el = $(`[data-unit="${CSS.escape(unitId)}"]`);
    el?.classList.add("is-open");
    $(".Quiz", el)?.scrollIntoView({ block: "center" });
    return;
  }

  rememberUnit(unitId);
  setMastery(unitId, current === "done" ? "learning" : "done");
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

/* --- 知識檢核 ------------------------------------------------------------ */

function questionsForUnit(unitId) {
  for (const chapter of state.course.chapters) {
    const unit = chapter.units.find((item) => item.id === unitId);
    if (unit) return Array.isArray(unit.questions) ? unit.questions : [];
  }
  return [];
}

function answeredIndexes(questionEl) {
  return $$('input[type="radio"], input[type="checkbox"]', questionEl)
    .filter((input) => input.checked)
    .map((input) => Number(input.value))
    .filter(Number.isInteger)
    .sort((a, b) => a - b);
}

function answerIsCorrect(question, answered) {
  const expected = (question.options || [])
    .map((option, index) => (option.correct ? index : -1))
    .filter((index) => index >= 0);
  return expected.length === answered.length && expected.every((index, i) => index === answered[i]);
}

function gradeQuiz(form, questions, records) {
  let score = 0;
  form.classList.add("is-graded");

  for (const question of questions) {
    const questionEl = $(`[data-question="${CSS.escape(question.id)}"]`, form);
    if (!questionEl) continue;
    const answered = new Set(records[question.id]?.answered || []);
    const correct = answerIsCorrect(question, [...answered].sort((a, b) => a - b));
    if (correct) score++;
    questionEl.classList.toggle("is-correct", correct);
    questionEl.classList.toggle("is-incorrect", !correct);
    questionEl.classList.remove("needs-answer");

    $$("input", questionEl).forEach((input) => {
      const optionIndex = Number(input.value);
      input.checked = answered.has(optionIndex);
      input.disabled = true;
      const optionEl = input.closest(".QuizOption");
      optionEl?.classList.toggle("is-correct", question.options?.[optionIndex]?.correct === true);
      optionEl?.classList.toggle(
        "is-incorrect",
        answered.has(optionIndex) && question.options?.[optionIndex]?.correct !== true,
      );
    });
  }

  $('[data-action="submit-quiz"]', form).hidden = true;
  $('[data-action="retry-quiz"]', form).hidden = false;
  $(".Quiz__result", form).textContent = `答對 ${score}/${questions.length}`;
  return score;
}

function resetQuizForm(form) {
  form.classList.remove("is-graded");
  $$(".QuizQuestion", form).forEach((questionEl) => {
    questionEl.classList.remove("is-correct", "is-incorrect", "needs-answer");
  });
  $$(".QuizOption", form).forEach((optionEl) => {
    optionEl.classList.remove("is-correct", "is-incorrect");
  });
  $$("input", form).forEach((input) => {
    input.checked = false;
    input.disabled = false;
  });
  $('[data-action="submit-quiz"]', form).hidden = false;
  $('[data-action="retry-quiz"]', form).hidden = true;
  $(".Quiz__result", form).textContent = "";
}

function submitQuiz(form) {
  const unitId = form.closest("[data-quiz-unit]")?.dataset.quizUnit;
  const questions = questionsForUnit(unitId);
  if (!unitId || !questions.length) return;

  markLearning(unitId);
  const answers = {};
  let unanswered = 0;
  for (const question of questions) {
    const questionEl = $(`[data-question="${CSS.escape(question.id)}"]`, form);
    const answered = questionEl ? answeredIndexes(questionEl) : [];
    answers[question.id] = answered;
    questionEl?.classList.toggle("needs-answer", !answered.length);
    if (!answered.length) unanswered++;
  }

  if (unanswered) {
    $(".Quiz__result", form).textContent = `尚有 ${unanswered} 題未作答`;
    $(".QuizQuestion.needs-answer input", form)?.focus();
    return;
  }

  const now = Date.now();
  const records = {};
  for (const question of questions) {
    const correct = answerIsCorrect(question, answers[question.id]);
    records[question.id] = { answered: answers[question.id], correctAt: correct ? now : null };
    state.quiz[question.id] = records[question.id];
  }
  save(STORE.quiz, state.quiz);

  const score = gradeQuiz(form, questions, records);
  if (score < questions.length) {
    if (masteryOf(unitId) !== "review") {
      state.masteryRestore[unitId] = masteryOf(unitId) === "done" ? "done" : "learning";
      save(STORE.masteryRestore, state.masteryRestore);
    }
    setMastery(unitId, "review");
  } else if (masteryOf(unitId) === "review") {
    const restored = ["learning", "done"].includes(state.masteryRestore[unitId])
      ? state.masteryRestore[unitId]
      : "learning";
    delete state.masteryRestore[unitId];
    save(STORE.masteryRestore, state.masteryRestore);
    setMastery(unitId, restored);
  }
}

function retryQuiz(form) {
  const unitId = form.closest("[data-quiz-unit]")?.dataset.quizUnit;
  for (const question of questionsForUnit(unitId)) delete state.quiz[question.id];
  save(STORE.quiz, state.quiz);
  resetQuizForm(form);
  $("input", form)?.focus();
}

function restoreQuizzes() {
  $$(".Quiz__form").forEach((form) => {
    const unitId = form.closest("[data-quiz-unit]")?.dataset.quizUnit;
    const questions = questionsForUnit(unitId);
    if (questions.length && questions.every((question) => state.quiz[question.id])) {
      gradeQuiz(form, questions, state.quiz);
    }
  });
}

/* --- 搜尋與篩選（實作在 filters.js） -------------------------------------- */

function expandedSearchTerms(query, glossary) {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  const terms = new Set([q]);
  for (const entry of glossary || []) {
    const candidates = [entry.en, entry.zh, ...(entry.aliases || [])]
      .filter(Boolean)
      .map((value) => value.toLowerCase());
    if (candidates.some((value) => value.includes(q))) {
      if (entry.zh) terms.add(entry.zh.toLowerCase());
      if (entry.en) terms.add(entry.en.toLowerCase());
    }
  }
  return [...terms];
}

function applyFilters() {
  state.searchTerms = expandedSearchTerms(state.query, state.course?.glossary);
  runFilters(state, state.course);
  syncMuscleChips(state.muscles);
}

/* --- 名詞表 -------------------------------------------------------------- */

const GLOSSARY_CATEGORIES = ["anatomy", "pathology", "technique", "classification", "sign"];
let glossaryQuery = "";
let glossaryCategory = "";

function glossaryMatches(entry) {
  const categoryOk = !glossaryCategory || entry.category === glossaryCategory;
  if (!categoryOk) return false;
  const q = glossaryQuery.trim().toLowerCase();
  if (!q) return true;
  return [entry.zh, entry.en, entry.definition, ...(entry.aliases || [])]
    .filter(Boolean)
    .some((value) => value.toLowerCase().includes(q));
}

function renderGlossaryList() {
  const host = $("#glossaryList");
  if (!host) return;
  const terms = (state.course?.glossary || []).filter(glossaryMatches);
  host.innerHTML = terms.length
    ? terms
        .map(
          (entry) => `
            <button class="GlossaryEntry" type="button" data-glossary-id="${esc(entry.id)}">
              <span class="GlossaryEntry__names">
                <strong>${esc(entry.zh)}</strong>
                <span lang="en">${esc(entry.en)}</span>
              </span>
              <span class="GlossaryEntry__definition">${esc(entry.definition)}</span>
            </button>`,
        )
        .join("")
    : `<p class="GlossaryPanel__empty">找不到符合的名詞</p>`;
}

function renderGlossaryPanel(course) {
  const terms = course.glossary;
  if (!Array.isArray(terms) || !terms.length) return;

  const html = `
    <section class="GlossaryPanel" id="glossaryPanel">
      <button class="GlossaryPanel__head" id="glossaryToggle" type="button" aria-expanded="false" aria-controls="glossaryBody">
        ${icon("book-open", 16)}
        <span>名詞表</span>
        <span class="Counter">${terms.length}</span>
        <span class="GlossaryPanel__chevron">${icon("chevron-right", 14)}</span>
      </button>
      <div class="GlossaryPanel__body" id="glossaryBody">
        <label class="GlossaryPanel__search">
          ${icon("search", 14)}
          <span class="visually-hidden">搜尋名詞表</span>
          <input type="search" id="glossarySearch" placeholder="搜尋名詞…" autocomplete="off" />
        </label>
        <div class="GlossaryPanel__categories" role="group" aria-label="名詞分類">
          ${GLOSSARY_CATEGORIES.map(
            (category) =>
              `<button class="GlossaryChip" type="button" data-glossary-category="${category}" aria-pressed="false">${category}</button>`,
          ).join("")}
        </div>
        <div class="GlossaryPanel__list" id="glossaryList"></div>
      </div>
    </section>`;

  const musclePanel = $("#musclePanel");
  if (musclePanel) musclePanel.insertAdjacentHTML("afterend", html);
  else $(".Layout__sidebar")?.insertAdjacentHTML("beforeend", html);
  renderGlossaryList();
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

function setTab(tab, { restorePlayer = true } = {}) {
  if (!["home", "course", "player"].includes(tab)) tab = "home";
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
  $("#view-player").hidden = tab !== "player";
  scrollTo({ top: 0 });

  if (tab === "player") {
    refreshPlaylist();
    if (restorePlayer && !$("#ytFrame") && state.playlist.length) {
      playAt(state.playing >= 0 ? state.playing : 0, { autoplay: false });
    }
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
    savePlaying();
    refreshPlaylist();
  }
}

function savePlaying() {
  const id = state.playlist[state.playing]?.vid;
  if (id) save(STORE.playing, id);
}

function playAt(i, { autoplay = true } = {}) {
  if (i < 0 || i >= state.playlist.length) return;
  state.playing = i;
  savePlaying();
  play(state.playlist[i], { total: state.playlist.length, query: state.playlistQuery, autoplay });
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

function goToUnit(unitId, updateHash = true) {
  const el = $(`[data-unit="${CSS.escape(unitId)}"]`);
  if (!el) return;
  resetCourseFilters();
  setTab("course");
  el.classList.add("is-open");
  el.closest(".Chapter")?.classList.add("is-open");
  markLearning(unitId);
  rememberUnit(unitId);
  if (updateHash && location.hash !== `#${unitId}`) history.pushState(null, "", `#${unitId}`);
  el.scrollIntoView({ block: "start" });
  $(".Unit__header", el)?.focus({ preventScroll: true });
}

function resetCourseFilters() {
  state.query = "";
  state.filter = "all";
  state.learningTier = "all";
  state.muscles.clear();
  $("#search").value = "";
  $("#searchBox").classList.remove("has-value");
  $$("[data-filter]").forEach((button) => {
    const active = button.dataset.filter === "all";
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  syncTierControls();
  applyFilters();
}

function goToChapter(code) {
  const el = $(`[data-chapter="${CSS.escape(code)}"]`);
  if (!el) return;
  resetCourseFilters();
  setTab("course");
  el.classList.add("is-open");
  if (location.hash !== `#${code}`) history.pushState(null, "", `#${code}`);
  el.scrollIntoView({ block: "start" });
  $(".Chapter__header", el)?.focus({ preventScroll: true });
}

function followCourseHash() {
  const { hashValue } = videoIdFromHash();
  const target = document.getElementById(hashValue);
  if (target?.classList.contains("Unit")) goToUnit(target.dataset.unit, false);
  else if (target?.classList.contains("Chapter")) goToChapter(target.dataset.chapter);
}

function stepChapter(delta) {
  if (state.tab !== "course") setTab("course");
  const headings = $$(".Chapter__header");
  if (!headings.length) return;

  const headerHeight = parseFloat(
    getComputedStyle(document.documentElement).getPropertyValue("--header-height"),
  ) || 56;
  const line = headerHeight + 16;
  let current = -1;
  headings.forEach((heading, i) => {
    if (heading.getBoundingClientRect().top <= line) current = i;
  });
  const aligned =
    current >= 0 && Math.abs(headings[current].getBoundingClientRect().top - line) < 40;
  const wanted = delta > 0 ? current + 1 : aligned ? current - 1 : current;
  headings[Math.max(0, Math.min(headings.length - 1, wanted))]
    ?.scrollIntoView({ block: "start" });
}

function videoIdFromHash() {
  let hashValue = "";
  try {
    hashValue = decodeURIComponent(location.hash.slice(1));
  } catch {
    hashValue = location.hash.slice(1);
  }
  return { hashValue, videoId: /^play=([\w-]{11})$/.exec(hashValue)?.[1] || null };
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
      setTab(link.dataset.tabLink);
      if (link.classList.contains("SkipLink")) {
        $("#main").tabIndex = -1;
        $("#main").focus();
      }
      return;
    }
    const goCh = e.target.closest("[data-goto-chapter]");
    if (goCh) {
      goToChapter(goCh.dataset.gotoChapter);
      return;
    }
    if (e.target.closest("[data-reset-filters]")) resetCourseFilters();
    const resume = e.target.closest("[data-continue-unit]");
    if (resume) goToUnit(resume.dataset.continueUnit);
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

  $("#glossaryToggle")?.addEventListener("click", () => {
    const panel = $("#glossaryPanel");
    const open = panel.classList.toggle("is-open");
    $("#glossaryToggle").setAttribute("aria-expanded", String(open));
  });

  $("#glossarySearch")?.addEventListener("input", (e) => {
    glossaryQuery = e.currentTarget.value;
    renderGlossaryList();
  });

  $(".GlossaryPanel__categories")?.addEventListener("click", (e) => {
    const chip = e.target.closest("[data-glossary-category]");
    if (!chip) return;
    glossaryCategory = glossaryCategory === chip.dataset.glossaryCategory
      ? ""
      : chip.dataset.glossaryCategory;
    $$("[data-glossary-category]").forEach((button) => {
      const active = button.dataset.glossaryCategory === glossaryCategory;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    renderGlossaryList();
  });

  $("#glossaryList")?.addEventListener("click", (e) => {
    const entryButton = e.target.closest("[data-glossary-id]");
    if (!entryButton) return;
    const entry = state.course.glossary.find((term) => term.id === entryButton.dataset.glossaryId);
    if (!entry) return;
    searchInput.value = entry.zh;
    searchInput.dispatchEvent(new Event("input", { bubbles: true }));
    searchInput.focus();
  });

  // 播放清單
  $("#playlist").addEventListener("click", (e) => {
    const item = e.target.closest("[data-play]");
    if (item) playAt(+item.dataset.play);
  });

  // 「只看命中的 N 段」：checkbox 每次搜尋都會被重繪，所以用委派而非直接綁定
  $("#playerInfo").addEventListener("change", (e) => {
    if (e.target.id !== "segmentOnlyHits") return;
    e.target.closest(".Segments")?.classList.toggle("is-onlyHits", e.target.checked);
  });

  $("#playerInfo").addEventListener("click", (e) => {
    const jump = e.target.closest("[data-seek]");
    if (jump) {
      const seconds = Number(jump.dataset.seek);
      if (Number.isFinite(seconds) && seconds >= 0) seekTo(seconds);
      return;
    }
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
    if (goto) return e.preventDefault(), goToUnit(goto.dataset.gotoUnit);
  });

  let plDebounce;
  $("#playlistSearch").addEventListener("input", (e) => {
    state.playlistQuery = e.target.value;
    clearTimeout(plDebounce);
    plDebounce = setTimeout(() => {
      refreshPlaylist();
      // 逐段筆記要跟著標亮；不能重跑 play()，否則影片會從頭播
      refreshSegments(state.playlist[state.playing], state.playlistQuery);
    }, 120);
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
    setTab("player", { restorePlayer: false });
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

  // 知識檢核提交與重作
  $("#chapters").addEventListener("submit", (e) => {
    const form = e.target.closest(".Quiz__form");
    if (!form) return;
    e.preventDefault();
    submitQuiz(form);
  });

  $("#chapters").addEventListener("click", (e) => {
    const retry = e.target.closest('[data-action="retry-quiz"]');
    if (retry) retryQuiz(retry.closest(".Quiz__form"));
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
    const opening = !host.classList.contains("is-open");
    host.classList.toggle("is-open");
    if (kind === "unit" && opening) {
      markLearning(host.dataset.unit);
      rememberUnit(host.dataset.unit);
    }
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
    if (state.query.trim() && state.tab !== "course") setTab("course");
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

  // 類型篩選
  $$(".FilterBar__btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      $$(".FilterBar__btn").forEach((b) => {
        b.classList.toggle("is-active", b === btn);
        b.setAttribute("aria-pressed", String(b === btn));
      });
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
    const progressCount = state.mastery.size;
    const quizCount = Object.keys(state.quiz).length;
    if (!progressCount && !quizCount) return;
    if (!confirm(`確定要清除 ${progressCount} 個單元的學習進度與知識檢核紀錄嗎？`)) return;
    const affectedUnits = [...state.mastery.keys()];
    state.mastery.clear();
    state.done.clear();
    state.masteryRestore = {};
    state.quiz = {};
    saveMastery();
    save(STORE.masteryRestore, state.masteryRestore);
    save(STORE.quiz, state.quiz);
    affectedUnits.forEach(applyMasteryToUnit);
    $$(".Quiz__form").forEach(resetQuizForm);
    renderProgress();
    renderNav();
    updateChapterMeta();
    renderLanding();
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
  mountPictograms();
  syncThemeIcon();

  let data;
  try {
    const res = await fetch("course.json");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    $("#view-home").hidden = true;
    $("#main").hidden = false;
    $("#view-player").hidden = true;
    document.body.dataset.tab = "course";
    $("#chapters").innerHTML = `
      <div class="Blankslate" role="alert">
        ${icon("triangle-alert", 32)}
        <p class="Blankslate__heading">課程資料載入失敗</p>
        <p>請檢查網路連線，稍後重新載入課程。</p>
        <button class="btn" id="retryCourse" type="button">重新載入</button>
      </div>`;
    $("#retryCourse").addEventListener("click", () => location.reload());
    return;
  }

  state.course = data;
  loadLearningState(data);
  state.lastUnit = load(STORE.lastUnit, null);

  setConfig(data.config);
  setLanguages(data.config?.languages);
  discuss.setDiscussions(data.config?.discussions);
  applyChrome(data);
  renderHits(data.config); // 不 await，取數慢不該擋住畫面
  setDrillEvidence(data.drillEvidence);

  $("#chapters").innerHTML = data.chapters
    .map((ch) => renderChapter(ch, state.done, state.mastery))
    .join("");


  $("#tabCourseCount").textContent = data.meta.units;

  state.playlist = buildPlaylist(data);
  state.playlist.forEach((it, i) => urlIndex.set(it.url, i));
  const storedPlaying = load(STORE.playing, -1);
  if (typeof storedPlaying === "number") {
    state.playing = state.playlist[storedPlaying] ? storedPlaying : -1;
    // 舊版存的是 index；成功還原一次後立刻遷移成穩定的 YouTube id。
    if (state.playing >= 0) savePlaying();
  } else {
    state.playing = state.playlist.findIndex((item) => item.vid === storedPlaying);
  }

  renderLanding();
  renderStats();
  renderNav();
  renderMusclePanel(data);
  renderGlossaryPanel(data);
  renderProgress();
  restoreQuizzes();
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
    nextChapter: () => stepChapter(1),
    prevChapter: () => stepChapter(-1),
  });
  applyFilters();
  syncTierControls();

  // 舊的 ?tab=player&play=12 仍可用；新的 #play=<ytid> 不受清單排序影響。
  const params = new URLSearchParams(location.search);
  const wanted = params.get("tab");
  const { videoId: hashPlay } = videoIdFromHash();
  const hashPlayIndex = hashPlay
    ? state.playlist.findIndex((item) => item.vid === hashPlay)
    : -1;
  setTab(
    hashPlayIndex >= 0
      ? "player"
      : ["home", "course", "player"].includes(wanted)
      ? wanted
      : load(STORE.tab, "home"),
    { restorePlayer: false },
  );

  const deepPlay = params.has("play") ? Number(params.get("play")) : NaN;
  if (hashPlayIndex >= 0) {
    state.playing = hashPlayIndex;
  } else if (state.tab === "player" && Number.isInteger(deepPlay) && state.playlist[deepPlay]) {
    state.playing = deepPlay;
  }
  // 明確影片連結才自動播放；一般返回先還原影片，等學員按播放。
  if (state.tab === "player" && state.playlist.length) {
    playAt(state.playing >= 0 ? state.playing : 0, {
      autoplay: hashPlayIndex >= 0 || (Number.isInteger(deepPlay) && !!state.playlist[deepPlay]),
    });
  }

  // 首次造訪展開第一章，讓畫面不是一片收合（不要硬編章節代碼，重編後會失效）
  if (load(STORE.open, null) === null) {
    $(".Chapter[data-chapter]")?.classList.add("is-open");
  }

  followCourseHash();

  addEventListener("hashchange", () => {
    const { videoId } = videoIdFromHash();
    const i = state.playlist.findIndex((item) => item.vid === videoId);
    if (videoId && i >= 0) {
      setTab("player", { restorePlayer: false });
      playAt(i);
    } else followCourseHash();
  });
}

init();
