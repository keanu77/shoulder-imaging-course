"""實查課程站影片：yt-dlp -j + YouTube oEmbed，核對頻道／片長／上架日／可嵌入／英文字幕。"""

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

SYL = Path(sys.argv[1])
OUT = Path(sys.argv[2])


def vid(url):
    m = re.search(r"[?&]v=([\w-]+)", url)
    return m.group(1) if m else None


def oembed(url):
    api = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(url, safe="")
    try:
        with urllib.request.urlopen(api, timeout=15) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}"}
    except Exception as e:
        return {"_error": str(e)}


def ytdlp(url):
    p = subprocess.run(
        ["yt-dlp", "-j", "--no-warnings", url], capture_output=True, text=True, timeout=180
    )
    if p.returncode != 0:
        return {
            "_error": p.stderr.strip().splitlines()[-1]
            if p.stderr.strip()
            else f"rc={p.returncode}"
        }
    return json.loads(p.stdout)


def hhmmss(sec):
    if sec is None:
        return None
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


syl = json.loads(SYL.read_text())
rows = []
for ch in syl["chapters"]:
    for u in ch["units"]:
        for d in u.get("drills", []):
            rows.append((ch.get("title"), u["id"], d))

results = []
for i, (chtitle, uid, d) in enumerate(rows, 1):
    url = d.get("url", "")
    print(f"[{i}/{len(rows)}] {uid} {url}", file=sys.stderr, flush=True)
    oe = oembed(url)
    j = ytdlp(url)
    subs = j.get("subtitles") or {}
    autos = j.get("automatic_captions") or {}
    en_manual = any(k == "en" or k.startswith("en-") for k in subs)
    en_auto = any(k == "en" or k.startswith("en-") for k in autos)
    results.append(
        {
            "unit": uid,
            "chapter": chtitle,
            "video_id": vid(url),
            "url": url,
            "declared": {
                "title": d.get("title"),
                "channel": d.get("channel"),
                "duration": d.get("duration"),
                "upload_date": d.get("upload_date"),
                "original_content_date": d.get("original_content_date"),
                "presenter": d.get("presenter"),
                "contains_intervention": d.get("contains_intervention"),
                "intervention_start_timestamp": d.get("intervention_start_timestamp"),
                "diagnostic_segment_range": d.get("diagnostic_segment_range"),
                "source_authority": d.get("source_authority"),
            },
            "actual": {
                "title": j.get("title"),
                "channel": j.get("channel") or j.get("uploader"),
                "channel_id": j.get("channel_id"),
                "channel_url": j.get("channel_url"),
                "duration_seconds": j.get("duration"),
                "duration": hhmmss(j.get("duration")),
                "upload_date": j.get("upload_date"),
                "release_date": j.get("release_date"),
                "playable_in_embed": j.get("playable_in_embed"),
                "availability": j.get("availability"),
                "live_status": j.get("live_status"),
                "age_limit": j.get("age_limit"),
                "view_count": j.get("view_count"),
                "en_captions_manual": en_manual,
                "en_captions_auto": en_auto,
                "error": j.get("_error"),
            },
            "oembed": {
                "title": oe.get("title"),
                "author": oe.get("author_name"),
                "error": oe.get("_error"),
            },
        }
    )

OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2))
print(f"→ {OUT} ({len(results)} 支)", file=sys.stderr)
