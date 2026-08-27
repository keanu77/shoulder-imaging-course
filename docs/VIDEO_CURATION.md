# 公開影片策展規則

## 優先順序

1. 最近五年內，由學會、學術醫療中心、具名專家或專業訓練機構發布。
2. 能清楚示範 patient position、probe position、掃描方向與正常地標。
3. 內容與目前診斷指引一致，且沒有把診斷與介入操作混在同一教學流程。
4. 影片可由原平台正常播放，並能追溯頻道、標題、日期與 URL。

觀看數不是醫療品質代理指標，因此不設最低觀看數門檻。

## 學習層級

`kind` 表示影片內容型態（總覽、掃描示範、病理判讀、經典大師）；`learning_tier` 另行表示學習優先級，兩者不可混用：

- `core`／核心必看：建立本課程主要掃描路徑，學員應優先觀看並配合實機練習。
- `extension`／延伸學習：補充長篇脈絡、不同講者觀點、特定病灶或 focused protocol。

目前 5 支核心必看為 Jon Jacobson、Marc Schmitz、SMUG 肱二頭肌起始掃描，以及 Carlo Martinoli 的兩部經典解剖影片。其餘 13 支保留為延伸學習，其中本輪指定的重點延伸包括 Don Buford、Sonosite Part 1／2、AIUM 旋轉肌袖判讀與 ABSIS protocol。

網站提供「只看核心必看」快速路徑；這是學習順序，不代表核心影片具有較高證據等級或已通過醫療核准。

## 日期、講者與來源揭露

- `original_content_date`：原始文章、webinar 或內容首次完成日期；未知時明確填 `null` 並提供 `date_note`。
- `upload_date`：目前 YouTube 影片由 yt-dlp 依 UTC 正規化的上架日期；若與頁面所示時區日期跨日，須以 `date_note` 說明，且不得用重上架日期冒充內容年代。
- 近五年門檻優先依 `original_content_date` 判定，未知時才退回 `upload_date`。
- 核心影片必須具名 `presenter`；公開頁面未具名時，必須以 `presenter_note` 說明。
- 廠商教育平台必須提供 `disclosure`，並在 `scope_note` 寫明可學習內容與不可外推的診斷結論。

## 經典例外

早於五年門檻的影片，只有在教學價值難以由近年內容取代時保留，並必須填寫 `classic_exception_reason`。目前 7 支經典例外為：

- Jon A. Jacobson：肩部超音波解剖、技術與掃描陷阱
- Don Buford：13-point 肩部超音波現場實作
- Sonosite：Diagnostic Shoulder Ultrasound Exam Part 1／2（2015 年內容、2023 年重上架）
- AIUM：旋轉肌腱病變與撕裂鑑別
- Prof. Carlo Martinoli：旋轉間隙超音波解剖
- Prof. Carlo Martinoli：旋轉肌袖肌腱的超音波解剖示範

這些影片的「經典」標籤表示策展理由，不等於影片所有陳述都自動獲得醫療核准。

## 狀態

- `provisional`：URL、標題、頻道、長度、內容日期及上架日期已建檔，仍待逐段醫療審閱
- `pending-date-verification`：內容候選可用，但尚未確認發布日期
- `approved`：逐段適用性已由具資格醫師簽核；技術連結驗證本身不會自動提升到此狀態

每次正式發布前應重跑外部連結驗證；影片失效時保留紀錄並替換，不下載或自行重製第三方內容。

---

## 第二輪策展：X 光與 MRI（2026-08-28）

課程由純超音波擴為三模態。本輪只找 X 光與 MRI，超音波不動。

### 方法

同一份 prompt 同時給 **codex** 與 **grok**，兩路獨立、不互看。硬性資格：原始頻道、
具名講者且附可驗證資格證據 URL、可嵌入、有英文字幕、純診斷、90 秒–90 分、
內容 cutoff 2021-08-28（早於此者須附破例理由）。

兩路產出後，**主編逐支實查**（`yt-dlp -j` + YouTube oEmbed），再抓字幕以關鍵字
（`inject|needle|aspirat|steroid|sterile|fluorosc|…`）掃描介入內容並定出框限。

### 結果

| | codex | grok | 收斂 |
|---|---|---|---|
| 提出候選 | 10 | 12 | 4 支兩路都找到 |
| 實查通過 | 3／6（獨有部分） | 12／12 | — |
| 最終採用 | — | — | **13 支** |

grok 這輪 12 支全部通過實查，沒有編造任何影片。

### 拒絕清單

