# 開發與驗證

## 基本建置

依 README 安裝 Python／uv。程式建置與讀取資料快照不需要 API 憑證；只有重新查詢外部來源或部署才需要相應工具與權限。

## 瀏覽器測試

需要 Node.js 及 Playwright，可安裝在 repo 的暫存目錄：

```bash
npm install --prefix .tmp/browser-tools --no-package-lock playwright@1.62.1
.tmp/browser-tools/node_modules/.bin/playwright install chromium
```

先依 README 啟動本機網站，再於另一終端執行：

```bash
export PLAYWRIGHT_MODULE="$PWD/.tmp/browser-tools/node_modules/playwright"
node tests/test-course-ui.cjs http://127.0.0.1:8899 .tmp/browser-results
```

一般課程的 `test-course-ui.cjs` 目前使用已安裝的 Google Chrome；膝部及主頁使用 Playwright Chromium。測試阻擋／取代外部影片時，只驗網站互動，不代表真實串流通過。

## 資料維護

`make verify` 會連線核對影片／PubMed；`make meta` 等研究工具可能另需 yt-dlp。它們與離線 `make check` 分開，遇到外部來源限制應保留錯誤，不把查核失敗改成成功。

進階資料的原稿、批准副本與正式輸出各有用途。任何內容變更先確認 DATA_AND_REVIEW 與具體批准，不修改受審包去配合新的雜湊。

## 文件更新

README 的數量是具日期的建置快照。調整課程後，從 dist/course.json（主頁為來源快照）重算，並同步資料範圍文件。新增畫面需從實際瀏覽器擷取，不用模擬設計稿代替正式畫面。
