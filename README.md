# 肩部影像診斷課程

以醫師為主要學員的繁體中文肩部影像判讀課程，涵蓋 **X 光、肌肉骨骼超音波與 MRI** 三種模態。
全課為診斷判讀，不含注射、穿刺或其他影像導引介入操作的教學。

正式站：<https://shoulder-imaging.sportsmedicine.tw>

**9 章 · 34 個教學單元 · 34 支精選公開影片 · 16 小時 6 分 · 414 段逐段筆記**

> **這是策展彙編，不是醫療背書。** 影片來自各原始頻道，著作權與臨床內容責任屬原發布單位與講者。
> 策展人負責的是篩選、範圍框限、來源與講者資格查證、文獻對應與課程編排。
> 本課不是 credentialing，也不取代實體 hands-on training、合格督導或正式影像判讀報告。

## 課程結構

依 **X 光 → 超音波 → MRI** 三大主軸編排：

| 章 | 主題 | 單元 |
| --- | --- | ---: |
| `XR1` | X 光：照射位選擇與系統性判讀 | 2 |
| `XR2` | X 光：常見病理與判讀陷阱 | 2 |
| `US1` | 超音波基礎：診斷範圍、安全與影像最佳化 | 6 |
| `US2` | 超音波前側：標準流程、肱二頭肌與肩胛下肌 | 6 |
| `US3` | 超音波上外側與後側：旋轉間隙、棘上肌與動態檢查 | 6 |
| `US4` | 超音波判讀、報告與品質 | 6 |
| `MR1` | MRI：序列邏輯與正常解剖 | 2 |
| `MR2` | MRI：旋轉肌袖與證據邊界 | 2 |
| `MR3` | MRI：盂唇、不穩定與常見陷阱 | 2 |

每個單元具備學習目標、必備視圖、操作重點、常見陷阱、評量與審閱狀態。
詳見 [課程結構](docs/CURRICULUM.md)。

## 這個 repo 有什麼值得參考

課程內容本身是策展成果，**真正可以借用的是治理機制**——如何在大量引用第三方影片的前提下，
維持可追溯、可稽核、且不誇大的醫學教育內容。

**審閱閘門**
`draft → medical-review → approved`。只有 `approved` 的內容會進入 `course.json`。
單元、逐段筆記、知識檢核與名詞表各有獨立狀態，新增內容一律從 `draft` 開始，
不影響既有審閱。`reviewer_role` 是「課程策展人」而非醫療專科職稱——
**審閱確認的是範圍框限與來源資格，不是對第三方臨床內容的背書**。

**影片可追溯性**
每支影片有約 26 個 provenance 欄位：原始頻道、具名講者、**可驗證的第三方資格證據 URL**
（大學／醫院 faculty 頁、學會講者頁、PubMed 作者頁）、來源權威層級、可嵌入與公開狀態、
實查日期。缺欄位會被 `src/build/audit_medical.py` 擋下。

**介入內容框限**
課程是 `diagnostic-only`。影片若含介入段落，以 `intervention_start_timestamp` 與
`diagnostic_segment_range` 切出可播範圍，逐段筆記也止於框限。
框限由字幕關鍵字掃描（`tools/scan_intervention.py`）定位、再逐字核對前後文裁定——
自動字幕會把肌腱 **insertion（止點）** 誤辨成 injection，直接信關鍵字會產生假警報。

**文獻驗證**
`reference_catalog` 的每一筆都以 PubMed eutils 實查過 PMID、標題與年份。
`make verify` 會打真 API 重驗所有影片連結與文獻來源。

**策展決策留痕**
[`docs/VIDEO_CURATION.md`](docs/VIDEO_CURATION.md) 記錄每一輪策展的**拒絕清單與理由**、
早於內容 cutoff 的破例理由、介入框限的裁定依據，以及被否決的建議。
未來要回答「為什麼沒收這支」時，答案在那裡。

## 本機建置

需要 Python 3.11+ 與 [uv](https://docs.astral.sh/uv/)：

```bash
uv sync
make check      # lint + jscheck + test + build + audit
make serve      # http://localhost:8899
make verify     # 打真實 API 重驗影片連結與 PubMed 引用
```

`make audit` 執行框架稽核與醫療內容結構閘門。**通過只代表資料結構完整，不等於內容正確。**

Cloudflare Pages 採 GitHub integration，設定與索引閘門見 [部署文件](docs/DEPLOYMENT.md)。

## 內容維護

| 路徑 | 內容 |
| --- | --- |
| `course/course.config.json` | 網站文案、章節、配額、稽核與醫療範圍設定 |
| `course/data/syllabus.json` | 課綱、單元、參考文獻與策展影片 |
| `course/data/{segments,questions,glossary}.json` | 逐段筆記、知識檢核、名詞表 |
| `course/data/video-meta.json` | 影片實查中繼資料 |
| `course/research/` | 策展原始輸出與字幕訛誤對照表 |
| `src/web/` | 靜態前端 |
| `src/build/` | 建置、SEO、連結與醫療內容稽核 |
| `tools/` | 策展與逐段筆記的工作腳本（實查、框限掃描、逐字稿裁切、字幕密度與訛誤預篩、初稿驗證與併檔）——見 [`tools/README.md`](tools/README.md) |

## 來源與授權

參考 [keanu77/online-course](https://github.com/keanu77/online-course) 的資料驅動靜態課程架構重新建置。

程式碼採 MIT License。**第三方影片、學會指引及論文不包含在此授權內**——
本站只儲存連結與書目中繼資料，影片由 YouTube 官方播放器提供，不重製也不代管。

審閱紀錄（`reviewed_by` / `reviewer_role` / `reviewed_at`）**不隨授權轉移**。
fork 或改作時必須移除這些欄位，不得聲稱原策展人為改作內容背書。
