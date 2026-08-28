// render.js — 把 course.json 的資料轉成 DOM 字串
import { icon } from "./icons.js";
import { CHAPTER_PICTOGRAM, configurePictograms } from "./pictograms.js";

/** HTML 逸出，資料雖為自產仍一律過濾 */
export const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );

/* 這些全部由 course.config.json 注入，框架本身不預設任何主題詞彙。
   用可變物件而非重新指派，import 過的模組才拿得到更新後的內容。 */
export const KIND = {};
export const TIER = {};
const GRADE = {};
export const UI = {};
let CFG = {};

export function setConfig(cfg) {
  CFG = cfg || {};
  configurePictograms(CFG.chapters || []);
  for (const o of [KIND, TIER, GRADE, UI]) for (const k of Object.keys(o)) delete o[k];

  for (const k of CFG.kinds || []) KIND[k.id] = { label: k.label, tone: k.tone || "accent" };
  for (const tier of CFG.learningTiers || []) {
    TIER[tier.id] = { label: tier.label, tone: tier.tone || "neutral" };
  }
  for (const g of CFG.grades || []) GRADE[g.id] = { label: g.label, tone: g.tone || "accent" };
  Object.assign(UI, CFG.ui || {});
}

/** 分級／類型都用 tone 對應到樣式，id 可以隨主題自由命名 */
const toneCls = (o) => `Label--${o?.tone || "neutral"}`;
const gradeOf = (id) => GRADE[id] || Object.values(GRADE)[0] || { label: id, tone: "neutral" };
const tierOf = (id) => TIER[id] || { label: id || "未分級", tone: "neutral" };

function dateMeta(v) {
  const original = v?.original_content_date;
  const upload = v?.upload_date;
  if (original && upload && original !== upload) {
    return `<span>· 內容 ${esc(original)}</span><span>· 上架 ${esc(upload)}</span>`;
  }
  if (original && upload) return `<span>· 內容／上架 ${esc(original)}</span>`;
  if (original) return `<span>· 內容 ${esc(original)}</span>`;
  if (upload) return `<span>· 上架 ${esc(upload)}</span><span>· 原始內容日未公開</span>`;
  return `<span>· 日期待查</span>`;
}

/** 課程卡片與播放模式共用同一句介入範圍提醒。 */
export function interventionNoticeText(v) {
  if (v?.contains_intervention !== true || !v?.intervention_start_timestamp) return "";
  return `本片自 ${v.intervention_start_timestamp} 起包含注射／介入操作示範。本課為診斷取向，僅涵蓋診斷段落；介入操作需另行接受合格督導訓練，不以本片作為操作依據。`;
}

function interventionNotice(v) {
  const notice = interventionNoticeText(v);
  if (!notice) return "";
  return `
    <span class="Drill__context Drill__context--intervention" role="note"><strong>介入內容提醒</strong>${esc(notice)}</span>
    <span class="Drill__context"><strong>本課診斷段落</strong>${esc(v.diagnostic_segment_range)}</span>`;
}

/* --- 影片 ---------------------------------------------------------------- */

/** 觀看數縮寫：1038712 -> 104 萬 */
function views(n) {
  if (!n) return "";
  if (n >= 1e8) return `${(n / 1e8).toFixed(1)} 億次`;
  if (n >= 1e4) return `${Math.round(n / 1e4)} 萬次`;
  return `${n.toLocaleString("en-US")} 次`;
}

/** 播放鈕：主課與精選影片共用同一個元件，只差尺寸 */
function playBtn(sm = false, disabled = false) {
  const cls = `PlayBtn${sm ? " PlayBtn--sm" : ""}${disabled ? " PlayBtn--disabled" : ""}`;
  return `<span class="${cls}">${icon(disabled ? "inbox" : "play", sm ? 14 : 16)}</span>`;
}