| 影片 | 提出者 | 拒絕理由 |
|---|---|---|
| `C1QXQThXZxs` Normal Shoulder Radiography Take1（Chris Beaulieu, 2010） | codex | **不可嵌入**（`playable_in_embed=false`）。內容本身合格，但掛上站會變成無法播放的死卡。 |
| `9wE7L-tw40U` Shoulder Radiography Fracture Dislocation（Chris Beaulieu, 2010） | codex | **不可嵌入**。同上。 |
| `lpfjcN4q0PM` Tears of the Rotator Cuff Part 2: Identifying Tears on MRI（Jeffrey B. Witty, MD, 2023） | codex | **不可嵌入**。M2 slot 主題吻合，可惜。 |

| `-ZlY-1Wsbd0` Shoulder X-ray interpretation（Radiology Tutorials, 2022） | codex + grok | **查不到合格的講者資格證據**。頻道以「Michael」署名，可連結到 Radiology Tutorials Education Ltd 的 Michael Francois Nel，但 Radiopaedia 個人頁回 402 付費牆，找不到符合資格的大學／醫院／學會頁。X2 slot 另有兩支合格片，依「不降低資格標準湊數」原則剔除。 |
| `EmoCOrqbP2U` Shoulder MRI Anatomy（Radiology Tutorials, 2022） | codex | **同上**，同一講者同一問題。M1 slot 另有兩支合格片，剔除。 |

前三支是靠 `yt-dlp -j` 的 `playable_in_embed` 欄位擋下的——策展 agent 兩路都聲稱
「可嵌入」，實查才發現不是。**這是實查步驟不可委派的直接證據。**

後兩支是資格證據查證階段擋下的：內容品質沒問題，但課程的治理鏈要求每支片都能回答
「這位講者憑什麼教這個」並附第三方可查證來源，做不到就不收。

### 早於 cutoff 而破例收錄

| 影片 | 上架日 | 破例理由 |
|---|---|---|
| `AAm493BgSH8` Shoulder Radiographic Evaluation | 2019-07-13 | 骨科創傷醫師視角逐一示範 Grashey、scapular Y、axillary 為何必要，並接到後脫位、Hill-Sachs 與近端肱骨骨折。近五年內找不到同等長度、可嵌入、具名專家原頻道的肩部標準位向課。 |
| `xspeQczm_mY` Glenoid Labrum: Location matters | 2020-05-18 | 大學放射科原頻道的盂唇經典課，依位置系統講 Bankart、Perthes、ALPSA、reverse Bankart、SLAP 與正常變異。 |
| `R1kG9Mu1at4` MRI Shoulder Arthrography Interpretation and Variants | 2020-07-11 | 醫院 MSK 組原頻道的 MRA 判讀與變異圖譜，涵蓋 sublabral recess／foramen、Buford complex、GLAD、ALPSA、HAGL、Hill-Sachs on-track／off-track。同系列另有注射操作片，未收。 |
| `VLKFpKpCjgQ` How Frozen shoulder looks on MRI | 2020-04-03 | 具名 MSK 專家原頻道的沾黏性關節囊炎 MRI 短講：rotator interval、腋囊厚度、喙肱韌帶。近五年幾乎沒有專講此主題的合格可嵌入片。 |
| `IXCD_BcbgOw` Proximal Humerus Fractures classification | 2011-12-09 | 近端肱骨骨折 Neer 分類的簡明說明，作為 X2 的補充短片。 |

### 介入內容框限（主編逐支掃字幕後裁定）

最終 13 支中 6 支含介入相關內容，全部設 `diagnostic_segment_range` 框限：

| 影片 | 介入起點 | 框限後可播範圍 | 裁定理由 |
|---|---|---|---|
| `gXRiTm5EWm4` | 45:12 | 00:00–45:11 | 45:12 之後為 Q&A，講者描述自身注射配方與進針位置，整段排除。 |
| `UFXRpfK1gHA` | 08:54 | 00:00–08:53、09:20–35:11、36:10–40:24、40:40–42:43 | 三段排除：MRA 進針入路與螢光透視導引、打藥過程、Q&A 問 indirect arthrography IV 注射。 |
| `R1kG9Mu1at4` | 38:35 | 00:00–38:34、38:45–44:05 | 提及注射顯影劑量不足的情境。 |
| `xspeQczm_mY` | 03:21 | 00:00–03:20、03:45–26:22 | 說明 MRA 注射劑量與體積。 |
| `zkhIYmlPgNk` | 02:43 | 00:00–02:42、02:50–41:18 | 說明 MR arthrogram 打顯影劑，屬檢查說明非操作示範，仍框限排除。 |
| `M8xGUNSK3MU` | 07:34 | 00:00–07:33、07:45–09:17 | 提及類固醇注射為保守治療選項，屬治療陳述，為維持 diagnostic-only 一致性排除。 |

