"""VTT → [MM:SS] 文字，去 rolling 重複，並依 diagnostic_segment_range 裁切介入段落。"""

import html
import json
import re
import sys
from pathlib import Path

SUBS = Path(sys.argv[1])
SYL = Path(sys.argv[2])
OUT = Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)


def to_sec(ts):
    parts = [float(p) for p in ts.replace(",", ".").split(":")]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def fmt(sec):
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


TIME = re.compile(r"^(\d{1,2}:\d{2}:\d{2}[.,]\d{3})\s+-->\s+(\d{1,2}:\d{2}:\d{2}[.,]\d{3})")
TAG = re.compile(r"<[^>]+>")


def parse_vtt(p):
    cues, start = [], None
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = TIME.match(line.strip())
        if m:
            start = to_sec(m.group(1))
            buf = []
            cues.append([start, buf])
            continue
        if start is None or not line.strip():
            continue
        if line.strip().startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        txt = html.unescape(TAG.sub("", line)).replace("\xa0", " ").strip()
        if txt:
            cues[-1][1].append(txt)
    return [(s, " ".join(b)) for s, b in cues if b]


def dedupe(cues):
    """自動字幕的 rolling window：後一句常包含前一句。只保留新增的尾巴。"""
    out, prev = [], ""
    for s, t in cues:
        t = re.sub(r"\s+", " ", t).strip()
        if not t:
            continue
        if t == prev:
            continue
        if prev and t.startswith(prev):
            new = t[len(prev) :].strip()
        elif prev and prev.endswith(t):
            continue
        else:
            new = t
        if new:
            out.append((s, new))
            prev = t
    return out


def parse_ranges(spec):
    if not spec:
        return None
    rs = []
    for part in re.split(r"[、,]", spec):
        part = part.strip().replace("–", "-").replace("—", "-")
        if not part:
            continue
        a, _, b = part.partition("-")
        if not b:
            continue
        rs.append((to_sec(a.strip()), to_sec(b.strip())))
    return rs or None


def in_ranges(t, rs):
    return rs is None or any(a <= t <= b for a, b in rs)


syl = json.loads(SYL.read_text())
drills = {}
for ch in syl["chapters"]:
    for u in ch["units"]:
        for d in u.get("drills", []):
            vid = d["url"].split("v=")[-1][:11]
            drills[vid] = (u["id"], d)

summary = []
for vid, (uid, d) in drills.items():
    cands = [SUBS / f"{vid}.en.vtt", SUBS / f"{vid}.en-orig.vtt"]
    src = next((c for c in cands if c.exists()), None)
    if src is None:
        summary.append((vid, uid, "NO_VTT", 0, 0))
        continue
    cues = dedupe(parse_vtt(src))
    rs = parse_ranges(d.get("diagnostic_segment_range"))
    kept = [(s, t) for s, t in cues if in_ranges(s, rs)]
    body = "\n".join(f"[{fmt(s)}] {t}" for s, t in kept)
    header = (
        f"# {d.get('title')}\n"
        f"# video_id: {vid} | unit: {uid} | duration: {d.get('duration')}\n"
        f"# channel: {d.get('channel')} | presenter: {d.get('presenter')}\n"
        f"# 診斷框限: {d.get('diagnostic_segment_range') or '全片'}\n"
        f"# 介入起點: {d.get('intervention_start_timestamp') or '無'}\n"
        f"# 原始 cue: {len(cues)} → 框限後: {len(kept)}\n\n"
    )
    (OUT / f"{vid}.txt").write_text(header + body, encoding="utf-8")
    summary.append((vid, uid, "OK", len(cues), len(kept)))

print(f"{'video_id':13} {'unit':8} {'狀態':8} {'原始':>6} {'框限後':>6} {'裁掉':>6}")
for vid, uid, st, a, b in sorted(summary, key=lambda x: x[1]):
    print(f"{vid:13} {uid:8} {st:8} {a:>6} {b:>6} {a - b:>6}")
