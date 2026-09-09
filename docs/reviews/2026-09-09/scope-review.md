# 進階教材獨立審查：範圍一致性與教學可用度

審查日期：2026-09-09。僅採範圍鏡頭，未編輯任何教材。依 `/Users/ethanstudio/.codex/skills/med-course-site/references/clinical-review.md` 執行；本報告不替代解剖、證據邊界或臨床簽核。審查者可能誤判，以下修訂建議須由主編依實際用途覆核。

## 材料與驗證方法

完整閱讀四站 `course/research/2026-09-09-advanced/package.json` 的 12 單元、36 選擇題（108 選項及逐項解析）、24 案例（10 原文圖例、14 虛構文字情境），以及所引用來源的本機 `*-figures.json` 圖說。逐項對照同站 `course/data/syllabus.json` 前置 unit ID 與名稱。未開啟原始圖像，因此「圖說支持」不等於視覺驗收通過；套件已有正確揭露此限制。此為來源圖說與教材契約的核對，未額外提出新的臨床主張。

## 結果

- 明確 blocking：0。
- worth-fixing：4 項，列於下方；其中 1 項跨全部單元。
- 12 單元的前置 ID 都存在；肩袖單元有教學關聯可改善，但不存在壞連結。
- 14 個虛構案例均同時有 `kind: synthetic`、prompt「虛構」、verification「作者編寫的虛構文字情境；沒有真實病人影像」，且 source / figure / source_url 為 null，沒有誤標真實。
- 10 個原文圖例均有來源、figure ID、連結與尚未視覺驗收聲明；已用圖說核對全部 10 個 figure ID。
- 每題恰有 1 正解，每個選項均有 rationale。未發現必須同時接受兩答案的明確題目歧義；干擾選項多採「一定／所有／百分之百」等絕對說法，較適合作為概念自評，尚非具鑑別力的進階測驗。
- 未發現正文使用簡體中文、嵌入 HTML 或 Markdown 格式；英文縮寫、序列與公式屬專業標記。未發現介入操作、用藥劑量、針路或手術步驟教學。

## 待覆核發現

### S1 — 全部 12 單元：正解位置固定重複，降低自評價值（worth-fixing）

**證據／原文：** 每單元 q1 的 `correct: true` 在第 3 選項，q2 在第 2 選項，q3 在第 1 選項。36 題完整核對，全部為 3 → 2 → 1；例如 `adv-cervical-postop-q1` 正解「描述可見器材，註明融合與神經結構尚無法評估。」位於第 3 選項，q2 正解「指出受限位置及尚未解決的臨床問題。」位於第 2 選項，q3 正解「依適應情境使用 CT，另行評估神經與軟組織問題。」位於第 1 選項。

**影響：** 學員讀過少數單元後，可以不理解題幹而利用規律作答，進階能力自評容易高估表現。

**建議：** 在資料層打散位置，或於實際練習呈現時將 text、rationale、correct 綁成同一選項一起洗牌。若現有顯示器已可靠洗牌，這個問題即不成立；應先確認再修。不要因此宣稱測驗有效度已被建立。

### S2 — `adv-shoulder-cuff-postop`：US 前置單元對應可更直接（worth-fixing）

**原文：** `prerequisite_units: ["ch11-u1", "ch11-u2", "ch4-u1"]`；required_views 為「US 長短軸核對肌腱連續性、附著處及可見範圍；動態依情境評估。」

**對照證據：** 同站 syllabus 的 `ch4-u1` 是「旋轉間隙與肱二頭肌近端」，`ch4-u2` 才是「棘上肌長短軸與附著面」，`ch6-u2` 是「部分與全層旋轉肌袖撕裂」。`ch11-u1`／`ch11-u2` 已提供 MRI 肌袖病變／肌肉品質背景。

**影響：** 雖無失效 ID，前置路徑未明確把讀者送到本單元主要 US 技術與肌腱連續性判讀基礎。

**建議：** 依修補範圍將 `ch4-u2` 或 `ch6-u2` 列為前置；若 `ch4-u1` 是刻意保留的旋轉間隙背景，可保留並增補，無須機械性替換。這是教學銜接問題，不是內容臨床錯誤。

### S3 — `adv-lumbar-infection-case1`：Figure 13 應分開面板涵蓋節段（worth-fixing）

