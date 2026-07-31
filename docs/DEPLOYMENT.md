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
- 24 個單元、13 支影片、2 支 Martinoli 經典影片載入正常
- 搜尋、章節展開、進度、明暗模式及 320/390px 行動版正常
- Console 無 JavaScript error、404 或 mixed content
