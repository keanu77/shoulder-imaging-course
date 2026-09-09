# 證據邊界獨立審查：2026-09-09 advanced packages

審查範圍：cervical-imaging-course、lumbar-imaging-course、wrist-hand-imaging-course、shoulder-ultrasound-course 的 `course/research/2026-09-09-advanced/package.json`。完整讀取 12 單元、36 題（含全部選項解析）、24 案例（含 rubric 與 sample_report）。只審證據邊界，不代替解剖、格式、視圖或原始圖像驗收。未修改教材。

依據：已提供的 `research/selected.json` 原始 metadata／abstract，以及相關 `*-body.txt` 全文段落。額外以 PubMed 即時核對 glenoid-track 原研究；PMC 網頁兩次遇到驗證頁，未將網頁失敗當成全文已讀，全文仍以已取得的 XML 衍生文字為準。摘要核對來源不宣稱全文審讀。這是單一獨立證據鏡頭；審查者可能誤判，以下修訂應由主編核對。

**結論：沒有確認的 blocking；2 項 worth-fixing。** 整體稿件已主動區分影像、症狀、功能、診斷信心與準確度，也未把研究切點轉為通用門檻。36 題正答與解析未發現顛倒證據方向或新增無來源的量化效度宣稱。

## 發現

### E1 — worth-fixing — adv-shoulder-glenoid-track

位置：`evidence_boundary`。

原文：「此為選定族群，不是普遍診斷準確率，更不是術式決策工具。」

問題：最後一句的否定範圍偏大。原研究是在檢驗 glenoid track 作為 surgical decision-making aid 的可靠性／效度，結論是慎用；它沒有證明該模型完全不能成為決策的一項輔助。教材其他段落已正確寫成「不能單獨決定手術」，此處應一致。這不是需要增加術式教學，而是避免把「不能單獨決策」改成「完全沒有輔助價值」。