**原文：** 「開啟 Figure 13。依序列出 L3–4 終板、椎間盤與椎旁變化；不要從圖像指定菌種。」rubric：「定位 L3–4；不將術後器材本身當成感染證明。」

**圖說證據：** `spine-postop-review-figures.json` 的 `fig13` 明確指出 a–c 是矢狀面、L3–L4 終板訊號及顯影；但 d–f 是 “Axial view at the intervertebral level of L3-L5”，並提到椎旁組織顯影。圖說涵蓋的軸向範圍比單一 L3–4 更廣。

**影響：** prompt 要求使用整張圖，卻將回答範圍全部收斂到 L3–4，可能使學員把 d–f 所見誤歸同一節段，或因正確保留節段不確定而被 rubric 扣分。

**建議：** 寫清 a–c 的 L3–4 所見；d–f 依原圖標示分別記錄可核對層面，無法確定層面就說明不明。原文圖說可能有用語粗略問題，請視覺驗收後決定更精確措辭，不能僅憑本報告替原圖補節段。

**嚴重度說明：** 本文整體仍將其作感染範例，並未宣稱所有 d–f 都是 L3–4；故不列 blocking。

### S4 — `adv-wrist-dynamic-sl-case1`：明示 a/c 才是負荷比較，b 是另項排列資訊（worth-fixing）

**原文：** 「開啟 Figure 1 的 a、b、c，比較左腕無負荷與握球壓力視圖；哪些差異屬於負荷資訊？」

**圖說證據：** `wrist-sl-figures.json` 的 `Fig1`：a 是 dorsopalmar radiograph 的舟月距離，b 是 lateral radiograph 的舟月角 73°，c 是 dorsopalmar clenched ball stress view。

**影響：** 新讀者可能把 a/b/c 當成三個可直接比較負荷的投照；b 的側位角度與 a/c 的正位間隙屬不同量測。現有 rubric 已指出角度不是通用切點，但尚未把應比較的面板明確配對。

**建議：** 改成「以 a 與 c 比較正位無負荷／握球壓力下的舟月間隙；再用 b 描述側位排列」，保留不能跨投照直接解釋間隙變化的既有教學。

**嚴重度說明：** 原句不必然要求拿 b 與 c 做同量測比較；屬降低歧義，不是已確認臨床錯誤。

## 12 單元覆蓋表

「題目 3/3」指三題均已人工閱讀，單一正解且逐項解析齊備；全部另受 S1 影響。所有案例均維持 diagnostic-only。