function videoCard(v) {
  if (!v || !v.url) {
    return `
      <div class="VideoCard VideoCard--missing">
        <span class="VideoCard__badge">${icon("book-open", 16)}</span>
        <span class="VideoCard__main">
          <span class="VideoCard__title">尚未找到合格影片</span>
          <span class="VideoCard__meta">${esc(v?.note || "這個主題在 YouTube 上沒有品質足夠的示範")}</span>
        </span>
        ${playBtn(false, true)}
      </div>`;
  }

  return `
    <a class="VideoCard" href="${esc(v.url)}" target="_blank" rel="noopener">
      <span class="VideoCard__badge">${icon("book-open", 16)}</span>
      <span class="VideoCard__main">
        <span class="VideoCard__title">${esc(v.title)}</span>
        <span class="VideoCard__meta">
          ${v.learning_tier ? `<span class="Label ${toneCls(tierOf(v.learning_tier))}">${esc(tierOf(v.learning_tier).label)}</span>` : ""}
          <span>${esc(v.channel)}</span>
          ${v.duration ? `<span>· ${esc(v.duration)}</span>` : ""}
          ${v.views ? `<span>· ${views(v.views)}</span>` : ""}
          ${dateMeta(v)}
        </span>
        ${v.why ? `<span class="VideoCard__why">${esc(v.why)}</span>` : ""}
        ${v.scope_note ? `<span class="Drill__context"><strong>適用範圍</strong>${esc(v.scope_note)}</span>` : ""}
        ${interventionNotice(v)}
        ${v.disclosure ? `<span class="Drill__context Drill__context--disclosure"><strong>來源揭露</strong>${esc(v.disclosure)}</span>` : ""}
        <span class="VideoCard__trust">
          ${v.source_authority ? `<span class="Label Label--neutral">${esc(v.source_authority)}</span>` : ""}
          ${v.classic_exception ? `<span class="Label Label--attention">經典例外</span>` : ""}
          ${v.curation_status ? `<span class="Label Label--neutral">${esc(v.curation_status)}</span>` : ""}
        </span>
      </span>
      ${playBtn()}
    </a>`;
}

const REVIEW = {
  draft: { label: "內容草稿", tone: "attention" },
  "medical-review": { label: "醫療審閱中", tone: "accent" },
  approved: { label: "已核准", tone: "success" },
};

function clinicalBrief(u) {
  const cleanList = (value) =>
    Array.isArray(value)
      ? value.filter((item) => typeof item === "string" && item.trim()).map((item) => item.trim())
      : [];

  const section = ({ title, code, iconName, list, cls = "", fallback, emptyLabel = "待補" }) => {
    const items = cleanList(list);
    return `<section class="ClinicalBrief__section ClinicalBrief__panel ${cls}${items.length ? "" : " is-fallback"}">
      <header class="ClinicalBrief__panelHead">
        <span class="ClinicalBrief__panelIcon">${icon(iconName, 16)}</span>
        <div class="ClinicalBrief__panelTitle">
          <span class="ClinicalBrief__panelCode">${esc(code)}</span>
          <h4>${esc(title)}</h4>
        </div>
        <span class="ClinicalBrief__panelCount">${items.length ? `${items.length} 項` : esc(emptyLabel)}</span>
      </header>
      ${items.length
        ? `<ol class="ClinicalBrief__list">
            ${items
              .map(
                (item, i) => `<li>
                  <span class="ClinicalBrief__listIndex">${String(i + 1).padStart(2, "0")}</span>
                  <span>${esc(item)}</span>
                </li>`,
              )
              .join("")}
          </ol>`
        : `<p class="ClinicalBrief__fallback">${esc(fallback)}</p>`}
    </section>`;
  };

  const objectives = cleanList(u.objectives);
  const objectiveBlock = objectives.length
    ? `<section class="ClinicalBrief__objective">
         <span class="ClinicalBrief__objectiveIcon">${icon("target", 17)}</span>
         <span class="ClinicalBrief__objectiveLabel">LEARNING TARGET</span>
         <ul>${objectives.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
       </section>`
    : "";

  const refs = (u.references || []).length
    ? `<section class="ClinicalBrief__refs">
         <h4>${icon("book-open", 14)} 依據與延伸閱讀</h4>
         <ul>
           ${u.references
             .map(
               (r) => `<li><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>` +
                 `${r.year ? ` <span class="Label Label--neutral">${esc(r.year)}</span>` : ""}</li>`,
             )
             .join("")}
         </ul>
       </section>`
    : "";

  const viewFallback = u.type === "orientation"
    ? "本課程規範／安全單元目前未設定掃描視圖。"
    : "必備視圖待醫療審閱。";

  return `<div class="ClinicalBrief">
    ${objectiveBlock}
    <div class="ClinicalBrief__grid" aria-label="臨床掃描檢核表">
      ${section({
        title: "必備視圖／產出",
        code: "VIEW SET",
        iconName: "scan-line",
        list: u.required_views,
        cls: "ClinicalBrief__section--views",
        fallback: viewFallback,
        emptyLabel: u.type === "orientation" ? "N/A" : "待補",
      })}
      ${section({
        title: "操作與判讀重點",
        code: "SCAN KEYS",
        iconName: "shield-check",
        list: u.key_points,
        cls: "ClinicalBrief__section--points",
        fallback: "操作與判讀重點待醫療審閱。",
      })}
      ${section({
        title: "常見陷阱",
        code: "PITFALLS",
        iconName: "triangle-alert",
        list: u.pitfalls,
        cls: "ClinicalBrief__section--pitfalls",
        fallback: "常見陷阱待醫療審閱。",
      })}
    </div>
    ${refs}
  </div>`;
}

