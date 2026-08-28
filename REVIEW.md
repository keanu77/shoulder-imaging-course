> **歷史文件。** 本報告寫於 2026-08-02，對象是當時的 8 章 24 單元／18 支影片版本，
> 章節代碼仍為 `CH0`–`CH7`。課程已於 2026-08-28 擴為三模態 9 章 34 單元 31 支影片，
> 章節代碼改為 `XR*`／`US*`／`MR*`。最新結構見 `docs/CURRICULUM.md`，
> 策展與框限決策見 `docs/VIDEO_CURATION.md`。
> **治理語意已更正**：本文提到的「醫師簽核」是當時的模型；現行 `approved` 代表
> **策展審閱**，不代表對第三方影片臨床內容的醫療背書。見 `README.md`。

# 肩部超音波診斷課程 — 優化與第一輪獨立審核

- 審核對象：本 repo（8 章 24 單元、18 支影片）
- 分支：`feat/shoulder-intervention-safety`
- 日期：2026-08-02
- 審核者身分：獨立審核（非醫療簽核）。醫師簽核僅使用者本人可執行。

## 一句話結論

**修正後可部署** —— 技術面已修正並全數綠燈，可在維持 `noindex` 醫療審閱狀態下部署為預備站；**正式解除索引與內容核准仍待醫師逐單元簽核**。本輪未發現醫療法 §85 療效／絕對化違規，也未發現診斷／介入範圍紅線被突破。

---

## 技術優化：做了什麼

全程 `uv sync --locked` 後 `make build`、`make check`（lint + 安全性測試 + 離線稽核 + 醫療閘門）、`make verify`（18/18 影片連結、11/11 PubMed／來源）皆綠；`ruff check .` 全數通過；`tests/test_segment_ranges.py` 20/20 通過。

1. **觸控目標（320／390px，補在既有窄螢幕 media query，桌面密度不動）**
   - `clinical.css` 窄螢幕：`.TabNav__item` 補 `min-width: 44px`（原本標籤隱藏後寬度掉到 ~38px）。高度該區塊已是 56px。
   - `player.css` 窄螢幕：`.Player__actions .btn` 補 `min-height: 44px`、`.Player__actions .btn-icon` 補 `width/height: 44px`、`.SearchBox--inline input`（播放清單搜尋）補 `min-height: 44px`。
   - `landing.css` 窄螢幕：`.Landing .btn` 補 `min-height: 44px`（首頁 CTA 與立場入口鈕，原本 ~32px）。
   - 既有已達標者未更動：Hero CTA（44）、`FilterBar__btn`／`FilterBar__core`（44）、`AppHeader .btn-icon`（44）、header 搜尋輸入（44）、`Unit__check`（44）、`NavList__item`（48）、`PlaylistItem`（>44）。

2. **死碼清理（刪除前已 `rg` 全專案確認僅存在於 CSS、無 JS/HTML/動態類名引用）**
   - `tokens.css`：移除未使用的 `.Box`／`.Box__header`／`.Box__body`、`.Flash`／`.Flash--warn`／`.Flash__icon`（框架殘留、本站未用）。
   - `evidence.css`：移除 `.Drill__marker--release/stretch/train`（render 走 inline style，未用這些修飾類；且命名沿用舊健身主題）。
   - `player.css`：移除 `.PlaylistItem__dot--lesson/release/stretch/train`（同上，走 inline style）與未使用的 `.Player__crumb`。
   - `stance.css`：移除已被 `.StancePage`／`.StanceCard` 取代的舊 `.Stance`／`.Stance__head/__title/__lede/__grid` 區塊與其 media query。
   - `layout.css`：移除未使用的 `.Stat__value .rating`。
   - `js/discuss.js`：移除未被引用的 `export const enabled`。
   - `evidence.css`：更新一則指向已刪除 `.Stance__grid` 的過時註解為 `.StancePage__grid`。
   - 未刪除具動態命名契約的類別（`Label--<tone>`、`MuscleBlock--<mod>` 等）以免破壞框架。

