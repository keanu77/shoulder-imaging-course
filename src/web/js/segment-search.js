// segment-search.js — 逐段筆記的全文比對與命中標示。
// 刻意不 import 任何東西：這些是純函式，要能直接用 node 測。

const HTML = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

/** 與 render.js 的 esc 同語意，這裡自帶一份以維持本模組零相依。 */
export function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => HTML[c]);
}

/** 把一段逐段筆記攤平成可搜尋的字串：標題、速讀摘要、完整詳解都要能被搜到。 */
export function segmentHaystack(segment) {
  if (!segment) return "";
  const detail = Array.isArray(segment.detail) ? segment.detail.join(" ") : "";
  return `${segment.title || ""} ${segment.summary || ""} ${detail}`.trim();
}

/** 查詢字串正規化：去頭尾空白、轉小寫。空查詢代表「不過濾」。 */
export function normalizeQuery(query) {
  return String(query ?? "").trim().toLowerCase();
}

/** 這一段筆記是否命中查詢。空查詢一律不算命中（避免整頁都被標亮）。 */
export function segmentMatches(segment, query) {
  const q = normalizeQuery(query);
  if (!q) return false;
  return segmentHaystack(segment).toLowerCase().includes(q);
}

/** 一支影片有幾段筆記命中——播放清單用它顯示「筆記 N 段」。 */
export function segmentHitCount(segments, query) {
  const q = normalizeQuery(query);
  if (!q || !Array.isArray(segments)) return 0;
  return segments.filter((s) => segmentMatches(s, q)).length;
}

/**
 * 把命中的字包成 <mark>。
 * 先在原文上找位置、再逐段 escape，避免在已 escape 的字串上比對造成錯位或注入。
 */
export function highlight(text, query) {
  const raw = String(text ?? "");
  const q = normalizeQuery(query);
  if (!q) return escapeHtml(raw);

  const lower = raw.toLowerCase();
  let out = "";
  let from = 0;
  for (;;) {
    const at = lower.indexOf(q, from);
    if (at < 0) break;
    out += escapeHtml(raw.slice(from, at));
    out += `<mark class="Hit">${escapeHtml(raw.slice(at, at + q.length))}</mark>`;
    from = at + q.length;
  }
  return out + escapeHtml(raw.slice(from));
}
