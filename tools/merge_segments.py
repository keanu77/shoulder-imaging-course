"""把 /tmp/sh-drafts/*.json 初稿併入 segments.json（review_status=draft，待策展審閱）。"""
import datetime
import json
import pathlib

ROOT = pathlib.Path.home() / "Projects/shoulder-ultrasound-course"
SEG = ROOT / "course/data/segments.json"
SYL = json.loads((ROOT / "course/data/syllabus.json").read_text())

URL = {}
for c in SYL["chapters"]:
    for u in c["units"]:
        for dr in u.get("drills", []):
            URL[dr["url"].split("v=")[-1]] = dr["url"]

TODAY = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")  # CF build 跑 UTC
SOURCE = f"yt-dlp 自動字幕（en, VTT）{TODAY} 實抓，依 diagnostic_segment_range 裁切後逐段對照時間戳核對"

blob = json.loads(SEG.read_text())
if not isinstance(blob.get("videos"), list):
    blob["videos"] = []          # 空骨架原本是 {}，build.py 迭代的是 list
existing = {e.get("video_url"): e for e in blob["videos"]}

added = updated = 0
for f in sorted(pathlib.Path("/tmp/sh-drafts").glob("*.json")):
    vid = f.stem
    url = URL.get(vid)
    if not url:
        print(f"SKIP {vid}: 不在 syllabus")
        continue
    draft = json.loads(f.read_text())
    entry = {
        "video_url": url,
        "review_status": "draft",
        "transcript_verified_at": TODAY,
        "transcript_source": SOURCE,
        "note": draft["note"],
        "segments": draft["segments"],
    }
    if url in existing:
        prev = existing[url]
        if prev.get("review_status") == "approved":
            print(f"KEEP {vid}: 已簽核，不覆蓋")
            continue
        blob["videos"][blob["videos"].index(prev)] = entry
        updated += 1
    else:
        blob["videos"].append(entry)
        added += 1

blob["videos"].sort(key=lambda e: e["video_url"])
SEG.write_text(json.dumps(blob, ensure_ascii=False, indent=2) + "\n")
total = sum(len(e["segments"]) for e in blob["videos"])
print(f"新增 {added}、更新 {updated}｜segments.json 共 {len(blob['videos'])} 支 / {total} 段")