證據：[Rashid et al., PMID 38390400](https://pubmed.ncbi.nlm.nih.gov/38390400/) 的結論仍容許將模型用來輔助決策，但要求謹慎。現有全文 `research/shoulder-track-primary-body.txt:73` 提醒單一因素決策需謹慎；`:83` 質疑其輔助效用，沒有作全面否定。研究確為 49 人、3D CT 對動態關節鏡分類 accuracy 65%、interrater α 0.368；教材數值未誤植。

建議：「此為選定族群的比較結果，不能視為普遍診斷準確率；模型可提供部分結構資訊，但不能單獨決定術式。」若要更完整說明效度，可另註原研究動態關節鏡也不是完美參考標準（麻醉下肌肉動態作用不同；全文 `:82`），屬可選的精度補充。

為何不是 blocking：整個單元、題目及案例反覆要求臨床整合，沒有導向錯誤術式或排除適當評估；問題是單句過度否定。

### E2 — worth-fixing — adv-cervical-ankylosed

位置：`required_views[1]`、`interpretation_steps[2]`，以及新發神經異常情境的 `q2`。

原文：「依外傷流程取得 CT 與多平面重組，核對是否需評估非連續損傷。」、「平片陰性仍不能完整排除損傷；依外傷影像流程以 CT 補足骨性評估，神經或韌帶問題另考慮 MRI。」

問題：引用的 DGOU 建議比「是否需」和「另考慮」更明確。對僵直脊椎相關外傷，文獻建議進行全脊椎骨折篩查以排除非連續損傷；已有神經功能受損時，MRI 在該建議中屬必要評估。現稿將「已有神經異常」與「一般韌帶疑問」合成同一可選措辭，可能淡化來源所強調的情境差異。

證據：[DGOU recommendations, PMID 30210963](https://pubmed.ncbi.nlm.nih.gov/30210963/)；已取得全文 `research/cervical-ankylosed-body.txt:32`：多節段損傷須列入並排除，相關外傷建議 whole-spine CT 或 MRI 篩查，神經受損時強調 MRI 必要性。其摘要亦明述有神經受損或仍有疑慮時應補 MRI。這是文獻／病例系列形成的建議，不能冒稱高確定度試驗，但也不宜將建議強度完全抹平。

建議：明確區分「依僵直脊椎外傷流程檢查全脊椎是否已完整篩查，以排除非連續損傷」及「已有新發神經異常時，應及時完成 MRI 等神經結構評估；一般疑慮則依情境補充」。可在 q2 的正答解析補一個短句，保留臨床團隊及外傷流程的執行角色。

為何不是 blocking：現稿沒有寫成不做 MRI 或只做局部 CT 即排除，且已有「核對 MRI」、「及時傳達」、保留非連續損傷等內容；屬情境與建議強度的精修。主編若認為「依外傷流程」已足夠承載此要求，可保留原稿並記錄理由。

## 12 單元覆蓋表

| Unit ID | 本次核對的核心證據／邊界 | 題目與案例 | 結果 |
| --- | --- | --- | --- |
| adv-cervical-postop | ACR 是適切性指引；spine-postop-review 為圖像敘述回顧。CT 骨與植入物、MRI 神經與軟組織分工有來源支持；未將器材完整等同融合，保留偽影盲區與症狀因果。 | q1–q3、case1–case2 全讀；正答與解析未超出模態限制。 | 無發現 |
| adv-cervical-discordance | 2024 DCM 評論與 2017 臨床指引支持影像症狀不一致。全文 T2 高訊號並非所有臨床脊髓病變者都有，且無症狀者也可有；「無高訊號不排除」成立。 | q1–q3、case1–case2 全讀；未由 MRI 決定臨床嚴重度或個人進展。 | 無發現 |
| adv-cervical-ankylosed | DGOU 為文獻／病例與專家建議；陰性平片不足以排除、低能量不能安心等主張成立。MRI／全脊椎篩查建議強度可更精確。 | q1–q3、case1–case2 全讀；急性誘發屈伸被正確否定。 | E2 worth-fixing |
| adv-lumbar-postop | Passavanti 摘要明示 124 份 MRI、兩位讀者、時程分組；終點是信心與一致性，非手術金標準準確度。18 個月未被誤用為硬切點。 | q1–q3、case1–case2 全讀；信心／準確度、結構／症狀因果區分正確。 | 無發現 |
| adv-lumbar-infection | Patel 73 人回溯 Modic-like 選樣及三組定義正確；claw 機率不是全部背痛／術後感染的普遍試驗。ACR 感染摘要支持 MRI 與臨床／微生物整合。 | q1–q3、case1–case2 全讀；無法判讀未當成 claw 陰性，沒有由 MRI 指定病原。 | 無發現 |
| adv-lumbar-sij-specificity | de Winter 172 人比較含健康者、跑者、產後；未把其比例外推成人口盛行率。2022 全文支持分類／診斷區別及 2016 移除強制二切片條件。Figure 6 原文的騎乘負荷與薦骨疲勞骨折相符。 | q1–q3、case1–case2 全讀；沒有把產後等替代原因改成排除 axSpA 的保證。 | 無發現 |
| adv-wrist-dynamic-sl | 2021 Delphi 與 46 人關節鏡選定、特定 3T DESS MRI 研究分開，沒有一般化 NPV 或準確率。靜態正常不能完整排除動態不穩定有共識支持。 | q1–q3、case1–case2 全讀；投照、負荷及技術可比性解析成立。 | 無發現 |
| adv-wrist-druj-tfcc | 19 位手外科／27 位放射科 Delphi 人數正確；中立／旋前／旋後 CT、中央與周邊 TFCC 差異、窩部 MRA／CTA 用途由摘要支持。 | q1–q3、case1–case2 全讀；沒有把中立位 CT 正常等同 TFCC 完整或直接確診。 | 無發現 |
| adv-wrist-scaphoid | 2025 癒合回顧與 2025 血流 meta-analysis 的終點分開；後者是不癒合族群，顯影敏感度並非 100%，且有異質性。全文 CT 橋接與 MRI 血流分工支持案例。 | q1–q3、case1–case2 全讀；未使用等訊號或顯影來保證癒合／活動許可。 | 無發現 |
| adv-shoulder-cuff-postop | meta-analysis 是 8 研究、US 2 研究，無顯著差異；並非等效設計。修補後異常外觀可超過 6 個月，不能只憑訊號判再撕裂。 | q1–q3、case1–case2 全讀；陰性、不可評估、結構及功能區分合理。 | 無發現 |
| adv-shoulder-glenoid-track | 49 人與 65% accuracy 核對正確；可靠度與對 engagement 的效度分開；0.83D−d 計算及 0.1 mm 邊界例正確。單句對工具的否定範圍過大。 | q1–q3、case1–case2 全讀；問題解析本身沒有錯誤，病例沒有推導術式。 | E1 worth-fixing |
| adv-shoulder-neuropathy | 兩篇回顧支持結構／定位與神經功能整合，不是驗證過的影像單獨診斷規則；肌肉分布只被當成假說，保留神經根／臂叢／肌腱等鑑別。 | q1–q3、case1–case2 全讀；囊腫沒有被當成壓迫或功能障礙保證，無囊腫也未排除神經病變。 | 無發現 |

## 不應為了迎合審查而修改的部分

- 題目錯誤選項刻意使用「一定」「百分之百」「所有」，並明確標 false、附駁斥解析；這些不是教材的肯定主張，不列為絕對化錯誤。
- 肩胛上神經舊回顧用了很強的肌肉水腫措辭；現稿將分布降為定位假說並保留鑑別，沒有理由為了逐字貼合回顧而升成 pathognomonic。
- 舟狀骨舊回顧對等訊號／存活的描述較強，新稿同時引用較新的統合分析保留假陰性與異質性，是合理邊界，不應恢復成單一訊號判決。
- 沒有原始影像視覺驗收的 source_figure，稿件已透明標示；本審查只核對其證據使用，不能藉本報告改為「視覺驗收完成」或臨床核准。

## Pass 2：限定修訂覆核（2026-09-09）

本次只核對 E1、E2 指定欄位；沒有重審其他內容，未修改教材。主編已另行核對來源全文。本輪參照首輪所記錄的原始來源段落，確認修訂沒有引入反向過度主張。

- **E1 已解決。** `adv-shoulder-glenoid-track.evidence_boundary` 現為「模型可提供部分結構資訊，但不能單獨決定術式，動態關節鏡參考標準也有其限制。」已保留輔助價值、拒絕單項決策，亦補上參考標準限制；與原研究的慎用結論一致。
- **E2 已解決。** `adv-cervical-ankylosed.required_views` 現要求確認全脊椎完整篩查，並區分新發神經異常應及時完成 MRI 與其他疑慮依情境補充。`interpretation_steps` 同步要求全脊椎篩查並明確歸屬 DGOU 神經功能異常 MRI 建議；q2 正答解析已加入「已有神經異常時，DGOU 建議及時補 MRI 評估」。三處一致，未將骨折 CT 當成神經評估完成。

限定 Pass 2 結論：兩項 worth-fixing 均已處理；在本次限定覆核範圍沒有剩餘 blocking 或 worth-fixing。此結論不是臨床簽核、原始影像視覺驗收或發布許可。

本次實際讀取之四包 SHA-256（完整檔案 bytes）：

| Package | SHA-256 |
| --- | --- |
| cervical-imaging-course/course/research/2026-09-09-advanced/package.json | `323998137fb974d0d3dfdd539f8632019f5925f195f3aafd723bae4f61923b79` |
| lumbar-imaging-course/course/research/2026-09-09-advanced/package.json | `86cc82e23d5d1b5e87ad1766d6ee5fd4e5202ff3120ed82ad22d0dfd33c3586f` |
| wrist-hand-imaging-course/course/research/2026-09-09-advanced/package.json | `ae4afd1855779ad14358e3ab7278bb70827f7c9582fec54a051268be604d0343` |
| shoulder-ultrasound-course/course/research/2026-09-09-advanced/package.json | `b6826006f1b15b0d49b51f8d6732397091827d363c2cb88e50ab8e0d36fec202` |
