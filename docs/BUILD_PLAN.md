# 建置與上線計畫

## 成功條件

1. 醫師能依固定順序完成肩部診斷超音波的標準掃描學習。
2. 每個單元都能回答：要取得哪些視圖、如何操作、哪裡最容易誤判、依據是什麼。
3. 所有公開影片均保留原始來源、原始內容日期、YouTube 上架日期、選片理由、適用範圍及最後驗證日。
4. 正式站在醫療審閱前不把 `draft` 內容呈現為已核准教材。

## 里程碑

### M1 — 可審閱骨架

- 建立 8 章、24 單元課綱與 18 支影片（5 支核心必看、13 支延伸學習）
- 完成臨床工作站版型、影片播放器、搜尋與學習進度
- 加入資料結構、醫療欄位、影片與來源稽核
- 建立 GitHub repository 與 CI

### M2 — 醫療內容審閱

- [x] 逐單元核對 ACR/AIUM、AIUM、ESSR 與台灣指引
- [x] 確認 probe position、patient position、required views 與常見假影
- [x] 確認每支影片的日期與講者／機構來源
- [ ] 由具資格醫師逐段觀看第三方影片並完成最終內容適用性簽核
- [ ] 將人工簽核通過的單元由 `medical-review` 提升至 `approved`

### M3 — 正式站部署

- 建立 Cloudflare Pages 專案並連結 GitHub
- 驗證 `shoulder-ultrasound.sportsmedicine.tw` 的 DNS、TLS 與 redirect
- 跑 production smoke test、手機版與無障礙檢查
- 僅在核准內容比例達到上線門檻後公開索引

### M4 — 第二階段

- 病例影像與 formative assessment
- 教師審閱紀錄與內容版本歷程
- 介入注射另立課程、另做安全與能力邊界審查，不混入診斷課程

## 上線閘門

- `make check` 與 `make verify` 通過
- 無未標示的五年以上影片；經典內容均具例外理由
- 必要單元完成具資格醫師審閱
- 第三方內容只以允許的官方嵌入或外部連結呈現
- 正式網域、SEO canonical、OG 圖與 robots/sitemap 完成 production 驗證