const langLabel = (l) => (CFG.languages || {})[l] || l || "其他";

/** 主課可能有多個語言版本，用小分頁切換 */
function lessonBox(u) {
  const lessons = (u.lessons || (u.lesson ? [u.lesson] : [])).filter(Boolean);
  // 本課的教學影片全部走 drills（精選影片），單元沒有「主課影片」這個角色。
  // 沒有主課影片時整塊不渲染，不要留「尚未找到合格影片」的空佔位卡。
  if (!lessons.length) return "";
  if (lessons.length === 1) return videoCard(lessons[0]);

  return `
    <div class="LessonBox">
      <div class="LessonBox__langs" role="tablist" aria-label="主課語言">
        ${lessons
          .map(
            (l, i) => `
          <button class="LessonBox__lang${i === 0 ? " is-active" : ""}" type="button"
                  role="tab" aria-selected="${i === 0}" data-lesson="${i}">
            ${esc(langLabel(l.lang))}
          </button>`,
          )
          .join("")}
      </div>
      ${lessons
        .map(
          (l, i) =>
            `<div class="LessonBox__pane" data-lesson-pane="${i}"${i ? " hidden" : ""}>${videoCard(l)}</div>`,
        )
        .join("")}
    </div>`;
}

/* --- 動作清單 ------------------------------------------------------------ */

function muscleTags(list) {
  return (list || [])
    .map(
      (m) =>
        `<button class="Label Label--neutral Label--muscle" data-muscle="${esc(m)}"
                 type="button" title="篩選涉及 ${esc(m)} 的內容">${esc(m)}</button>`,
    )
    .join("");
}

