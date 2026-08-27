# Cloudflare Pages 部署

本專案固定使用 Cloudflare Pages Git integration，不使用 `wrangler pages deploy` 的 Direct Upload 模式。Cloudflare 建立專案後無法在兩種模式間直接切換；Git integration 可保留 GitHub commit 狀態與未來 PR preview。

## Pages 設定

- Repository：`keanu77/shoulder-ultrasound-course`
- Project name：`shoulder-ultrasound-course`
- Production branch：`main`
- Root directory：repository root
- Build command：

  ```bash
  python3 src/build/build.py && python3 src/build/audit.py && python3 src/build/audit_medical.py
  ```

- Build output directory：`dist`

建置腳本只使用 Python 標準函式庫；Ruff 是本機與 GitHub Actions 的開發品質檢查，不是 Pages production build 的必要相依。

## 醫療內容與索引閘門

`course.config.json` 的 `medical.allowIndexing` 預設為 `false`。此時建置會同時輸出：

- HTML `<meta name="robots" content="noindex, follow">`
- Cloudflare `_headers` 的 `X-Robots-Tag: noindex, follow`

若仍有任何單元不是 `approved`，將 `allowIndexing` 改為 `true` 會使 `audit_medical.py` 失敗。只有人工醫療簽核完成後才能解除索引閘門。

## 自訂網域

先確認 `shoulder-ultrasound-course.pages.dev` 的 production deployment 正常，再到 Pages 專案的 Custom domains 加入：

`shoulder-ultrasound.sportsmedicine.tw`

母網域已由 Cloudflare 管理時，應由 Pages 的 Custom domains 流程自動建立 DNS；不要先手動建立 CNAME，以免自訂網域驗證或回源設定不一致。

## 上線 smoke test

- Deployment branch 與 commit SHA 對應 GitHub `main`
- `/`、`course.json`、`og.png`、`robots.txt`、`sitemap.xml`、`llms.txt` 都回 200
- `og.png` 是 1200×630
- canonical、Open Graph 與 sitemap 使用正式網域
- `_headers` 的安全、快取與 `X-Robots-Tag` 實際生效
- HTML 的 CSS／JS、ES module import 與 `course.json` 共用同一個 `?v=<內容指紋>`；即使 zone Browser Cache TTL 覆寫 Pages `_headers`，既有訪客也不會卡在舊版 JavaScript
- 24 個單元、18 支影片、5 支核心必看與 13 支延伸學習載入正常
- 「只看核心必看」在課程與播放清單同步生效；核心模式的上一部／下一部不跳入延伸影片
- 原始內容日期、YouTube 上架日期、適用範圍及廠商揭露顯示正常
- 搜尋、章節展開、進度、明暗模式及 320/390px 行動版正常
- Console 無 JavaScript error、404 或 mixed content

## 時區地雷：`last_verified_at` 不得用台北日期

Cloudflare Pages 的建置伺服器跑在 **UTC**。`audit_medical.py` 會檢查
`last_verified_at` 不得晚於「今天」，而那個「今天」是**建置機的 UTC 日期**。

台北是 UTC+8，所以在**台北時間 00:00–08:00 之間**，本機的今天已經是隔一天，
UTC 還停在前一天。此時把 `last_verified_at` 填成台北日期，本機 `make audit` 全綠，
推上去 CF **一定 build failure**，錯誤訊息是每支片各一行「`last_verified_at` 不得晚於今天」。

2026-08-28 實際踩過：13 支新片全被擋，preview 部署 `f713b1a1` 失敗。

**做法**：`last_verified_at` 一律填**實查當下的 UTC 日期**。要驗證就加 `TZ=UTC` 模擬建置環境：

```bash
COURSE=course DIST=/tmp/dist-cf TZ=UTC python3 src/build/build.py
COURSE=course DIST=/tmp/dist-cf TZ=UTC python3 src/build/audit.py
COURSE=course DIST=/tmp/dist-cf TZ=UTC python3 src/build/audit_medical.py
```

注意 CF 的 build command 用的是**純 `python3`（僅標準函式庫）**，不是 `uv run`；
本機用 `uv` 跑得過不代表 CF 過得了，這兩件事要分開驗。
