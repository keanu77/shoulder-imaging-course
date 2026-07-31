// player.js — 上課模式：把整門課攤平成播放清單，左側嵌入播放
import { icon } from "./icons.js";
import { esc, KIND, UI } from "./render.js";
import { button as discussButton, panel as discussPanel } from "./discuss.js";

const $ = (s, r = document) => r.querySelector(s);

const EMBED = "https://www.youtube-nocookie.com/embed/";
let LANG = {};
export function setLanguages(m) { LANG = m || {}; }

/** 把 course.json 攤平成一維播放清單 */
export function buildPlaylist(course) {
  const items = [];
  for (const ch of course.chapters) {
    for (const u of ch.units) {
      const base = {
        chCode: ch.code,
        chTitle: ch.title,
        unitId: u.id,
        unitName: u.name,
      };
      for (const les of u.lessons || (u.lesson ? [u.lesson] : [])) {
        if (!les?.url) continue;
        items.push({
          ...base,
          kind: "lesson",
          lang: les.lang,
          name: les.title,
          title: les.title,
          channel: les.channel,
          duration: les.duration,
          views: les.views,
          url: les.url,
          why: les.why,
          assessment: u.assessment,
        });
      }
      for (const d of u.drills || []) {
        if (!d.url) continue;
        items.push({
          ...base,
          kind: d.kind,
          name: d.name,
          en: d.en,
          title: d.title,
          channel: d.channel,
          duration: d.duration,
          views: d.views,
          url: d.url,
          target: d.target,
          dose: d.dose,
          facets: d.facets,
          cat: d.cat,
        });
      }
    }
  }
  return items.map((it, i) => ({ ...it, i, vid: videoId(it.url) }));
}

function videoId(url) {
  const m = /(?:v=|youtu\.be\/)([\w-]{11})/.exec(url || "");
  return m ? m[1] : null;
}

function dur(s) {
  return s || "";
}

/* --- 播放清單渲染 -------------------------------------------------------- */

export function renderPlaylist(items, { doneSet, currentIndex, query, onlyTodo }) {
  const q = (query || "").trim().toLowerCase();
  let lastCh = null;
  let lastUnit = null;
  let shown = 0;
  const html = [];

  for (const it of items) {
    if (onlyTodo && doneSet.has(it.unitId)) continue;
    if (q) {
      const hay = `${it.name} ${it.title || ""} ${it.channel || ""} ${it.unitName} ${it.chTitle} ${(it.facets || []).join(" ")} ${it.target || ""}`;
      if (!hay.toLowerCase().includes(q)) continue;
    }

    if (it.chCode !== lastCh) {
      html.push(`<div class="PlaylistChapter">${esc(it.chCode)} ${esc(it.chTitle)}</div>`);
      lastCh = it.chCode;
      lastUnit = null;
    }
    if (it.unitId !== lastUnit) {
      html.push(`<div class="PlaylistUnit">${esc(it.unitName)}</div>`);
      lastUnit = it.unitId;
    }

    const k = it.kind === "lesson" ? null : KIND[it.kind];
    html.push(`
      <button class="PlaylistItem${it.i === currentIndex ? " is-playing" : ""}${doneSet.has(it.unitId) ? " is-done" : ""}"
              type="button" data-play="${it.i}">
        <span class="PlaylistItem__dot" style="background:var(--fgColor-${esc(it.kind === "lesson" ? "accent" : (KIND[it.kind] || {}).tone || "accent")})"></span>
        <span class="PlaylistItem__main">
          <span class="PlaylistItem__name">${esc(it.kind === "lesson" ? `${UI.lessonLabel || ""} · ${it.name}` : it.name)}</span>
          <span class="PlaylistItem__meta">${k ? esc(k.label) + " · " : ""}${it.lang ? esc(LANG[it.lang] || it.lang) + " · " : ""}${esc(it.channel || "")}</span>
        </span>
        <span class="PlaylistItem__dur">${esc(dur(it.duration))}</span>
      </button>`);
    shown++;
  }

  $("#playlist").innerHTML =
    html.join("") ||
    `<div class="Blankslate">${icon("inbox", 28)}<p class="Blankslate__heading">沒有符合的影片</p></div>`;
  $("#playlistCount").textContent =
    shown === items.length ? `${items.length} 支影片` : `${shown} / ${items.length} 支`;
  return shown;
}

/* --- 播放 ---------------------------------------------------------------- */