3. **安全掃描**：未發現 secret／API key／token／個人路徑（`/Users/...`）／內網主機名／tailnet 網址。`.env.example` 僅留空白佔位；`functions/api/hits.js`、`functions/schema.sql` 無真實憑證。

4. **內容指紋一致性**：HTML、CSS/JS module graph 與 `course.json` 共用單一指紋（本輪 `bb29d88251b8`）；dist 內所有 `css/*`、`js/*` 連結與 `app.js` 的 `fetch("course.json?v=…")` 均帶同一版本。

5. **無回歸**：所有既有稽核、安全性測試與 gate 條件維持不變（未刪測試、未放寬 audit、未改 gate）。24 單元維持 `medical-review`，`allowIndexing` 維持 `false`。

---

## 🔴 必須由醫師處理的項目（審核者僅記錄，未修改內容）

> 以下並非發現的內容錯誤，而是**只有具資格醫師才能清除**的關卡；審核者不具臨床簽核權。

1. **24 個單元的逐單元醫療簽核**。目前全部 `medical-review`。`audit_medical.py` 明訂：只要有任一單元非 `approved`，將 `allowIndexing` 改為 `true` 會使稽核失敗。解除 `noindex` 前必須完成人工簽核。
2. **臨床主張、診斷準則、掃描步驟的實質正確性最終認定**。本輪逐單元檢查了側別、縮寫與範圍一致性（見下），**未發現錯誤且未改寫任何實質內容**，但診斷準則的臨床正確性須由醫師背書。
3. **介入時間戳的字幕層級覆核**。見任務二第 6 點：本環境無法重讀 YouTube 字幕，僅完成結構與邏輯一致性抽驗；字幕層級的實查仍需醫師／curator 確認。

### 已檢查且未發現問題的項目（供醫師覆核）

- **醫療法 §85（療效保證／絕對化）**：全站無「保證／百分百／100%／根治／痊癒／一定／絕對／療效」等宣稱。命中的「最佳化」「完全斷裂／完全省略／完全相同」「永久保存」「品質保證」均為技術描述（optimization／full-thickness tear／records retention／QA），非療效或檢查準確度的絕對宣稱。全站對超音波準確度採描述性、保守語氣（例：「不得由退化性骨贅直接歸因疼痛」「不以單一所見取代多平面確認」）。
- **側別與縮寫（逐條）**：
  - 棘上肌 supraspinatus（CH4-u2，大結節足跡）／棘下肌 infraspinatus（CH5-u1，後側）／肩胛下肌 subscapularis（CH3-u2，小結節）— 附著與側別對應正確。
  - 大結節 greater tuberosity ↔ 小結節 lesser tuberosity — 對應正確（subscapularis→小結節、supraspinatus→大結節）。
  - 前側（CH3）↔ 後側（CH5）、外展（CH5-u2 動態夾擠）、內外旋（CH3-u3 肱二頭肌穩定；CH3-u2 動態外旋）— 使用正確。
  - **值得肯定**：CH3-u2 明確澄清「動作名稱是肩關節外旋；前臂旋後只用於起始擺位」，主動修正常見錯誤。
  - LHBT 結節間溝：CH1-u2／CH3-u1 以結節間溝兩側骨性地標定位，正確。
  - AC joint（CH2-u1／CH4-u3／CH6-u3）與 SC joint：兩者未混用；SC joint 未涵蓋（見 🟡-5）。
  - 盂唇 labrum：CH0-u2、CH5-u1 以「後側盂肱關節與關節唇區域」呈現，並註明「超音波對關節唇評估的限制」「過度解讀關節唇的有限可見範圍」，無過度宣稱；未細分前上／後上（符合超音波實際可視限制）。
  - 肩峰下／三角肌下滑囊層次：CH4-u3／CH6-u2 描述「三角肌、滑囊、旋轉肌袖及骨皮質層次」，層次關係正確。
