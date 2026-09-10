# 2026-09-10 Repo 文件整備

- 原始碼可見性：PUBLIC；依使用者指示，只公開肩部與膝部，其餘維持私有。
- 現行入口：https://shoulder-imaging.sportsmedicine.tw/；系列首頁：https://imaging-course-hub.sportsmedicine.tw/。
- README、引用、貢獻、安全回報、資料範圍、開發、部署與改作說明已整理。歷史說明見 docs/COURSE_GUIDE.md；其他日期報告維持歷史用途。
- 本次不新增教材、不刷新醫療審閱、不更動搜尋索引。資料以 course 原始檔 SHA 比對確認。
- 最終驗證與部署摘要見 docs/REPOSITORY_READINESS.md。

以下保留之前交接；其中網址、可見性與未發布狀態可能已過期，以本段和現行文件為準。

# 2026-09-10 學習站正式網域

- 主頁正式網址：https://imaging-course-hub.sportsmedicine.tw/。課程返回按鈕與主頁 canonical 同步更新。
- 各公開頁面提供推薦影片／文獻入口，沿用 injury.sportsmedicine.tw/contribute/；網址 context 帶入課程頁面，主課程含目前單元。
- 延續預設深色與既有教材審閱狀態。發布及驗證紀錄見工作區 HANDOFF 與 hub-domain-*.json。

# 2026-09-10 預設深色與返回主頁

- 首次造訪預設深色；即使系統偏好淺色、無儲存權限或無 JavaScript 亦然。原有深淺切換與有效偏好繼續保留。
- 七個課程網站左上方新增「← 學習站首頁」，連到 https://imaging-course-hub.pages.dev/；檢核表與已發布進階頁同步提供。
- 檢核表採深色螢幕顯示、白底列印。膝部純靜態單元講義維持無 JS、固定深色，主頁外連延續新分頁規則。
- 教材、策展批准與醫療審閱狀態未改。八站實際品質檢查及瀏覽器驗證均通過，證據為 ../imaging-design-audit-2026-09-09/dark-default-checks-final.json 與 dark-default-browser-0.json；舊失敗報告保留。
- 最終部署 SHA 與狀態見工作區 ../.claude/HANDOFF.md。

# 2026-09-10 搬移與發布進行中

工作路徑：`/Users/ethanstudio/Documents/Vobe coding/shoulder-ultrasound-course`。使用者已要求推送 GitHub 與部署 Cloudflare；正在核對實際上線 commit。以下為歷史工作記錄。髖／踝足進階研究包仍保留 draft，不視為新增策展批准。

# HANDOFF — 2026-09-09 — 肩部課程優化與進階教材

## 目前狀態

- Repository: `/Users/ethanstudio/Projects/shoulder-ultrasound-course`；branch `main`；base commit `ec050583749f830d2fbf36c18419107c6b70e732`。
- 使用者授權繼續優化其他 imaging courses 並重新搜尋、補足進階內容。使用者已說「審核通過，commit and push」；本輪已整合核准副本，接續完成 Git／部署驗證。
- 本站既有 34 單元／34 支不重複影片，原有 8 份內容 SHA 均未改變。保留原 approved/indexable 狀態；新增教材 approved 副本已整合。

## 已完成

- `src/web/index.html`、`src/web/js/{app,player,render}.js`、`src/web/css/course-guide.css`：導覽、深連結、手機版、播放器與載入錯誤復原；肩部段落跳轉事件修復。
- `course/research/2026-09-09-advanced/package.json`：3 個進階單元、9 題、6 個病例／報告練習。已核准副本正式輸出於 /advanced/ 及各單元講義；原始 draft 保留不動。
- `tools/build_advanced_review.py`、`tools/advanced-review/`：獨立可互動預覽，僅本機儲存、自評解析、可列印、拒絕 dist/public。
- 三鏡頭獨立審閱及 Pass 2 完成；0 未解決問題，並非臨床簽核。來源圖面已由主編核對。
- `make check` 通過：68 既有 + 14 新增 Python 檢查；課程 UI 27 情境，新教材 19 情境通過。

## 核對包與紀錄

