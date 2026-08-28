"""實查策展候選片：存在性、頻道歸屬、片長、上架日、可嵌入、英文字幕。"""

import json
import subprocess
import sys
from pathlib import Path

CAND = Path(sys.argv[1])
OUT = Path(sys.argv[2])
CUT = "2021-08-28"


def ytdlp(url):
    p = subprocess.run(
        ["yt-dlp", "-j", "--no-warnings", url], capture_output=True, text=True, timeout=180
    )
    if p.returncode != 0:
        err = (p.stderr.strip().splitlines() or ["rc"])[-1]
        return {"_error": err}
    return json.loads(p.stdout)


def hhmmss(s):
    if s is None:
        return None
    s = int(s)
    h, r = divmod(s, 3600)
    m, sec = divmod(r, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


cands = json.loads(CAND.read_text())
res = []
for i, c in enumerate(cands, 1):
    url = c.get("url", "")
    print(f"[{i}/{len(cands)}] {c.get('slot')} {url}", file=sys.stderr, flush=True)
    j = ytdlp(url)
    subs, autos = j.get("subtitles") or {}, j.get("automatic_captions") or {}
    en_m = any(k == "en" or k.startswith("en-") for k in subs)
    en_a = any(k == "en" or k.startswith("en-") for k in autos)
    ud = j.get("upload_date") or ""
    ud = f"{ud[:4]}-{ud[4:6]}-{ud[6:]}" if len(ud) == 8 else None
    verdict, reasons = "PASS", []
    if j.get("_error"):
        verdict, reasons = "FAIL", [f"影片不存在或無法取得：{j['_error'][:80]}"]
    else:
        if j.get("playable_in_embed") is False:
            verdict = "FAIL"
            reasons.append("不可嵌入")
        if not (en_m or en_a):
            verdict = "FAIL"
            reasons.append("無英文字幕軌")
        if j.get("availability") not in (None, "public"):
            verdict = "FAIL"
            reasons.append(f"非公開：{j.get('availability')}")
        dur = j.get("duration") or 0
        if dur < 90:
            verdict = "FAIL"
            reasons.append(f"片長 {hhmmss(dur)} < 90 秒")
        if dur > 5400:
            verdict = "FAIL"
            reasons.append(f"片長 {hhmmss(dur)} > 90 分")
        if ud and ud < CUT and not c.get("classic_exception_reason"):
            if verdict == "PASS":
                verdict = "REVIEW"
            reasons.append(f"上架 {ud} 早於 cutoff {CUT}，但未附破例理由")
        dc = c.get("channel") or ""
        ac = j.get("channel") or j.get("uploader") or ""
        if (
            dc
            and ac
            and dc.strip().lower() not in ac.strip().lower()
            and ac.strip().lower() not in dc.strip().lower()
        ):
            if verdict == "PASS":
                verdict = "REVIEW"
            reasons.append(f"頻道不符：宣稱「{dc}」實際「{ac}」")
        if c.get("upload_date") and ud and c["upload_date"] != ud:
            if verdict == "PASS":
                verdict = "REVIEW"
            reasons.append(f"上架日不符：宣稱 {c['upload_date']} 實際 {ud}")
        if c.get("duration") and hhmmss(dur) and c["duration"] != hhmmss(dur):
            reasons.append(f"片長標示差異：宣稱 {c['duration']} 實際 {hhmmss(dur)}（±秒可忽略）")
    res.append(
        {
            **c,
            "_verdict": verdict,
            "_reasons": reasons,
            "_actual": {
                "title": j.get("title"),
                "channel": j.get("channel") or j.get("uploader"),
                "channel_url": j.get("channel_url"),
                "upload_date": ud,
                "duration": hhmmss(j.get("duration")),
                "duration_seconds": j.get("duration"),
                "playable_in_embed": j.get("playable_in_embed"),
                "availability": j.get("availability"),
                "view_count": j.get("view_count"),
                "en_captions_manual": en_m,
                "en_captions_auto": en_a,
                "error": j.get("_error"),
            },
        }
    )
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2))
print(f"→ {OUT}", file=sys.stderr)
