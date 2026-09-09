# 獨立解剖鏡頭審查

審查日期：2026-09-09。範圍限定為解剖、側別、方向、命名、分型與公式；不評其他鏡頭。依 `med-course-site/references/clinical-review.md` 執行。未修改教材。

## 結論

12/12 單元已閱讀，包括目標、視圖、步驟、陷阱、題幹／選項／解析與病例 rubric／sample_report。未發現可確認的 blocking 解剖或公式錯誤。提出 2 項 worth-fixing 的解剖定義精確度建議；均不是已寫反的解剖關係，主編可視教學完整性決定採納。

本審查核對已提供的 `selected.json`、全部 `*-figures.json`、相關全文摘錄與來源摘要。未完成原始圖像視覺驗收，因此「側別／面板吻合」僅表示教材與原文圖說吻合，不等於獨立在原圖上辨識成功。審查不構成臨床簽核。

## 問題清單

### A1 — adv-shoulder-glenoid-track — worth-fixing

位置：`required_views[1]`、`interpretation_steps[1]`、`cases[0].rubric[1]`。

原文：「記錄最佳擬合圓、原盂寬 D、骨缺損寬 d、Hill–Sachs interval（HSI）的定義。」；「HSI 包含缺損寬度與骨橋的模型定義。」

問題：目前要求學員記錄 HSI 定義，但正文／評分規準並未明確給出骨橋的兩端點。若僅據教材文字量測，無法確認是從缺損外側緣量到旋轉肌袖附著區的內側緣；附著區內外側端點混用會改變 HSI。原文沒有把方向寫反，所以不是 blocking。

證據：`research/shoulder-track-primary-figures.json` Figure 1，a 是 Hill–Sachs 缺損內側緣，b 是外側緣，c 是後方旋轉肌袖附著處；HSI = a–b + b–c。`research/shoulder-track-primary-body.txt` Methods / 3DCT 明確將 c 定義為 rotator cuff footprint 的 medial margin，並採肱骨頭 posterior view。來源為 PMID 38390400 / PMC10883128。

建議：在步驟或 rubric 增補「肱骨頭後方視圖：HSI 為 Hill–Sachs 缺損寬度，加上缺損外側緣至後方旋轉肌袖附著區內側緣的骨橋距離」。D 可一併寫成最佳擬合圓重建的原始盂寬，d 是同方法下前方缺損寬。保留現有 GT 公式與近邊界措辭。

### A2 — adv-lumbar-sij-specificity — worth-fixing

位置：`interpretation_steps[0]`。

原文：「先確認病灶位於關節下骨、薦骨內或其他部位；描述側別及分布。」

問題：「關節下骨」不是此處最精確的解剖定位名稱，可能被讀為關節下方的骨，而不是關節面的軟骨下骨。其意圖可理解，且其他欄位已要求薦骨側／髂骨側與前後分布，因此不構成 blocking。

證據：`research/sij-interpret-body.txt` 定義段使用 subchondral bone；來源為 PMID 35199195 / PMC9283193。該文也分辨軟骨性關節部位的骨髓病灶與薦骨疲勞性骨折分布。

建議改為：「先確認病灶位於關節面軟骨下骨、薦骨內或其他部位；描述薦骨側／髂骨側、側別及分布。」單純提升定位精確度，不改變疾病結論。

## 12 單元覆蓋表

| 單元 ID | 已核對的解剖／方向／命名要點 | 結果 |
|---|---|---|
| adv-cervical-postop | Figure 4 a/b 矢狀與冠狀 C6–T1 固定；c 在固定節段上方，d 在 T1；教材未把 c 誤稱固定節段。脊髓／神經根／骨性融合分列。 | 未見問題 |
| adv-cervical-discordance | Figure 2 A/B 為有症狀 DCM、C/D 無 myelopathic signs/symptoms；矢狀與軸向壓迫描述無反向。 | 未見問題 |
| adv-cervical-ankylosed | Figure 2 C4–5；A 初始側位、B 術前 CT。C6 以下顯示不足與 C7–T1 交界限制一致；未引用錯誤 AO 分型。 | 未見問題 |
| adv-lumbar-postop | 硬膜外組織、神經根、椎間盤分列；Figure 8 為腰椎 pseudomeningocele 與金屬偽影，教材用較上位的「液體集合」未錯命名成瘢痕或復發椎間盤。 | 未見問題 |
| adv-lumbar-infection | Modic 第一型、DWI claw sign 的正常／異常骨髓交界定位正確；Figure 13 矢狀終板 L3–4，整組其他描述包含 L3–5。教材未將整組所有軸向面板強制命名成 L3–4。 | 未見問題 |
| adv-lumbar-sij-specificity | Figure 6 左薦骨／單側薦骨分布吻合；ASAS、axSpA 命名一致。 | A2 worth-fixing |
| adv-wrist-dynamic-sl | Figure 1 左腕；a 背掌投照、b 側位、c 握球壓力視圖；病例 73° 未誤當通用切點。舟月韌帶與舟月間隙／角度未混名。 | 未見問題 |
| adv-wrist-druj-tfcc | DRUJ 中立／旋前／旋後位置與共識摘要一致；TFCC 中央盤、周邊與窩部未錯置；沒有捏造 Palmer 分型。 | 未見問題 |
| adv-wrist-scaphoid | 近端／腰部／遠端與舟狀骨長軸重組無混淆；Figure 6 是近端骨片有顯影，不是 Figure 7 的無顯影 AVN 圖。 | 未見問題 |
| adv-shoulder-cuff-postop | 肌腱、附著處、肌肉分開；US 長短軸與 MRI 多平面描述沒有解剖方向錯置；兩例均為虛構，不冒稱特定原圖。 | 未見問題 |
| adv-shoulder-glenoid-track | GT = 0.83D − d；30 × 0.83 − 3 = 21.9 mm；HSI 22 mm 比 GT 大 0.1 mm 正確。Figure 1 盂面與肱骨頭的量測未混用。 | A1 worth-fixing |
| adv-shoulder-neuropathy | 兩肌受影響提示較近端、孤立棘下肌提示較遠端／棘盂切跡，與來源神經走向一致；Figure 4 病人右肩，左面板冠狀、右面板橫斷，均正確。 | 未見問題 |