function drill(d) {
  const tier = tierOf(d.learning_tier);
  const inner = `
    <span class="Drill__marker" style="background:var(--fgColor-${esc((KIND[d.kind] || {}).tone || "accent")})"></span>
    <span class="Drill__main">
      <span class="Drill__name">${esc(d.name)}${d.en ? ` <span class="Drill__en">${esc(d.en)}</span>` : ""}</span>
      <span class="Drill__meta">
        <span class="Label ${toneCls(tier)}">${d.learning_tier === "core" ? icon("star", 11) : ""}${esc(tier.label)}</span>
        ${d.target ? `<span>${esc(d.target)}</span>` : ""}
        ${d.dose ? `<span class="Drill__dose">${esc(d.dose)}</span>` : ""}
        ${d.channel ? `<span>· ${esc(d.channel)}</span>` : ""}
        ${d.presenter || d.presenter_note ? `<span>· 講者：${esc(d.presenter || d.presenter_note)}</span>` : ""}
        ${d.duration ? `<span>· ${esc(d.duration)}</span>` : ""}
        ${dateMeta(d)}
      </span>
      ${d.why ? `<span class="Drill__why">${esc(d.why)}</span>` : ""}
      ${d.scope_note ? `<span class="Drill__context"><strong>適用範圍</strong>${esc(d.scope_note)}</span>` : ""}
      ${interventionNotice(d)}
      ${d.disclosure ? `<span class="Drill__context Drill__context--disclosure"><strong>來源揭露</strong>${esc(d.disclosure)}</span>` : ""}
      ${d.date_note ? `<span class="Drill__context"><strong>日期註記</strong>${esc(d.date_note)}</span>` : ""}
      <span class="Drill__trust">
        ${d.source_authority ? `<span class="Label Label--neutral">${esc(d.source_authority)}</span>` : ""}
        ${d.classic_exception ? `<span class="Label Label--attention">經典例外</span>` : ""}
        ${d.curation_status ? `<span class="Label Label--neutral">${esc(d.curation_status)}</span>` : ""}
      </span>
      ${(d.facets || []).length ? `<span class="Drill__muscles">${muscleTags(d.facets)}</span>` : ""}
    </span>
    ${playBtn(true, !d.url)}`;

  const attrs = `class="Drill" data-kind="${esc(d.kind)}" data-learning-tier="${esc(d.learning_tier)}" data-facets="${esc((d.facets || []).join("|"))}"${d.cat ? ` data-cat="${esc(d.cat)}"` : ""}`;

  // 有連結就整列可點，跟主課卡片一致
  return d.url
    ? `<li ${attrs}><a class="Drill__link" href="${esc(d.url)}" target="_blank" rel="noopener" title="${esc(d.title || "觀看示範")}">${inner}</a></li>`
    : `<li ${attrs}><span class="Drill__link" aria-disabled="true" title="尚未找到合格影片">${inner}</span></li>`;
}

function drillGroup(kind, list) {
  if (!list.length) return "";
  const k = KIND[kind];
  const ranked = [...list].sort(
    (a, b) => Number(b.learning_tier === "core") - Number(a.learning_tier === "core"),
  );
  return `
    <div class="DrillGroup" data-group="${kind}">
      <h4 class="DrillGroup__title">
        <span class="Drill__marker" style="background:var(--fgColor-${esc(k.tone)})"></span>
        ${k.label}
        <span class="Counter">${list.length}</span>
      </h4>
      <ul class="DrillList">${ranked.map(drill).join("")}</ul>
    </div>`;
}

/* --- 實證註記 ------------------------------------------------------------ */

function evidence(ev, unitId) {
  if (!ev) return "";
  const g = gradeOf(ev.evidence_grade);

  const row = (key, val) =>
    val
      ? `<div class="Evidence__row"><span class="Evidence__key">${key}</span><span>${esc(val)}</span></div>`
      : "";

  const cites = (ev.citations || []).length
    ? `<div class="Evidence__cite">
         ${ev.citations
           .map(
             (c) =>
               `<a href="${esc(c.url)}" target="_blank" rel="noopener" title="${esc(c.title)}">${esc(c.journal || c.title)}${c.year ? ` ${esc(c.year)}` : ""}</a>`,
           )
           .join("")}
       </div>`
    : "";

  const rows = (UI.evidenceRows || [])
    .map((r) =>
      r.type === "flags"
        ? (ev[r.field] || []).length
          ? `<div class="Evidence__row">
               <span class="Evidence__key">${esc(r.label)}</span>
               <span class="Evidence__flags">
                 ${ev[r.field].map((f) => `<span class="Label Label--danger">${esc(f)}</span>`).join("")}
               </span>
             </div>`
          : ""
        : row(r.label, ev[r.field]),
    )
    .join("");

  return `
    <section class="Evidence" data-evidence="${esc(unitId)}">
      <button class="Evidence__header" type="button" data-toggle="evidence">
        ${icon("microscope", 14)}
        <span>${esc(UI.unitEvidenceLabel || "")}</span>
        <span class="Label ${toneCls(g)}">${g.label}</span>
        <span class="Evidence__spacer"></span>
        ${ev.url ? `<span class="Label Label--neutral">OpenEvidence</span>` : ""}
        <span class="Evidence__chevron">${icon("chevron-right", 14)}</span>
      </button>
      <div class="Evidence__body">
        ${rows}
        ${cites}
        ${
          ev.url
            ? `<div class="Evidence__cite"><a href="${esc(ev.url)}" target="_blank" rel="noopener">在 OpenEvidence 讀完整回答 ${icon("external-link", 11)}</a></div>`
            : ""
        }
      </div>
    </section>`;
}