- **免責聲明**：`footer.disclaimer` 明載——醫師為主要學員、僅供教育用途、不取代 hands-on training／合格督導／機構 credentialing／完整病史理學檢查／正式影像判讀、第一階段不提供注射穿刺介入指引；`llms.disclaimer` 亦聲明僅供醫師專業教育、第一階段不涵蓋導引介入。**符合要求。**
- **診斷／介入範圍紅線（本課最重要）**：24 單元的學習目標、操作要點、評量題目**均未教授介入操作**。所有介入提及皆為排除性（CH0-u1「不包含任何注射、穿刺或其他介入操作」；CH0-u3「介入用無菌屏障只需辨認，仍不在本階段實作範圍」）；含介入影片一律以 `diagnostic_segment_range` 切出診斷段落並於 scope_note 明列排除。`audit_medical.py` 強制 `scope=diagnostic-only`、禁止 intervention 類型單元、標題介入關鍵字偵測。**範圍紅線完整維持。**
- **介入標註抽驗（3 支，結構／邏輯一致性）**：
  - CH1-u3《肩部肌肉骨骼超音波入門總覽》：`contains_intervention=true`、起點 02:12、診斷段 02:30–11:17…39:29–45:10（duration 52:34）。段落均在起點之後、未涵蓋 02:12，遞增不重疊。
  - CH2-u1《Buford 13-point》：起點 07:32、首段 01:45–07:31 於起點前結束、07:48 續接。一致。
  - CH4-u2《Martinoli 旋轉肌袖解剖》：起點 16:07（屍體染料注入）、診斷段 00:00–16:06、16:18–42:30，精準切出 16:07–16:17。一致。
  - 三支皆通過 `audit_medical` 的「診斷段不得涵蓋介入起點／遞增不重疊／起點早於片尾」規則。**字幕層級準確性見 🔴-3。**

---

## 🟡 建議但非阻斷的項目

1. **robots.txt 與 sitemap 與檢查表字面不符（但索引仍被阻擋）**。任務三要求 `robots.txt` 為 `Disallow: /`、`sitemap.xml` 為空；實際上 `seo.py` 產生的 `robots.txt` 為 `Allow: /`（並主動放行 GPTBot/ClaudeBot 等），`sitemap.xml` 含首頁 1 筆。
   - 現況**仍不會被索引**：`meta robots=noindex, follow` + `_headers` `X-Robots-Tag: noindex, follow` + `allowIndexing=false` 同時生效。
   - 技術上這是**刻意設計**（`seo.py` 註解：「AI 檢索器一律放行」）：`Disallow: /` 會使爬蟲讀不到頁面因而讀不到 `noindex`，反而可能留下 URL-only 索引；目前「允許抓取 + noindex」是較可靠的排除索引方式。
   - **建議**：與其他 5 站的實際 robots／sitemap 產出對齊；若跨站標準要求 `Disallow: /` 且空 sitemap，需在 `seo.py` 依 `allowIndexing` 切換（此為部署姿態決策，審核者未逕自修改）。**標記待確認。**
2. **殘餘 sub-44px 觸控目標（側欄密集 chip 與次要工具鈕）**：`.MuscleChip`／`.Label--muscle`（肌群 facet 標籤雲，~26px）、`.MusclePanel__clear`（~30px）、`.ProgressPanel__reset`（~26px）、`.SearchBox__clear`（~22px，位於 44px 高搜尋列內置中）。這些位於窄螢幕會轉為橫向捲動的側欄，強制 44px 會破壞密集 facet 版面，故未更動、僅記錄，供與其他 5 站標準對齊後決定。（`.LessonBox__lang` 語言切換鈕本站 0 支多語言版本，實際不會渲染，暫不處理。）
3. **早於五年的參考文獻缺機器記錄的保留理由**：`essr-shoulder`(2010)、`martinoli2010`(2010)、`jacobson2011`(2011)、`dynamic2018`(2018)、`aium-documentation2020`(2020) 早於五年門檻。11 筆參考**全部標註年份**，但 `reference_catalog` 無 `classic_exception_reason` 之類欄位，亦無近期替代來源搜尋紀錄（影片才有）。這些多為奠基性指引／技術標準（ESSR 肩部技術指引、Martinoli 技術指引、Jacobson How-I-Do-It），保留具正當性，惟建議補記保留理由。
4. **7 支經典例外影片的近期替代搜尋紀錄不齊**：7 支皆有 `classic_exception_reason`，但僅部分明確載明「近五年替代搜尋」（如 Martinoli 旋轉間隙「現有近五年公開影片未提供同等…」、Sonosite P1「近期短片少有同等長度…」）；Jacobson、Martinoli 解剖、Sonosite P2、AIUM、Buford 的理由偏「經典價值」而未載搜尋過程。`course/research/source-candidates.csv` 為策展紀錄，建議補齊搜尋字串。
5. **SC joint 未涵蓋**：僅涵蓋 AC joint。屬範圍選擇（肩部 MSK 超音波常聚焦 AC，SC 為另一主題），非錯誤；供醫師確認是否符合課程預期範圍。