## 不應誤修的地方

- `adv-shoulder-neuropathy` 的右肩與左側面板是不同概念，原文圖說明確就是右肩／左冠狀／右橫斷；不要把病例改為左肩。
- `adv-wrist-dynamic-sl` 的原圖已有輕微靜態間隙增加及 73° 側位角度。教材沒有稱此原圖為「靜態完全正常」，也未將之強分類成純動態型，所以不應強加修正。
- `shoulder-track-primary-body.txt` 前言對 true glenoid width 的文字可能造成 0.83(D−d) 的閱讀歧義；該文 Methods 與 Figure 1 明確為 0.83D−d，現教材公式正確，不能迎合前言字面而改錯。
- `adv-lumbar-postop` 用「液體集合」描述 Figure 8 是刻意較廣泛的結構描述，圖說更具體為 pseudomeningocele；目前未錯稱膿瘍／血腫，不列為臨床錯誤。
- `adv-lumbar-infection` Figure 13 的來源圖說本身包含 L3–4 終板與 L3–5 的其他描述；在未視覺驗收前，不應自行把教材 L3–4 一律改成 L3–5。

## 核對來源與完整性

已確認 `selected.json` 中引用來源的 PMID／PMCID 與四份 package 的來源及病例圖連結一致。詳細圖說檔包括 cervical-ankylosed、cervical-dcm、spine-postop-review、sij-interpret、wrist-sl、wrist-vascular-review、shoulder-track-primary、shoulder-nerve-review；另讀其餘提供圖說以防同號圖張冠李戴。對 DRUJ/TFCC、特殊腕 MRI、術後肌袖使用已提供原始書目摘要核對術語。全文針對神經走向、HSI 端點／分類方向、舟狀骨骨片、軟骨下位置與 DCM 面板對應複核。

以下為審查時 package SHA-256，供主編核對後續修訂是否使此審查過期：

- `cervical-imaging-course`: `2fb717d731117b8eeb3e48c294ecd3e6e9c0a519963e8bc4dc4e7403b1f57c58`
- `lumbar-imaging-course`: `bfdb3eac5a570e6906217364eb70454c4dc497f2bbc5f19d477566afa6d36239`
- `wrist-hand-imaging-course`: `9f4e16c5d0bc7e855cac193bdd25042caf43fac338f83159dfea577956ea9a05`
- `shoulder-ultrasound-course`: `bff49b8b574dabcc53977f180e610a7179a5700e0df11dc879a1642e6de117f8`


## Pass 2 — 修訂後定向複核（2026-09-09）

依主編要求，本次僅複核 A1、A2 及 lumbar infection 的 Figure 13 分面板文字；未重新審查全部 12 單元或重作所有原圖視覺驗收。

| 項目 | 修訂後核對 | 結論 |
|---|---|---|
| A1 / adv-shoulder-glenoid-track | 步驟及 rubric 已明確定義骨橋為缺損外側緣至後方旋轉肌袖附著區內側緣；步驟註明肱骨頭後方視圖。與 shoulder-track-primary Methods 的 b–c 端點一致。GT 公式及 21.9 mm 算例保留正確。 | 已解決；未見新解剖問題 |
| A2 / adv-lumbar-sij-specificity | 已改為「關節面軟骨下骨」，並明列薦骨側／髂骨側、側別及分布；與來源 subchondral bone 定位一致。 | 已解決；未見新解剖問題 |
| adv-lumbar-infection / case1 | a–c 明列矢狀面板 L3–4 終板／椎間盤，d–f 明列軸向、依原圖說 L3–5 範圍且不推定每張同節段。與提供 Figure 13 圖說一致，沒有將終板節段與全組範圍混為一談。 | 通過；未見新解剖問題 |

本次複核範圍內：blocking 0，未解決 worth-fixing 0。主編已回報完成 10 張實際圖像及 caption 核對；本審查者未獨立重作該視覺檢查。Pass 1 的「原圖尚未視覺驗收」為當時狀態，不能用來否定主編後續完成的工作；亦不應將主編的視覺檢查記成此審查者親自執行。

Pass 2 最新 package SHA-256（四包均已讀取計算，定向內容複核範圍如上）：

- `cervical-imaging-course`: `323998137fb974d0d3dfdd539f8632019f5925f195f3aafd723bae4f61923b79`
- `lumbar-imaging-course`: `86cc82e23d5d1b5e87ad1766d6ee5fd4e5202ff3120ed82ad22d0dfd33c3586f`
- `wrist-hand-imaging-course`: `ae4afd1855779ad14358e3ab7278bb70827f7c9582fec54a051268be604d0343`
- `shoulder-ultrasound-course`: `b6826006f1b15b0d49b51f8d6732397091827d363c2cb88e50ab8e0d36fec202`
