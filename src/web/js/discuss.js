// discuss.js — 每支影片一串 GitHub Discussions（giscus）
import { icon } from "./icons.js";
import { esc, UI } from "./render.js";

const $ = (s, r = document) => r.querySelector(s);

let CFG = null;

export function setDiscussions(cfg) {
	CFG = cfg?.repo ? cfg : null;
}

export const enabled = () => !!CFG;

/** 目前站台主題 → giscus 主題 */
function theme() {
	const dark =
		(document.documentElement.dataset.theme ||
			(matchMedia("(prefers-color-scheme: dark)").matches
				? "dark"
				: "light")) === "dark";
	return dark ? "dark_dimmed" : "light";
}

/** 討論串的識別碼。用 video id，同一支影片跨單元共用同一串。 */
function term(item) {
	return `${CFG.termPrefix || "video"}/${item.vid || item.unitId}`;
}

export function button() {
	if (!CFG) return "";
	return `<button class="btn" data-toggle-discuss type="button">
            ${icon("message-circle", 14)} <span class="Player__btnText">${esc(UI.discussLabel || "討論")}</span>
          </button>`;
}

export function panel() {
	if (!CFG) return "";
	return `<section class="Discuss" id="discussPanel" hidden>
            <div class="Discuss__head">
              ${icon("github", 14)}
              <span>${esc(UI.discussLabel || "討論")}</span>
              <span class="Discuss__note">${esc(UI.discussNote || "")}</span>
            </div>
            <div class="Discuss__body" id="discussBody"></div>
          </section>`;
}

/** 載入（或重載）目前影片的討論串。giscus 每次換片都要重新掛 script。 */
export function mount(item) {
	const body = $("#discussBody");
	if (!CFG || !body || !item) return;

	body.innerHTML = "";
	const s = document.createElement("script");
	Object.entries({
		src: "https://giscus.app/client.js",
		"data-repo": CFG.repo,
		"data-repo-id": CFG.repoId,
		"data-category": CFG.category,
		"data-category-id": CFG.categoryId,
		"data-mapping": CFG.mapping || "specific",
		"data-term": term(item),
		"data-strict": "1",
		"data-reactions-enabled": CFG.reactions === false ? "0" : "1",
		"data-emit-metadata": "0",
		"data-input-position": CFG.inputPosition || "top",
		"data-theme": theme(),
		"data-lang": CFG.lang || "zh-TW",
		"data-loading": "lazy",
		crossorigin: "anonymous",
	}).forEach(([k, v]) => s.setAttribute(k, v));
	s.async = true;
	body.append(s);
}

export function close() {
	const p = $("#discussPanel");
	if (p) p.hidden = true;
	const b = $("#discussBody");
	if (b) b.innerHTML = "";
}

/** 主題切換時同步 giscus */
export function syncTheme() {
	document
		.querySelector("iframe.giscus-frame")
		?.contentWindow?.postMessage(
			{ giscus: { setConfig: { theme: theme() } } },
			"https://giscus.app",
		);
}

// giscus 載入完成才收得到 setConfig。它一 ready 就補發一次，
// 避免「開了討論之後才切主題」或 iframe 比 script 屬性晚就緒造成的不同步。
addEventListener("message", (e) => {
	if (e.origin === "https://giscus.app" && e.data?.giscus)
		setTimeout(syncTheme, 0);
});

// 系統主題變動時（使用者沒手動覆寫的情況）也跟著走
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
	if (!document.documentElement.dataset.theme) syncTheme();
});
