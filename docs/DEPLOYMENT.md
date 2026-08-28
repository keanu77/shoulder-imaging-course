# Cloudflare Pages 部署

本專案固定使用 Cloudflare Pages Git integration，不使用 `wrangler pages deploy` 的 Direct Upload 模式。Cloudflare 建立專案後無法在兩種模式間直接切換；Git integration 可保留 GitHub commit 狀態與未來 PR preview。

## Pages 設定

- Repository：`keanu77/shoulder-imaging-course`（**public**，2026-08-29 起）
- Project name：`shoulder-ultrasound-course`
  **CF Pages 專案名不會跟著 repo 改名，維持原值。** 這個名字同時是
  `course.config.json` 的 `site.project`，並驅動瀏覽計數器的 D1 資料庫名
  `shoulder-ultrasound-course-hits`——**改了會讓現有資料庫變孤兒**。
  CF Pages 以 `repo_id` 綁定 GitHub，改名不影響自動部署（膝部站與本站均已實測）。

### ⚠️ 開源時換過 repo：Git integration 需重新綁定

2026-08-29 開源時**建了新 repo 推乾淨歷史**，不是把原 repo 轉 public。原因：原 repo 的
`refs/pull/5/head` 保留著一個已從歷史移除的 commit，GitHub 的 PR ref 由 GitHub 管理、
`git push --delete` 刪不掉，repo 一公開該 PR 頁面就會顯示完整 diff。

| repo | 狀態 | 用途 |
| --- | --- | --- |
| `keanu77/shoulder-imaging-course` | **public** | 開源用，歷史乾淨（0 PR refs） |
| `keanu77/shoulder-imaging-course-archive` | private | 改名前的原 repo，保留 CF `repo_id` 綁定與完整開發歷史 |

**新 repo 有新的 `repo_id`，CF Pages 不會自動跟著換**——Git integration 仍指向 archive。
在 CF dashboard 完成改綁之前，**推 public repo 不會觸發部署**，要推 archive 才會。
改綁後記得把 archive 的 webhook 停掉，避免兩邊都部署。

本地 remote 慣例：`origin` = public repo，`old` = archive。
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

若仍有任何單元不是 `approved`，將 `allowIndexing` 改為 `true` 會使 `audit_medical.py` 失敗。只有策展審閱完成後才能解除索引閘門。

## 自訂網域

先確認 `shoulder-ultrasound-course.pages.dev`（CF 專案名，非 repo 名）的 production deployment 正常，再到 Pages 專案的 Custom domains 加入：

`shoulder-imaging.sportsmedicine.tw`（2026-08-28 起的正式網址）

**舊網域 `shoulder-ultrasound.sportsmedicine.tw` 仍掛在同一個 Pages 專案上，不要拔掉。**
它在改名前已被搜尋引擎索引，直接移除會留下死連結。兩個網域都指向同一個 Pages 專案，
內容相同，且 HTML 的 `<link rel="canonical">` 已指向新網址——搜尋引擎會把權重收斂過去。

### ⚠️ `_redirects` 做不到舊網域轉新網域（2026-08-28 實測確認）

本專案曾在 `src/web/_redirects` 放過這條規則：

```
https://shoulder-ultrasound.sportsmedicine.tw/* https://shoulder-imaging.sportsmedicine.tw/:splat 301
```

**它永遠不會生效，檔案已移除。** Cloudflare Pages 的 `_redirects`
[官方文件](https://developers.cloudflare.com/pages/configuration/redirects/)
在 advanced redirects 表格中把 **Domain-level redirects 標為 ❌**，
來源欄只接受**檔案路徑**，不接受絕對 URL。

**不要用 `curl /_redirects` 判斷檔案在不在。** CF Pages 會把 `_headers` 與 `_redirects`
消耗掉，兩個路徑都回 **200 + SPA fallback 的 index.html**——檔案存在或不存在，
回應長得一模一樣。2026-08-28 曾據此誤判成「CF 沒把 `_redirects` 當設定檔消化」。

診斷方法（值得記著，因為兩個檔的行為不同）：
- `_headers` 的規則**有生效**（`curl -D-` 看得到 `x-content-type-options` 等三個標頭）
  → 證明 CF 確實有讀這兩個設定檔，問題不在部署或路徑
- 舊網域根路徑回 **200 而不是 301** → 規則被讀了但不適用
- `/checklist.html` 回 308 是 **CF Pages 內建的去副檔名轉址**，不是我們的規則，別誤判成成功

**真的要轉址就用 zone 層級的 Redirect Rule**（不在 Pages 專案裡）：
Cloudflare dashboard → 選 `sportsmedicine.tw` → Rules → Redirect Rules → Create rule
- 條件：`Hostname` equals `shoulder-ultrasound.sportsmedicine.tw`
- 動作：Dynamic redirect，Expression `concat("https://shoulder-imaging.sportsmedicine.tw", http.request.uri.path)`
- 狀態碼 301，勾 Preserve query string

規模大時改用 Bulk Redirects。**wrangler 的 OAuth token 做不到**——它沒有 zone 權限
（2026-08-28 實測連 `GET /zones` 都回 `Invalid access token`），只能由使用者在 dashboard 操作。

### DNS

**自訂網域的 CNAME 要使用者手動到 dashboard 加**（2026-08-28 實測）。
在 Pages 專案 `POST .../domains` 加了自訂網域之後，狀態會停在 `pending`，
**DNS 紀錄不會自動長出來**；手動加完 CNAME（`<子網域>` → `<CF專案名>.pages.dev`，Proxied）
約 80 秒就會從 522 轉成 200。

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
