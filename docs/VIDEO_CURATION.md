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