/* --- 動作類別的實證 ------------------------------------------------------ */

let DRILL_EV = {};

export function setDrillEvidence(map) {
  DRILL_EV = map || {};
}

function drillEvidence(u) {
  const cats = [...new Set((u.drills || []).map((d) => d.cat).filter(Boolean))]
    .map((id) => DRILL_EV[id])
    .filter((c) => c && c.citations?.length);
  if (!cats.length) return "";

  const totalCites = cats.reduce((n, c) => n + c.citations.length, 0);

  const block = (cat) => {
    const g = gradeOf(cat.evidence_grade);
    return `
      <details class="DrillEvCat">
        <summary>
          <span class="DrillEvCat__name">${esc(cat.name)}</span>
          <span class="Label ${toneCls(g)}">${g.label}</span>
          <span class="Counter">${cat.citations.length}</span>
        </summary>
        ${cat.summary ? `<p class="DrillEvCat__summary">${esc(cat.summary)}</p>` : ""}
        <ol class="DrillEvCat__cites">
          ${cat.citations
            .map(
              (c) => `
            <li>
              <a href="https://pubmed.ncbi.nlm.nih.gov/${esc(c.pmid)}/" target="_blank" rel="noopener">${esc(c.title)}</a>
              <span class="DrillEvCat__src">${esc(c.journal || "")}${c.year ? ` ${esc(c.year)}` : ""}${c.design ? ` · ${esc(c.design)}` : ""} · PMID ${esc(c.pmid)}</span>
              ${c.takeaway ? `<span class="DrillEvCat__take">${esc(c.takeaway)}</span>` : ""}
            </li>`,
            )
            .join("")}
        </ol>
      </details>`;
  };

  return `
    <section class="Evidence DrillEv" data-drillev="${esc(u.id)}">
      <button class="Evidence__header" type="button" data-toggle="drillev">
        ${icon("microscope", 14)}
        <span>${esc(UI.drillEvidenceLabel || "")}</span>
        <span class="Counter">${cats.length} 類 · ${totalCites} 篇</span>
        <span class="Evidence__spacer"></span>
        <span class="Label Label--neutral">PubMed</span>
        <span class="Evidence__chevron">${icon("chevron-right", 14)}</span>
      </button>
      <div class="Evidence__body DrillEv__body">${cats.map(block).join("")}</div>
    </section>`;
}

/* --- 肌群 ---------------------------------------------------------------- */

function muscles(tight, weak) {
  if (!tight?.length && !weak?.length) return "";
  const block = (mod, iconName, title, list) =>
    list?.length
      ? `<div class="MuscleBlock MuscleBlock--${mod}">
           <h4 class="MuscleBlock__title">${icon(iconName, 12)} ${title}</h4>
           <div class="MuscleBlock__list">
             ${list.map((m) => `<span class="Label Label--neutral">${esc(m)}</span>`).join("")}
           </div>
         </div>`
      : "";

  return `
    <div class="MuscleGrid">
      ${block("tight", "flame", UI.tightLabel || "", tight)}
      ${block("weak", "battery-low", UI.weakLabel || "", weak)}
    </div>`;
}

/* --- 知識檢核 ------------------------------------------------------------ */