---

## 部署就緒檢查表

| 項目 | 狀態 | 說明 |
|---|---|---|
| `python3 src/build/build.py` 無 uv 可獨立跑完 | ✅ | `pyproject.toml` `dependencies=[]`、`requires-python>=3.11`；build.py/seo.py 僅用標準庫；未設定 taxonomy plugin（`importlib` 不載外部碼）。`DEPLOYMENT.md` 記載 Pages build command 即 `python3 src/build/build.py && …`。（本機直接以 `/usr/bin/python3` 執行受 harness 權限提示阻擋，非程式問題；`make build` 已成功執行同一程式碼。）|
| `dist/` 含必要檔 | ✅ | index.html、course.json、css/、js/、og.png、robots.txt、sitemap.xml、llms.txt、_headers 全在。 |
| `_headers` 含 `X-Robots-Tag: noindex` | ✅ | `X-Robots-Tag: noindex, follow`；HTML 亦有 `meta robots=noindex, follow`。 |
| `robots.txt` 為 `Disallow: /` | ❌ | 實際為 `Allow: /`（並放行 AI 爬蟲）。索引仍被 `noindex` 阻擋，屬框架刻意設計。詳見 🟡-1。 |
| `sitemap.xml` 為空清單 | ❌ | 含首頁 1 筆（`/`，附 og.png image）。詳見 🟡-1。 |
| `course.config.json` `site.url` 正確 | ✅ | `https://shoulder-ultrasound.sportsmedicine.tw`。 |
| `allowIndexing` 維持 false | ✅ | `medical.allowIndexing=false`；`scope=diagnostic-only`、`primaryAudience=physicians`、`interventionalContentDeferred=true`。 |
| CI（`.github/workflows/quality.yml`）綠 | ✅ | 分支 `feat/shoulder-intervention-safety` 上 `check` 與 Cloudflare Pages 均 pass；CI 流程為 `uv sync --locked` + `make check`，本機已通過。新 commit 會重跑。 |
| og.png = 1200×630 | ✅ | 實測 1200×630。 |
| `make verify` 連結／引用 | ✅ | 18/18 影片連結、11/11 來源（含 PMID/URL）皆 200/206。 |
| **D1 綁定（本站特有）** | ✅（缺綁定不影響主體） | `functions/api/hits.js` 需 Cloudflare D1 綁定 `HITS`。缺綁定時回 `503 {error:"no-d1"}`；前端 `renderHits` 以 try/catch 靜默、`#hitCounter` 徽章維持 `hidden`，**頁面主體完全正常**。部署時若要啟用計數器：於 Pages 專案綁定 D1（binding 名 `HITS`），並以 `functions/schema.sql` 建表（`make counter` 或 `wrangler d1 execute <DB> --file functions/schema.sql --remote`）。`_headers` 已對 `/api/*` 設 `no-store`。 |

---

## 未做的事（依規範）

未 merge、未改 approved 狀態、未開啟 indexing、未動 Cloudflare Pages／DNS／自訂網域、未改寫任何臨床主張／診斷準則／掃描步驟、未刪測試／未放寬 audit／未改 gate。技術修正僅限前端 CSS/JS 的觸控目標、死碼與過時註解。
