"""掃描候選片字幕的介入操作內容，定出 intervention_start_timestamp 候選。"""

import html
import json
import re
import sys
from pathlib import Path

SUBS = Path(sys.argv[1])
POOL = Path(sys.argv[2])

TIME = re.compile(r"^(\d{1,2}:\d{2}:\d{2}[.,]\d{3})\s+-->")
TAG = re.compile(r"<[^>]+>")
KW = re.compile(
    r"\b(inject\w*|needle\w*|aspirat\w*|steroid\w*|sterile|lidocaine|corticosteroid|"
    r"hydrodissect\w*|barbotage|anesthetic|anaesthetic|betadine|chlorhexidine|"
    r"fluoroscop\w*.{0,20}guid\w*|under\s+ultrasound\s+guidance)\b",
    re.I,
)


def sec(ts):
    p = [float(x) for x in ts.replace(",", ".").split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2]


def fmt(s):
    s = int(s)
    h, r = divmod(s, 3600)
    m, x = divmod(r, 60)
    return f"{h}:{m:02d}:{x:02d}" if h else f"{m:02d}:{x:02d}"


def cues(p):
    out = []
    st = None
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = TIME.match(line.strip())
        if m:
            st = sec(m.group(1))
            out.append([st, []])
            continue
        if st is None or not line.strip():
            continue
        if line.strip().startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        t = html.unescape(TAG.sub("", line)).strip()
        if t:
            out[-1][1].append(t)
    seen = set()
    res = []
    for s, b in out:
        t = re.sub(r"\s+", " ", " ".join(b)).strip()
        if t and t not in seen:
            seen.add(t)
            res.append((s, t))
    return res


pool = json.loads(POOL.read_text())
for d in pool:
    vid = d["url"][-11:]
    p = SUBS / f"{vid}.en.vtt"
    if not p.exists():
        p = SUBS / f"{vid}.en-orig.vtt"
    if not p.exists():
        print(f"\n### {vid} [{d['slot']}] — 無字幕")
        continue
    c = cues(p)
    hits = [(s, t) for s, t in c if KW.search(t)]
    dur = d["_actual"].get("duration_seconds") or 0
    print(f"\n### {vid} [{d['slot']}] {d['_actual']['duration']}  命中 {len(hits)}/{len(c)} cue")
    if not hits:
        print("    ✓ 全片無介入關鍵字")
        continue
    for s, t in hits[:12]:
        print(f"    [{fmt(s)}] {t[:100]}")
    if len(hits) > 12:
        print(f"    …另 {len(hits) - 12} 處")
    first = hits[0][0]
    last = hits[-1][0]
    print(f"    ⚑ 首次 {fmt(first)}（{first / dur:.0%}）  末次 {fmt(last)}（{last / dur:.0%}）")