其餘 7 支全片字幕掃描無介入關鍵字命中。

### 既有 18 支超音波影片的複查

同時對原有 18 支重跑實查，結果：

- **全部 18 支可嵌入、公開、狀態正常。**
- `W_X5SmLE3gs`（Jon A. Jacobson, RadiologyRSNA, 2015）**沒有任何英文字幕軌**，
  連自動字幕都沒有 → 這支無法產出逐段筆記，且早於 cutoff 十年。留待醫師裁決去留。
- 頻道名稱兩處寫錯：`Global Medical Business` 實際為 `Global Medical Business at Canon Inc.`；
  `AIUM` 實際為 `AIUMultrasound`。
- 片長 ±1 秒、上架日 ±1 天的差異多處，屬 yt-dlp 取整與 UTC 時區差，非錯誤。
- 介入框限複查：9,000 個 cue 中僅 3 處命中介入關鍵字，且都是診斷內容中的順帶提及。
  其中 `eglplbWaqxA` 的 26:10 與 `WzkiVfEg3qw` 的 31:03 是前一段（已排除）的尾音溢入，
  建議框限起點各後推 2 秒。

### 字幕訛誤掃描（本地 LLM）

17 支有字幕的既有影片，逐字稿共 752 KB。機械預篩（字典比對＋詞形還原）得 434 個候選詞，
交本地 `qwen3.8:27b-mlx` 判定，得 263 個字幕訛誤。高頻對照：

`versa`→bursa（64）、`supinatus`／`suppinatus`／`superspinatus`／`spinatus`→supraspinatus（114）、
`fassett`→facet（36）、`infraspanatus`→infraspinatus（30）、`hummeral`→humeral（28）、
`hyperacolic`／`aoic`→hyperechoic（16）、`acromium`→acromion（12）、`corocoid`→coracoid（8）、
`coroumeral`→coracohumeral（8）。

主編抽驗 6 個高頻判定，發現 **1 個錯誤**：`pathak` 應為 **pathologic**（"no Pathak findings"
＝"no pathologic findings"），本地 LLM 誤判為 "Parker"。另 `intra` 是斷字產物
（intra substance／intra muscle），不是單詞訛誤。完整對照表待逐段筆記階段逐支寫入 `note`。

### 講者資格證據（治理鏈）

18 支既有超音波影片與 13 支新片全部走過資格查證：找出講者、寫明職稱與所屬機構、
附上**可驗證的第三方資格證據 URL**（大學／醫院 faculty 頁、學會講者頁、PubMed 作者頁）。
明確排除 YouTube 頻道頁、LinkedIn、維基百科與商業產品頁。

主編逐一實開每個證據 URL 確認姓名出現在頁面，結果：

- **既有 18 支**：17 支有可驗證證據；`ZMkYok_VU9w`（Dr. Sam's Imaging Library）
  只以「Dr. Sam」署名，查不到完整姓名、學位或機構，全部欄位維持 null 待醫師裁決。
- 兩支的證據 URL 原本指向**商業產品頁**（Clarius webinar、Sonosite Institute），
  已換成已驗證的學術／機構頁（SonoSkills 講師 bio、Sharp HealthCare 醫師頁）。
- **新 13 支**：全部有可驗證證據。其中兩支的機構頁受 bot 防護（Cloudflare challenge／
  Akamai 阻擋）無法程式驗證，改用可經 PubMed eutils 驗證的作者證據，並在 `scope_note` 註明原因。

**兩則被否決的 agent「更正」**（留作紀錄，說明為什麼查證要雙向）：

1. 資格查證 agent 主張 `eglplbWaqxA` 的講者應只有 Don Buford、Ben DuBois 是誤植，
   依據是一份 OSET 議程 PDF——但該 PDF 一律回 403 無法開啟。主編改查影片本身，
   說明欄明寫 "performed by Dr. Don Buford **and Dr. Ben DuBois**"，
   **既有的雙講者標註才是對的，agent 的更正是錯的**。維持原值。
2. 同一 agent 為 `WzkiVfEg3qw` 的 J. Antonio Bouffard 提供 PubMed 證據，但引用的是
   一篇**膝部**超音波論文。改用同作者的肩部論文（PMID 10994687
   《Ultrasonography of the shoulder》），對題且同樣可機器驗證。