function quiz(u) {
  if (!Array.isArray(u.questions) || !u.questions.length) return "";

  const questions = u.questions.map((q, questionIndex) => {
    const inputType = q.type === "multi" ? "checkbox" : "radio";
    const typeLabel = q.type === "multi" ? "複選" : "單選";
    const options = (q.options || []).map((option, optionIndex) => `
      <label class="QuizOption" data-option="${optionIndex}">
        <input type="${inputType}" name="quiz-${esc(q.id)}" value="${optionIndex}" />
        <span class="QuizOption__control" aria-hidden="true"></span>
        <span class="QuizOption__main">
          <span class="QuizOption__text">${esc(option.text)}</span>
          <span class="QuizOption__rationale">${esc(option.rationale)}</span>
        </span>
      </label>`).join("");

    return `
      <fieldset class="QuizQuestion" data-question="${esc(q.id)}">
        <legend class="QuizQuestion__legend">
          <span class="QuizQuestion__meta">第 ${questionIndex + 1} 題 · ${typeLabel}${q.difficulty ? ` · ${esc(q.difficulty)}` : ""}</span>
          <span class="QuizQuestion__stem">${esc(q.stem)}</span>
        </legend>
        <div class="QuizQuestion__options">${options}</div>
      </fieldset>`;
  }).join("");

  return `
    <section class="Quiz" data-quiz-unit="${esc(u.id)}" aria-labelledby="quiz-title-${esc(u.id)}">
      <header class="Quiz__header">
        <span class="Quiz__icon">${icon("brain", 18)}</span>
        <div>
          <h3 id="quiz-title-${esc(u.id)}">知識檢核</h3>
          <p>完成 ${u.questions.length} 題後提交；複選題須選出所有正確答案。</p>
        </div>
      </header>
      <form class="Quiz__form" novalidate>
        ${questions}
        <footer class="Quiz__footer">
          <button class="btn btn-primary" type="submit" data-action="submit-quiz">提交</button>
          <button class="btn" type="button" data-action="retry-quiz" hidden>${icon("rotate-ccw", 13)} 重作</button>
          <p class="Quiz__result" aria-live="polite" aria-atomic="true"></p>
        </footer>
      </form>
    </section>`;
}

/* --- 單元 ---------------------------------------------------------------- */

const MASTERY_VIEW = {
  "not-started": { icon: "circle-dot", label: "未開始" },
  learning: { icon: "book-open", label: "學習中" },
  done: { icon: "check", label: "已完成" },
  review: { icon: "triangle-alert", label: "待複習" },
};

function renderUnit(u, mastery) {
  const total = (u.drills || []).length;
  const review = REVIEW[u.review_status] || REVIEW.draft;
  const masteryView = MASTERY_VIEW[mastery] || MASTERY_VIEW["not-started"];

  const typeLabel = (UI.unitTypes || {})[u.type];
  const badges = [
    typeLabel
      ? `<span class="Label Label--${u.type === "foundation" ? "accent" : "neutral"}">${esc(typeLabel)}</span>`
      : "",
    u.level ? `<span class="Label Label--neutral">${esc(u.level)}</span>` : "",
    `<span class="Label Label--${review.tone}">${esc(review.label)}</span>`,
    total ? `<span class="Label Label--neutral">${icon("layers", 11)} ${total}</span>` : "",
    // 實證強度直接標在標題列。contested 的單元不該要展開才看得到
    u.evidence?.evidence_grade
      ? `<span class="Label ${toneCls(gradeOf(u.evidence.evidence_grade))}"
               title="OpenEvidence 查證結果">${icon("microscope", 11)} ${gradeOf(u.evidence.evidence_grade).label}</span>`
      : "",
  ].join("");

  const groups = Object.keys(KIND)
    .map((k, i) => ({ k, i, list: (u.drills || []).filter((d) => d.kind === k) }))
    .filter(({ list }) => list.length)
    .sort(
      (a, b) =>
        Number(b.list.some((d) => d.learning_tier === "core")) -
          Number(a.list.some((d) => d.learning_tier === "core")) ||
        a.i - b.i,
    )
    .map(({ k, list }) => drillGroup(k, list))
    .join("");

  // 單元自身的肌群 + 底下所有動作的肌群，供側欄篩選比對
  const allFacets = [
    ...new Set([...(u.facets || []), ...(u.drills || []).flatMap((d) => d.facets || [])]),
  ];

  return `
    <article class="Unit is-${esc(mastery)}" id="${esc(u.id)}" data-unit="${esc(u.id)}"
             data-facets="${esc(allFacets.join("|"))}">
      <button class="Unit__header" type="button" data-toggle="unit">
        <span class="Unit__check" data-action="toggle-done" role="checkbox"
              aria-checked="${mastery === "done"}" aria-label="掌握度：${masteryView.label}"
              tabindex="0" title="掌握度：${masteryView.label}">
          ${icon(masteryView.icon, 13)}<span class="Unit__checkLabel">${masteryView.label}</span>
        </span>
        <span class="Unit__main">
          <span class="Unit__kicker"><span>${esc(u.id.toUpperCase().replace("-", " / "))}</span> CLINICAL MODULE</span>
          <span class="Unit__title">${esc(u.name)} ${badges}</span>
          ${u.summary ? `<span class="Unit__summary">${esc(u.summary)}</span>` : ""}
        </span>
        <span class="Unit__chevron">${icon("chevron-right", 16)}</span>
      </button>

      <div class="Unit__body">
        ${clinicalBrief(u)}
        ${lessonBox(u)}
        ${
          u.assessment
            ? `<div class="Assessment">
                 <span class="Assessment__icon">${icon("clipboard-check", 16)}</span>
                 <span><span class="Assessment__label">${esc(UI.assessmentLabel || "")}</span>${esc(u.assessment)}</span>
               </div>`
            : ""
        }
        ${quiz(u)}
        ${muscles(u.tight, u.weak)}
        ${evidence(u.evidence, u.id)}
        ${groups}
        ${drillEvidence(u)}
      </div>
    </article>`;
}

