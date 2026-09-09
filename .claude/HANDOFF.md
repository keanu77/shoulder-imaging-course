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