export function play(item, { total }) {
  if (!item?.vid) return;

  $("#playerFrame").innerHTML = `
    <iframe id="ytFrame" src="${EMBED}${esc(item.vid)}?rel=0&modestbranding=1&autoplay=1&enablejsapi=1&origin=${encodeURIComponent(location.origin)}"
            title="${esc(item.title || item.name)}"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            referrerpolicy="strict-origin-when-cross-origin"
            allowfullscreen></iframe>`;

  const k = item.kind === "lesson" ? null : KIND[item.kind];
  const badge = k
    ? `<span class="Label Label--${esc(k.tone || "neutral")}">${esc(k.label)}</span>`
    : `<span class="Label Label--accent">${esc(UI.lessonLabel || "")}</span>`;

  $("#playerInfo").innerHTML = `
    <div class="Player__bar">
      <div class="Player__barMain">
        <h2 class="Player__title">${esc(item.name)}</h2>
        <div class="Player__sub">
          <span>${esc(item.chCode)} ${esc(item.chTitle)}</span>
          <span>›</span>
          <a href="#${esc(item.unitId)}" data-goto-unit="${esc(item.unitId)}">${esc(item.unitName)}</a>
          <span>· ${item.i + 1} / ${total}</span>
          ${badge}
          ${item.lang ? `<span class="Label Label--neutral">${esc(LANG[item.lang] || item.lang)}</span>` : ""}
          <span>${esc(item.channel || "")}</span>
          ${item.duration ? `<span>· ${esc(item.duration)}</span>` : ""}
          ${item.dose ? `<span class="Drill__dose">${esc(item.dose)}</span>` : ""}
        </div>
      </div>
      <div class="Player__actions">
        <button class="btn" data-step="-1" type="button">${icon("chevron-left", 14)} <span class="Player__btnText">${esc(UI.prevLabel || "")}</span></button>
        <button class="btn" data-step="1" type="button"><span class="Player__btnText">${esc(UI.nextLabel || "")}</span> ${icon("chevron-right", 14)}</button>
        <button class="btn" data-mark-unit="${esc(item.unitId)}" type="button">${icon("check", 14)} ${esc(UI.doneLabel || "")}</button>
        <button class="btn btn-icon" data-toggle-list type="button" title="收起／顯示清單">${icon("layers", 16)}<span class="visually-hidden" data-list-label>收起清單</span></button>
        ${discussButton()}
        <a class="btn btn-icon" href="${esc(item.url)}" target="_blank" rel="noopener" title="${esc(UI.openExternal || "")}">${icon("external-link", 16)}</a>
      </div>
    </div>
    ${
      item.why || item.assessment
        ? `<details class="Player__more">
             <summary>${esc(UI.moreLabel || "")}</summary>
             ${item.why ? `<p class="Player__note">${esc(item.why)}</p>` : ""}
             ${item.assessment ? `<p class="Player__note"><strong>怎麼自己評估　</strong>${esc(item.assessment)}</p>` : ""}
           </details>`
        : ""
    }
    ${discussPanel()}`;

  fitFrame();
}

/** 依實際可用高度算出影片寬度，讓它吃滿又不變形。
 *  純 CSS 同時給 max-width + max-height 會讓 aspect-ratio 失效，所以這裡用量的。 */
export function fitFrame() {
  const stage = $(".Player__stage");
  const frame = $(".Player__frame");
  const info = $("#playerInfo");
  if (!stage || !frame) return;

  // 用 scrollHeight：資訊區要完整放得下，影片才拿剩下的空間
  const infoH = info ? Math.max(info.offsetHeight, info.scrollHeight) : 0;
  const avail = stage.clientHeight - infoH - 12;
  if (avail <= 0) return;
  const byHeight = avail * (16 / 9);
  frame.style.setProperty("--frame-w", `${Math.floor(Math.min(stage.clientWidth, byHeight))}px`);
}

/** 視窗大小改變或資訊區內容變動時重算 */
export function watchFrame() {
  const stage = $(".Player__stage");
  if (!stage || typeof ResizeObserver === "undefined") return;
  const ro = new ResizeObserver(() => fitFrame());
  ro.observe(stage);
  const info = $("#playerInfo");
  if (info) ro.observe(info);
  addEventListener("resize", fitFrame);
}

export function stop() {
  const f = $("#playerFrame iframe");
  if (f) f.remove();
}

/* --- 播放清單寬度可拖曳 --------------------------------------------------- */

const MIN_W = 260;

/** 讓使用者拖動分隔條調整右側清單寬度；回傳目前寬度供外部保存 */
export function initResizer(initial, onChange) {
  const player = $(".Player");
  const grip = $("#playerResizer");
  if (!player || !grip) return;

  const clamp = (w) => Math.max(MIN_W, Math.min(w, Math.round(player.clientWidth * 0.6)));
  const apply = (w) => {
    player.style.setProperty("--playlist-w", `${clamp(w)}px`);
    fitFrame();
  };

  if (initial) apply(initial);

  grip.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    grip.setPointerCapture(e.pointerId);
    grip.classList.add("is-dragging");
    document.body.classList.add("is-resizing");

    const move = (ev) => apply(player.getBoundingClientRect().right - ev.clientX - 16);
    const up = () => {
      grip.classList.remove("is-dragging");
      document.body.classList.remove("is-resizing");
      grip.removeEventListener("pointermove", move);
      grip.removeEventListener("pointerup", up);
      const w = parseInt(player.style.getPropertyValue("--playlist-w"), 10);
      if (w) onChange?.(w);
    };
    grip.addEventListener("pointermove", move);
    grip.addEventListener("pointerup", up);
  });

  // 鍵盤也能調，方向鍵每次 24px
  grip.addEventListener("keydown", (e) => {
    const step = e.key === "ArrowLeft" ? 24 : e.key === "ArrowRight" ? -24 : 0;
    if (!step) return;
    e.preventDefault();
    const cur = parseInt(getComputedStyle(player).getPropertyValue("--playlist-w"), 10) || 380;
    apply(cur + step);
    onChange?.(clamp(cur + step));
  });
}
