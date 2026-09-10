# Repository 整備紀錄

日期：2026-09-10。範圍是專案分享、文件與可維護性；本次沒有擴充教材或新增臨床批准。

- GitHub：`keanu77/shoulder-imaging-course`；可見性維持 `PUBLIC`。系列只有肩部、膝部公開，其他五部位與主頁 repo 私有。
- 整備前版本：`8ea9045be1ae703b7da4183310c1724a47771e94`。
- README 已補學習入口、真實桌機／手機截圖、資料數量及系列網站。
- 補齊授權範圍、第三方聲明、CITATION.cff、貢獻與安全回報規則、Issue／PR 範本、開發、Fork 與部署說明。
- 新文件的本機連結已核對；引用檔通過 cffconvert 的 CFF 1.2.0 schema 驗證。
- make check 通過；course/ 全部檔案 SHA-256 與整備前一致。
- Git 歷史已在 fetch 遠端分支與 tags 後，用 Gitleaks 8.30.1 掃描 `--all` 可達歷史，未發現符合規則的憑證。掃描輸出使用完整遮罩。

## 驗證界線

憑證掃描不涵蓋 GitHub 已刪除物件、隱藏 PR refs、Actions 日誌與 artifacts，也不等於人工完成所有個資或素材授權審核。既有影片 metadata 及醫療研究未在本次重新查證；資料現況見 [DATA_AND_REVIEW](DATA_AND_REVIEW.md)。

教材沿用原有授權；第三方內容不因 repo 公開而取得重製權。歷史研究、批准與稽核檔保留原文，由文件索引區分歷史與目前操作說明。未變更正式教材、批准檔、索引設定與網站功能。

發布版本以 Git 提交、GitHub Actions 與 Cloudflare 正式 deployment 的 commit 為準；發布驗證記錄由維護者存放於系列工作區，不把尚未發生的部署結果寫成已通過。