/* --- 立場聲明 ------------------------------------------------------------ */

/* --- 章節 ---------------------------------------------------------------- */

export function renderChapter(ch, doneSet, masteryMap = new Map()) {
  const doneCount = ch.units.filter((u) => doneSet.has(u.id)).length;
  const pct = ch.units.length ? Math.round((doneCount / ch.units.length) * 100) : 0;
  const drillTotal = ch.units.reduce((n, u) => n + (u.drills?.length || 0), 0);

  return `
    <section class="Chapter" id="${esc(ch.code)}" data-chapter="${esc(ch.code)}">
      <button class="Chapter__header" type="button" data-toggle="chapter">
        <span class="Chapter__num">${CHAPTER_PICTOGRAM[ch.code] ? `<svg class="Pictogram" width="30" height="30" aria-hidden="true"><use href="#p-${CHAPTER_PICTOGRAM[ch.code]}" /></svg>` : icon(ch.icon || "circle-dot", 18)}</span>
        <span class="Chapter__titles">
          <span class="Chapter__title">
            <span class="Chapter__code">${esc(ch.code)}</span>
            ${esc(ch.title)}
          </span>
          <span class="Chapter__meta">
            ${ch.units.length} 個單元${drillTotal ? ` · ${drillTotal} ${UI.drillNoun || "支精選影片"}` : ""}
            ${doneCount ? ` · 已完成 ${doneCount}` : ""}
          </span>
        </span>
        <span class="Chapter__progress">
          <span class="ProgressBar ProgressBar--thin">
            <span class="ProgressBar__fill" style="width:${pct}%"></span>
          </span>
        </span>
        <span class="Chapter__chevron">${icon("chevron-right", 16)}</span>
      </button>
      <div class="Chapter__body">
        ${ch.units
          .map((u) =>
            renderUnit(
              u,
              masteryMap.get(u.id) || (doneSet.has(u.id) ? "done" : "not-started"),
            ),
          )
          .join("")}
      </div>
    </section>`;
}

/* --- 首頁 ---------------------------------------------------------------- */