- package SHA-256：`b6826006f1b15b0d49b51f8d6732397091827d363c2cb88e50ab8e0d36fec202`；clinical_approval 為 null。
- `docs/CONTENT_QUALITY_REVIEW_2026-09-09.md`：內容是否足夠、證據、缺口、重建命令。
- `docs/reviews/2026-09-09/`：三鏡頭初審／Pass 2、validation.json、原內容 SHA 及原圖定位核對。
- 未完成完整 DICOM／盲測／專家評分效度；本次未重新進行真實影片串流驗收。不可宣稱已達「頂尖認證」或所有影片完整驗收。

## 預覽

- 既有課程：http://127.0.0.1:8916/?tab=home
- 新增教材：http://127.0.0.1:8920/shoulder/
- 常駐 server 是本機暫存程序；退出後依內容報告重建。四站列表：cervical 8913、lumbar 8914、wrist 8915、shoulder 8916；新教材共用 8920。

## 下一個 session 前三步

1. **執行** `git status --short` 與 `shasum -a 256 course/research/2026-09-09-advanced/package.json`，核對修改範圍與本包版本，勿沿用舊審閱到不同 hash。
2. **重建並打開** `python3 tools/build_advanced_review.py --output .tmp/advanced-review --base-url http://127.0.0.1:8916`，依使用者對具體教材的審閱修訂。本包已獲使用者批准，勿重問；後續髖與踝足新稿屬另一批。
3. **依本次已授權 release 執行** scoped commit/push、CI 與正式站資產／互動比對；若只有內容修訂授權，保持獨立草稿預覽。

## 其他

不需 migration 或新環境變數。未修改 D1、project、remote、SEO 審閱閘門、原 unit/video ID。相鄰課程各自獨立 repository；不得把本站收錄或發布授權擴張到其他站。

## 本輪續接

- 已核准整合詳見 `docs/RELEASE_2026-09-09.md`。Git／平台最終結果須以實際 HEAD、origin/main 與部署紀錄核對。
- 新指示：另補髖、踝足進階教材；七站影片清單最近十年優先，經典例外另列。全站影片審查資料在同層 `imaging-course-review-2026-09-09/`。


## 2026-09-09：運動醫學品牌設計與統合入口（未發布）

- 使用者要求 multi-llm audit 後優化七站，並新增統合課程主頁。
- 本輪 src/web/css/sports-medicine.css 統一藍白／深藍與珊瑚色視覺；首頁、課程側欄、章節、篩選、焦點與手機入口已調整。index/app 修復當前視圖 SkipLink、首頁 CTA 焦點；六站另修復 JSON 格式主題保存。
- course/ 全部檔案 SHA-256 與本輪起始相同。沒有改變醫療狀態、核准、索引政策或研究包。
- Codex gpt-6-astra、Gemini（CLI 指定 gemini-3.1-pro-high）、本機 qwen3.8:27b-mlx 實際執行；18 項 Pass 2：../imaging-design-audit-2026-09-09/PASS2.md。
- make check 七站通過；版型 168 組、操作 49 項、系統／手動主題 28 組；六站完整 UI 回歸與膝站 14 項 browser smoke 通過。影片 fixture 測試不代表真實串流驗證。
- 統合主頁 ../imaging-course-hub/；http://127.0.0.1:8940/preview/ 可進七個本機新版；/dist/ 連往已核對的線上網址。稽核與比較頁 http://127.0.0.1:8941/。
- 新設計與主頁未 commit、push、部署，尚未設定統合主網域；前一批發布批准不視為本輪新增內容的臨床簽核。先前原有 dirty files 保留。


## 2026-09-10：移除裝飾邊框與影片來源目錄（未發布）

- 使用者不希望截圖所示的圓角白框／粗藍頂邊；已在共用 sports-medicine.css 移除首頁引導、閱讀標頭、進階入口與章節標題的同類裝飾。
- 主頁更名「運動醫學影像學習站」，新增七站主要影片來源及逐片重要性，134 筆核心收錄／132 支影片／39 個發布頻道，另可切換完整 251 筆。
- 最新主頁 http://127.0.0.1:8940/preview/；來源 http://127.0.0.1:8940/preview/sources.html；來源頁可下載主要／完整 CSV。
- 影片 metadata 仍是 2026-09-09 快照；本次未變更 course 資料或審閱狀態。既有缺少講者／資格資訊明示待補查。
- 七站重新建置、168 組版面、49 項操作及主頁／來源頁瀏覽器測試通過；84 個 course 檔案 SHA-256 不變。詳見 ../imaging-course-hub/docs/UPDATE-2026-09-10.md。
- 本輪仍是未發布的本機修改，沒有新增 commit／push。
