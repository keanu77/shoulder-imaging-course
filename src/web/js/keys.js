// keys.js — 站內鍵盤快捷鍵。iframe 跨域，所以透過 YouTube IFrame API 的 postMessage 控制。
import { icon } from "./icons.js";

const $ = (s, r = document) => r.querySelector(s);

// 由 infoDelivery 事件持續更新，供 seek/volume 這類需要現值的指令使用
const st = { time: 0, duration: 0, rate: 1, volume: 100, muted: false, playing: false };

function frame() {
  return $("#ytFrame");
}

function send(func, args = []) {
  const f = frame();
  if (!f?.contentWindow) return false;
  f.contentWindow.postMessage(
    JSON.stringify({ event: "command", func, args }),
    "https://www.youtube-nocookie.com",
  );
  return true;
}

/** 訂閱播放器狀態；每次換片後要重新呼叫 */
export function listen() {
  const f = frame();
  if (!f?.contentWindow) return;
  f.contentWindow.postMessage(
    JSON.stringify({ event: "listening", id: "ytFrame", channel: "widget" }),
    "https://www.youtube-nocookie.com",
  );
}

addEventListener("message", (e) => {
  if (!e.origin.includes("youtube")) return;
  let d;
  try {
    d = typeof e.data === "string" ? JSON.parse(e.data) : e.data;
  } catch {
    return;
  }
  const info = d?.info;
  if (!info) return;
  if (typeof info.currentTime === "number") st.time = info.currentTime;
  if (typeof info.duration === "number") st.duration = info.duration;
  if (typeof info.playbackRate === "number") st.rate = info.playbackRate;
  if (typeof info.volume === "number") st.volume = info.volume;
  if (typeof info.muted === "boolean") st.muted = info.muted;
  if (typeof info.playerState === "number") st.playing = info.playerState === 1;
});

const seek = (delta) => send("seekTo", [Math.max(0, st.time + delta), true]);
const setRate = (dir) => {
  const steps = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];
  const i = steps.indexOf(st.rate);
  const next = steps[Math.min(steps.length - 1, Math.max(0, (i < 0 ? 3 : i) + dir))];
  st.rate = next;
  send("setPlaybackRate", [next]);
  toast(`${next}×`);
};

function toast(text) {
  let el = $("#ytToast");
  if (!el) {
    el = document.createElement("div");
    el.id = "ytToast";
    el.className = "YtToast";
    $(".Player__frame")?.append(el);
  }
  el.textContent = text;
  el.classList.add("is-on");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove("is-on"), 900);
}

/* --- 快捷鍵說明 ---------------------------------------------------------- */

const SHEET = [
  ["播放", [["Space / K", "播放或暫停"], ["J", "倒退 10 秒"], ["L", "快轉 10 秒"], ["← / →", "±5 秒"], ["0–9", "跳到影片 0%–90%"]]],
  ["聲音與畫面", [["M", "靜音切換"], ["↑ / ↓", "音量 ±10"], ["F", "全螢幕"], ["Shift + . / ,", "加速／減速"]]],
  ["課程導覽", [["Shift + N", "下一部影片"], ["Shift + P", "上一部影片"], ["/", "搜尋"], ["?", "顯示這張表"]]],
];

function toggleSheet(force) {
  let el = $("#keySheet");
  if (!el) {
    el = document.createElement("div");
    el.id = "keySheet";
    el.className = "KeySheet";
    el.innerHTML = `
      <div class="KeySheet__box" role="dialog" aria-label="鍵盤快捷鍵">
        <div class="KeySheet__head">
          ${icon("info", 16)}<strong>鍵盤快捷鍵</strong>
          <button class="btn btn-invisible btn-icon" data-close type="button">${icon("x", 16)}</button>
        </div>
        <div class="KeySheet__cols">
          ${SHEET.map(
            ([group, rows]) => `
            <div>
              <div class="KeySheet__group">${group}</div>
              ${rows.map(([k, d]) => `<div class="KeySheet__row"><kbd>${k}</kbd><span>${d}</span></div>`).join("")}
            </div>`,
          ).join("")}
        </div>
        <p class="KeySheet__foot">播放控制透過 YouTube 播放器 API 送出；點進影片後也可直接用 YouTube 原生快捷鍵。</p>
      </div>`;
    el.addEventListener("click", (e) => {
      if (e.target === el || e.target.closest("[data-close]")) el.classList.remove("is-on");
    });
    document.body.append(el);
  }
  el.classList.toggle("is-on", force ?? !el.classList.contains("is-on"));
}

/* --- 綁定 ---------------------------------------------------------------- */

export function bindKeys({ next, prev, isPlayerTab }) {
  addEventListener("keydown", (e) => {
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName)) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;

    if (e.key === "?" || (e.shiftKey && e.key === "/")) {
      e.preventDefault();
      return toggleSheet();
    }
    if (e.key === "Escape") return toggleSheet(false);

    // 換片不限分頁，其餘播放控制只在上課模式生效
    if (e.shiftKey && (e.key === "N" || e.key === "n")) return e.preventDefault(), next();
    if (e.shiftKey && (e.key === "P" || e.key === "p")) return e.preventDefault(), prev();
    if (!isPlayerTab() || !frame()) return;

    const k = e.key;
    if (k === " " || k === "k" || k === "K") {
      e.preventDefault();
      send(st.playing ? "pauseVideo" : "playVideo");
      st.playing = !st.playing;
    } else if (k === "j" || k === "J") { e.preventDefault(); seek(-10); toast("−10 秒"); }
    else if (k === "l" || k === "L") { e.preventDefault(); seek(10); toast("+10 秒"); }
    else if (k === "ArrowLeft") { e.preventDefault(); seek(-5); toast("−5 秒"); }
    else if (k === "ArrowRight") { e.preventDefault(); seek(5); toast("+5 秒"); }
    else if (k === "m" || k === "M") {
      e.preventDefault();
      send(st.muted ? "unMute" : "mute");
      st.muted = !st.muted;
      toast(st.muted ? "靜音" : "取消靜音");
    } else if (k === "ArrowUp" || k === "ArrowDown") {
      e.preventDefault();
      const v = Math.max(0, Math.min(100, st.volume + (k === "ArrowUp" ? 10 : -10)));
      st.volume = v;
      send("setVolume", [v]);
      toast(`音量 ${v}`);
    } else if (k === "f" || k === "F") {
      e.preventDefault();
      const box = $(".Player__frame");
      document.fullscreenElement ? document.exitFullscreen() : box?.requestFullscreen?.();
    } else if (e.shiftKey && (k === ">" || k === ".")) { e.preventDefault(); setRate(1); }
    else if (e.shiftKey && (k === "<" || k === ",")) { e.preventDefault(); setRate(-1); }
    else if (/^[0-9]$/.test(k) && st.duration) {
      e.preventDefault();
      send("seekTo", [st.duration * (+k / 10), true]);
      toast(`${+k * 10}%`);
    }
  });
}