export function renderHome(course, { doneSet = new Set(), lastUnit = null } = {}) {
  const { meta, chapters, stance } = course;

  const units = chapters.flatMap((chapter) =>
    chapter.units.map((unit) => ({ chapter, unit })),
  );
  const last = units.find(({ unit }) => unit.id === lastUnit?.id);
  const first = units[0];
  const resume = last || first;
  const total = units.length;
  const done = units.filter(({ unit }) => doneSet.has(unit.id)).length;
  const progress = total ? Math.round((done / total) * 100) : 0;

  const L = CFG.landing || {};
  const steps = (L.steps || []).map(
    (s, i) => `
    <div class="Step">
      <span class="Step__n">${icon(s.icon || "circle-dot", 18)}</span>
      <div>
        <h3 class="Step__title">${i + 1}. ${esc(s.title)}</h3>
        <p class="Step__body">${esc(s.body)}</p>
      </div>
    </div>`,
  ).join("");

  const stanceCards = (stance || []).map((s) => {
    const g = gradeOf(s.evidence_grade);
    return `
      <div class="LandingStance">
        <div class="LandingStance__head">
          <span class="Label ${toneCls(g)}">${g.label}</span>
          <strong>${esc(s.name)}</strong>
        </div>
        <p>${esc((CFG.stance?.verdicts || {})[s.unit] || "")}</p>
      </div>`;
  }).join("");

  const chapterCards = chapters.map((ch) => {
    const drills = ch.units.reduce((n, u) => n + (u.drills?.length || 0), 0);
    return `
      <button class="ChapterCard" type="button" data-goto-chapter="${esc(ch.code)}">
        <span class="ChapterCard__icon">${icon(ch.icon || "circle-dot", 18)}</span>
        <span class="ChapterCard__main">
          <span class="ChapterCard__title"><span class="Chapter__code">${esc(ch.code)}</span> ${esc(ch.title)}</span>
          <span class="ChapterCard__meta">${ch.units.length} 單元${drills ? ` · ${drills} ${UI.drillNoun || "支精選影片"}` : ""}</span>
          <span class="ChapterCard__units">${ch.units.map((u) => esc(u.name)).join("、")}</span>
        </span>
      </button>`;
  }).join("");

  return `
    <section class="ContinueCard" aria-labelledby="continueTitle">
      <div class="ContinueCard__main">
        <span class="ContinueCard__eyebrow">${icon("book-open", 14)} LEARNING PROGRESS</span>
        <h2 class="ContinueCard__title" id="continueTitle">
          ${last
            ? `上次學到：${esc(last.chapter.title)}／${esc(last.unit.name)}`
            : "從第一章開始"}
        </h2>
        <div class="ContinueCard__progressHead">
          <span>整體進度</span>
          <strong>${done} / ${total} · ${progress}%</strong>
        </div>
        <div class="ProgressBar" role="progressbar" aria-label="整體進度"
             aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progress}">
          <div class="ProgressBar__fill" style="width:${progress}%"></div>
        </div>
      </div>
      ${resume
        ? `<button class="btn btn-primary ContinueCard__action" type="button"
                   data-continue-unit="${esc(resume.unit.id)}">
             ${last ? "繼續" : "從第一章開始"} ${icon("chevron-right", 14)}
           </button>`
        : ""}
    </section>

    <section class="Landing__section">
      <h2 class="Landing__h2">${icon("book-open", 20)} ${esc(L.howTitle || "")}</h2>
      <div class="Steps">${steps}</div>
    </section>

    <section class="Landing__section">
      <h2 class="Landing__h2">${icon("microscope", 20)} ${esc(L.stanceTitle || "")}</h2>
      <p class="Landing__lede">
${esc(L.stanceLede || "")}
      </p>
      <div class="Landing__stance">${stanceCards}</div>
    </section>

    ${(L.notices || []).length
      ? `<section class="Landing__section">
           <h2 class="Landing__h2">${icon("info", 20)} ${esc(L.noticeTitle || "")}</h2>
           ${L.noticeLede ? `<p class="Landing__lede">${esc(L.noticeLede)}</p>` : ""}
           <div class="Notices">
             ${(L.notices || [])
               .map(
                 (n) => `
               <article class="Notice">
                 <h3 class="Notice__title">${icon(n.icon || "info", 15)} ${esc(n.title)}</h3>
                 <p class="Notice__body">${esc(n.body)}</p>
               </article>`,
               )
               .join("")}
           </div>
         </section>`
      : ""}

    <section class="Landing__section">
      <h2 class="Landing__h2">${icon("layers", 20)} ${esc(L.chaptersTitle || "")}</h2>
      <div class="ChapterGrid">${chapterCards}</div>
    </section>

    <section class="Landing__cta">
      <div>
        <h2 class="Landing__h2">${esc(L.ctaTitle || "")}</h2>
        <p class="Landing__lede">
${esc((L.ctaLede || "").replace("{units}", meta.units).replace("{videos}", meta.video_slots))}
        </p>
      </div>
      <div class="Landing__ctaBtns">
        <button class="btn btn-primary" type="button" data-tab-link="player">
          ${icon("play", 14)} ${esc(CFG.ui?.tabs?.player || "")}
        </button>
        <button class="btn" type="button" data-tab-link="course">
          ${icon("layers", 14)} ${esc(CFG.ui?.tabs?.course || "")}
        </button>
      </div>
    </section>`;
}
