// pictograms.js — 可由課程 config 選用的通用影像／探頭線稿。
// 只提供不綁定部位的視圖語彙；解剖定向圖必須另經醫療審核後再加入。

const symbol = (id, inner) =>
  `<symbol id="p-${id}" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${inner}</symbol>`;

const SYMBOLS = [
  symbol(
    "ultrasound-longitudinal",
    '<path d="M9 11 H39 L35 18 H13 Z" /><path d="M24 18 V39" stroke-dasharray="3 3" /><path d="M15 39 H33" />',
  ),
  symbol(
    "ultrasound-transverse",
    '<path d="M11 9 V19 L18 23 V13 Z" /><path d="M18 16 H39" stroke-dasharray="3 3" /><ellipse cx="31" cy="31" rx="9" ry="5" />',
  ),
  symbol(
    "radiograph-projection",
    '<path d="M8 24 H28" /><path d="M24 20 L28 24 L24 28" /><rect x="34" y="11" width="5" height="26" rx="1" />',
  ),
  symbol(
    "cross-sectional-plane",
    '<ellipse cx="24" cy="24" rx="16" ry="9" /><path d="M8 24 H40" stroke-dasharray="3 3" /><path d="M24 8 V40" stroke-dasharray="3 3" />',
  ),
];

const PICTOGRAM_IDS = new Set([
  "ultrasound-longitudinal",
  "ultrasound-transverse",
  "radiograph-projection",
  "cross-sectional-plane",
]);

export const CHAPTER_PICTOGRAM = {};

export function configurePictograms(chapters = []) {
  for (const key of Object.keys(CHAPTER_PICTOGRAM)) delete CHAPTER_PICTOGRAM[key];
  for (const chapter of chapters) {
    if (chapter?.code && PICTOGRAM_IDS.has(chapter.pictogram)) {
      CHAPTER_PICTOGRAM[chapter.code] = chapter.pictogram;
    }
  }
}

export function mountPictograms() {
  if (document.getElementById("course-pictogram-sprite")) return;
  const host = document.createElement("div");
  host.id = "course-pictogram-sprite";
  host.hidden = true;
  host.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg">${SYMBOLS.join("")}</svg>`;
  document.body.prepend(host);
}