| Unit ID | 前置 ID 已核對 | required_views 核對／資料不足處理 | 原圖與虛構案例覆蓋 | 題目／局部結論 |
|---|---|---|---|---|
| adv-cervical-postop | mr1-u2、mr4-u2，存在且相關 | 正側位固定涵蓋、CT 多平面、MRI T1/T2；屬完整評估清單，案例未假稱全數提供 | fig4：a/b 矢狀冠狀 C6–T1；c 固定上方軸向；d T1 軸向。prompt 無額外手術推論。synthetic 偽影與缺時程標示正確 | 3/3；無局部 blocking |
| adv-cervical-discordance | mr3-u2、mr4-u1，存在且相關 | 矢狀與對應軸向 T2、臨床資料；缺漏明確標記 | fig2 A/B symptomatic DCM、C/D 無體徵症狀，圖說支持。synthetic 清楚分開 | 3/3；無局部問題 |
| adv-cervical-ankylosed | xr2-u1、mr1-u2，存在且相關 | 平片涵蓋、CT 多平面、依情境 MRI；沒有把動態誘發當 required view | fig2 明限 A 初始側位/B 術前 CT，排除 C/D 搬動及復位學習。synthetic 明確 | 3/3；來源其他面板含手術不等於教材越界 |
| adv-lumbar-postop | mr2-u1、mr3-u2，存在且相關 | 多平面 T1/T2，顯影依問題；病例明說單張無法完成要求 | fig8 圖說為腰椎術後 pseudomeningocele 與偽影，教材稱「液體集合」範圍較保守但無失真，沒有把它當 scar/disc 驗證題。synthetic 明確 | 3/3；無局部 blocking |
| adv-lumbar-infection | mr4-u1、mr2-u2，存在且相關 | T1/T2、水敏感、軸向、適當 DWI，品質不佳不判徵象 | fig13 的 L3–4 與 L3–5 面板需分開（S3）；synthetic 缺軸向/DWI 等明確 | 3/3；S3 worth-fixing |
| adv-lumbar-sij-specificity | mr6-u1、mr6-u2、mr6-u3，存在且相關 | 斜冠狀 T1/水敏感及正交平面；病灶與背景分列 | Fig6 左側薦骨為主、extensive horse riding、fatigue fracture，圖說支持；synthetic 明確 | 3/3；無局部問題 |
| adv-wrist-dynamic-sl | xr2-u2、us3-u2、mr2-u2，存在且相關 | 正位/真正側位、標準化負荷、MRI 技術；指向具體模態但未提供整套資料，限制已寫 | Fig1 左腕與 a/b/c 皆存在，應明確 a/c 負荷配對（S4）；synthetic 明確 | 3/3；S4 worth-fixing |
| adv-wrist-druj-tfcc | mr2-u1、mr2-u2，存在且相關 | 中立/旋前/旋後 CT 姿勢與 MRI 可見度；兩病例專練沒有完整資料時的限制 | 2 個 synthetic 均標示，無硬借無關病例圖；沒有關節造影穿刺操作 | 3/3；無局部問題 |
| adv-wrist-scaphoid | mr3-u1、xr2-u1，存在且相關 | 長軸 CT 與 MRI T1/水敏感/適當顯影，分開結構和血流 | F6 圖說確有顯影前後並描述 preserved vascularity；教材未要求其證明骨性癒合。synthetic 明確 | 3/3；無局部問題 |
| adv-shoulder-cuff-postop | ch11-u1、ch11-u2、ch4-u1 均存在；S2 教學銜接 | US 長短軸與 MRI 多平面；單長軸虛構題刻意不足，不應因未提供全套圖判 blocking | 2 個 synthetic 均標示；無虛構真實影像驗收 | 3/3；S2 worth-fixing |
| adv-shoulder-glenoid-track | ch12-u1、ch12-u2、ch9-u2，存在且相關 | 3D CT en face、肱骨頭、D/d/HSI 量測資訊；既有圖為方法示例 | fig1 3DCT a/b 圖說含 D/d、後側肱骨頭、HSI=缺損+骨橋；synthetic GT 21.9 mm 與 0.1 mm 差距計算正確。未要求術式 | 3/3；無局部問題 |
| adv-shoulder-neuropathy | ch10-u2、ch12-u2、ch7-u3，存在且相關 | T1/水敏感涵蓋兩肌與切跡區；圖例未假稱提供神經功能資料 | f004 右肩、左面板冠狀/右面板橫斷，圖說支持。synthetic 無囊腫並未宣稱排除神經病變 | 3/3；無局部問題 |

## 不應誤判為 blocking 的事項

1. **required_views 有臨床背景項目，且病例沒有全套影像。** 本套件已宣告沒有完整 DICOM、盲測或效度；多題刻意練習資料不足，原圖也明說僅是圖例。因此不是失敗的「完整病例」。未來若改為正式技能測驗，可把欄位拆成「建議完整資料／本題已提供／尚缺」，並對每個案例附 view checklist，但不能僅因名稱 required_views 就把目前草稿判定不可教學。
2. **資料庫文章包含治療內容。** 頸椎僵直原圖有 C–E 復位手術，肩胛上神經回顧有阻斷與 portal 圖；教材已限定診斷面板，沒有抽出操作細節。來源主題不等於本題範圍。
3. **術後、血流或模型題提及治療／運動許可。** 相關語句是在限制影像能支持的結論，不是提供處置步驟或許可。
4. **未完成視覺驗收。** 這是真實的尚未完成工作，套件也明確揭露；不能在此次只讀圖說的審查中誤稱已完成，亦不能僅靠這點反向主張圖中必有錯誤。

## 使用邊界

本報告支持「草稿範圍與文字教學一致性未見明確阻斷問題」，不構成臨床批准、原始圖像驗收、正式測驗效度驗證或生產發布批准。


## Pass 2 — 限定修訂驗收（2026-09-09）

本輪只核對 S1–S4 的修訂以及主編完成圖面核對後的 verification 文案；未重審其餘內容，也未修改教材。前文保留為 Pass 1 歷史紀錄；目前狀態以此節為準。

### 四項發現結案

