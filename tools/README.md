# tools/ — 策展與逐段筆記的工作腳本

這些是主編（策展人）在課程擴充時實際跑過的腳本，不參與 `make build`，
但下一輪加片或做逐段筆記時會直接用到。全部只依賴標準函式庫與外部 CLI（`yt-dlp`）。

| 腳本 | 用途 |
| --- | --- |
| `verify_videos.py` | 對 `syllabus.json` 裡已收錄的影片跑實查（yt-dlp + oEmbed），比對宣稱值與實際的頻道、片長、上架日、可嵌入、字幕軌 |
| `verify_candidates.py` | 對策展候選片跑同一套實查，並依硬性資格（可嵌入／公開／英文字幕／片長／cutoff）給 PASS／REVIEW／FAIL |
| `scan_intervention.py` | 用介入關鍵字掃字幕，找出需要 `diagnostic_segment_range` 框限的段落與群集 |
| `clean_vtt.py` | VTT → `[MM:SS] 文字`，去自動字幕的 rolling 重複、解 HTML 實體，**並依 `diagnostic_segment_range` 裁切**。逐段筆記派工前先跑這支，比事後刪段可靠 |
| `find_garbled.py` | 機械預篩字幕訛誤候選：字典比對＋詞形還原，把數十萬字縮到數百個候選詞 |
| `local_correct.py` | 把候選詞交本地 ollama（零 API 成本）判定是訛誤還是正常詞，輸出對照表 |

## 典型流程

```bash
# 1. 抓字幕
yt-dlp --skip-download --write-auto-subs --write-subs --sub-langs "en.*" \
       --sub-format vtt -o "%(id)s.%(ext)s" "<url>"

# 2. 清理並依框限裁切
python3 tools/clean_vtt.py <subs_dir> course/data/syllabus.json <out_dir>

# 3. 掃介入內容，定出框限
python3 tools/scan_intervention.py <subs_dir> <candidates.json>

# 4. 字幕訛誤對照（本地 LLM，零成本）
python3 tools/find_garbled.py <transcripts_dir> candidates.json
python3 tools/local_correct.py candidates.json verdicts.json
```

## 已知產出

`course/research/caption-corrections.json` — 261 條字幕訛誤對照表
（本地 `qwen3.8:27b-mlx` 判定 → 主編抽驗更正）。逐段筆記階段用來校正解剖名詞，
並把更正紀錄寫進各影片的 `note` 欄位，作為課程可信度的證據。

**主編抽驗抓到的錯**都記在該檔的 `reviewed_overrides`：本地 LLM 把 `pathak` 誤判為
"Parker"（實為 pathologic）、`intra` 是斷字產物不是訛誤。另有一則 ESSR 影片的
`rejection`／`injection` 實為肌腱 **insertion** 的誤辨，記在 `docs/VIDEO_CURATION.md`。
