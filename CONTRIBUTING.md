# 貢獻指南

這個 repo 同時裝著兩種東西，貢獻政策不一樣：**引擎（程式碼）歡迎 PR，課程內容不接受 PR。**

## 歡迎的貢獻

建置與前端相關的一切：

- `src/build/` — 建置、SEO、稽核腳本
- `src/web/` — 靜態前端（CSS、JS）
- `tools/` — 策展與逐段筆記的工作腳本
- `tests/` — 測試
- `functions/` — Cloudflare Pages Functions
- 文件的錯字、連結失效、說明不清

送 PR 前請跑：

```bash
uv sync
make check      # lint + jscheck + test + build + audit
```

`make check` 必須全綠。**不要為了讓稽核通過而放寬閘門**——
`src/build/audit_medical.py` 的檢查項是刻意嚴格的，繞過它等於拆掉這個專案的核心。
如果你認為某條規則有誤，開 issue 討論規則本身，不要在 PR 裡改寬它。

## 不接受的貢獻

**課程內容不接受外部 PR**，包括：

- `course/data/syllabus.json` — 影片策展、單元教材、參考文獻
- `course/data/{segments,questions,glossary}.json` — 逐段筆記、知識檢核、名詞表
- `course/course.config.json` 的醫療與文案設定
- 任何 `review_status`、`reviewed_by`、`reviewer_role` 欄位

原因是治理上的，不是不歡迎：`approved` 代表**具名策展人**確認過範圍框限、
來源與講者資格、文獻對應與課程編排。策展人為這件事具名負責，
所以不能由外部 PR 代為變更。

**發現內容有問題請開 issue**，這非常有價值。特別是：

- 影片內容與現行文獻不符（曾發生：某支影片把 on-track／off-track 的風險講反，
  見 `docs/VIDEO_CURATION.md`）
- 解剖名詞、側別或方向錯誤
- 逐段筆記的時間碼對不上影片內容
- 文獻引用的 PMID、年份或結論有誤

請附上**具體位置**（影片 id 與時間碼、或單元 id）與**依據**。

## Fork 與改作

MIT 授權涵蓋程式碼，**不涵蓋第三方影片、學會指引與論文**（見 [`NOTICE.md`](NOTICE.md)）。

fork 去做自己部位的課程站時，**必須移除所有審閱紀錄**
（`reviewed_by` / `reviewer_role` / `reviewed_at` / `reviewed_commit`），
並把 `review_status` 全部改回 `draft`。
不得讓改作內容看起來像是由原策展人審閱過。

## 回報安全問題

不要開公開 issue。請用 GitHub 的 Security advisory 私下回報。