- **S1：通過／已解決。** 已讀修訂腳本 `/private/tmp/imaging-siblings-qa/revise_advanced.py`，確認使用每題 ID 的 SHA-256 字串作為 `random.Random` seed，並對完整 option 物件洗牌。另以 Pass 1 已確認的初始答案位置 3 / 2 / 1 獨立重算每題置換，36 / 36 題均符合。資料不再跨 12 單元重複固定 3 → 2 → 1；每題仍恰一正解及逐項解析。個別單元偶然出現 2 / 2 / 2 或 3 / 3 / 3 是此次 deterministic shuffle 的結果，並不表示仍沿用原固定規律。
- **S2：通過／已解決。** `adv-shoulder-cuff-postop` 前置已改為 `ch11-u1`、`ch11-u2`、`ch4-u2`、`ch6-u2`，後兩者在同站 syllabus 存在，名稱分別為「棘上肌長短軸與附著面」、「部分與全層旋轉肌袖撕裂」。
- **S3：通過／已解決。** `adv-lumbar-infection-case1` prompt 已明分「a–c 矢狀面板的 L3–4 終板與椎間盤」及「d–f 軸向面板的周邊延伸」，並明示原圖說後者為 L3–5 範圍、不可將全部面板當作同節段。rubric 同步更新，沒有要求學員替各軸向面板猜特定節段。
- **S4：通過／已解決。** `adv-wrist-dynamic-sl-case1` 已明寫「比較左腕 a（無負荷正位）與 c（握球壓力正位）的間隙，再用 b（側位）評估排列」，清楚分開負荷比較與側位排列。

### 圖面驗收狀態核對

主編回報已實際檢視 10 張來源圖及圖說。本 reviewer 沒有重複執行獨立圖面檢視；本輪確認 10 / 10 source_figure 的 verification 均已改為「2026-09-09 已核對原文圖說、實際圖像與面板」，且同時保留「此為公開圖例，原頁可能顯示答案，並非完整 DICOM 或盲測病例」。四包 limitations 亦同步記載已完成實際圖像核對，仍保留沒有完整 DICOM、盲測病例或專家評分效度的限制。沒有把圖面核對寫成臨床批准或測驗效度驗證。

### 36 題置換核對

| Unit ID | q1 / q2 / q3 正解位置 | ID seed 置換重算 |
|---|---|---|
| adv-cervical-postop | 2 / 1 / 2 | 通過 |
| adv-cervical-discordance | 2 / 1 / 1 | 通過 |
| adv-cervical-ankylosed | 2 / 1 / 1 | 通過 |
| adv-lumbar-postop | 1 / 3 / 1 | 通過 |
| adv-lumbar-infection | 2 / 2 / 2 | 通過 |
| adv-lumbar-sij-specificity | 2 / 1 / 1 | 通過 |
| adv-wrist-dynamic-sl | 2 / 2 / 1 | 通過 |
| adv-wrist-druj-tfcc | 3 / 3 / 3 | 通過 |
| adv-wrist-scaphoid | 3 / 3 / 1 | 通過 |
| adv-shoulder-cuff-postop | 2 / 1 / 2 | 通過 |
| adv-shoulder-glenoid-track | 3 / 2 / 3 | 通過 |
| adv-shoulder-neuropathy | 1 / 2 / 1 | 通過 |

### Pass 2 四包 SHA-256

以下是本輪實際讀取的原始 `package.json` 位元組雜湊，對應各站 `course/research/2026-09-09-advanced/package.json`；雜湊涵蓋整包，但本輪審查範圍仍限於上述修訂。

| Repository | SHA-256 |
|---|---|
| cervical-imaging-course | `323998137fb974d0d3dfdd539f8632019f5925f195f3aafd723bae4f61923b79` |
| lumbar-imaging-course | `86cc82e23d5d1b5e87ad1766d6ee5fd4e5202ff3120ed82ad22d0dfd33c3586f` |
| wrist-hand-imaging-course | `ae4afd1855779ad14358e3ab7278bb70827f7c9582fec54a051268be604d0343` |
| shoulder-ultrasound-course | `b6826006f1b15b0d49b51f8d6732397091827d363c2cb88e50ab8e0d36fec202` |

限定 Pass 2 結論：四項 worth-fixing 已解決，無新增範圍 blocking。此結論不等於臨床簽核、正式測驗效度驗證或生產發布批准。
