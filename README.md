# 肩部超音波診斷課程

以醫師為主要學員的繁體中文肩部肌肉骨骼超音波課程。第一階段聚焦診斷掃描：儀器最佳化、標準切面、正常解剖、動態檢查、常見病理與報告品質；介入注射延後處理。

正式站預定網址：<https://shoulder-ultrasound.sportsmedicine.tw>

> 目前內容狀態為 `medical-review`。網站可供版型與課綱審閱，但不代表醫療內容已核准，也不取代實體 hands-on training、合格督導或機構 credentialing。審閱範圍與剩餘簽核見 [醫療內容審閱紀錄](docs/MEDICAL_REVIEW.md)。

## 首輪範圍

- 8 章、24 個教學單元、13 支精選公開影片
- 近五年影片優先；具不可替代教學價值者可列為「經典例外」
- 明確保留 Prof. Carlo Martinoli 的旋轉間隙與旋轉肌袖解剖示範
- 以 ACR/AIUM、AIUM、ESSR、USMSIT/NMUSIT 與同儕審查文獻建立掃描框架
- 每單元具備學習目標、必備視圖、操作重點、常見陷阱、評量與審閱狀態

詳細資料見 [課程結構](docs/CURRICULUM.md)、[選片規則](docs/VIDEO_CURATION.md)、[版型設計](docs/DESIGN_SYSTEM.md) 與 [建置計畫](docs/BUILD_PLAN.md)。

Cloudflare Pages 採 GitHub integration，設定與醫療索引閘門見 [部署文件](docs/DEPLOYMENT.md)。

## 本機建置

需要 Python 3.11+ 與 [uv](https://docs.astral.sh/uv/)：

```bash
uv sync
make check
make serve
```

開啟 <http://localhost:8899>。若要驗證外部影片及文獻連結，另執行：

```bash
make verify
```

`make audit` 會同時執行框架稽核與醫療內容結構閘門。通過只代表資料結構完整，不等於醫療核准。

## 內容維護

- `course/course.config.json`：網站、章節、配額、稽核與醫療範圍設定
- `course/data/syllabus.json`：課綱、單元、參考來源與策展影片
- `course/data/video-meta.json`：影片 ID、頻道、長度及驗證中繼資料
- `src/web/`：靜態前端
- `src/build/`：建置、SEO、連結與醫療內容稽核

審閱狀態採 `draft` → `medical-review` → `approved`。任何醫療內容變更都應回到 `medical-review`，不得只改畫面而保留既有核准狀態。

## 來源與授權

本專案參考 [keanu77/online-course](https://github.com/keanu77/online-course) 的資料驅動靜態課程架構重新建置。程式碼採 MIT License；第三方影片、學會指引及論文不包含在此授權內。本站只儲存連結與書目中繼資料，影片由 YouTube 官方播放器提供，不重製或代管。
