"""本地驗證逐段筆記初稿：時間戳合法性、遞增不重疊、框限、欄位長度。與 audit_medical.check_segments 同規則。"""
import json
import pathlib
import sys

SYL = json.loads((pathlib.Path(__file__).resolve().parent.parent / "course/data/syllabus.json").read_text())
VID = {}
for c in SYL["chapters"]:
    for u in c["units"]:
        for dr in u.get("drills", []):
            VID[dr["url"].split("v=")[-1]] = dr


def clock(s):
    try:
        parts = [int(p) for p in str(s).split(":")]
    except ValueError:
        return None
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


def ranges(text):
    out = []
    for part in str(text or "").replace("—", "–").split(","):
        part = part.strip()
        if "–" not in part:
            continue
        a, b = part.split("–", 1)
        sa, sb = clock(a.strip()), clock(b.strip())
        if sa is not None and sb is not None:
            out.append((sa, sb))
    return out or None


def check(vid, entry):
    errs = []
    v = VID.get(vid)
    if not v:
        return [f"{vid} 不在 syllabus"]
    segs = entry.get("segments")
    if not isinstance(segs, list) or not segs:
        return [f"{vid}: segments 空"]
    dur = clock(v.get("duration"))
    rg = ranges(v.get("diagnostic_segment_range"))
    prev = None
    for i, s in enumerate(segs, 1):
        w = f"{vid} 第{i}段"
        st, en = clock(s.get("start")), clock(s.get("end"))
        if st is None or en is None:
            errs.append(f"{w}: 時間格式錯 {s.get('start')}~{s.get('end')}")
            continue
        if st >= en:
            errs.append(f"{w}: start>=end")
            continue
        if prev is not None and st <= prev:
            errs.append(f"{w}: 與前段重疊/不遞增 ({s['start']} <= 前段 end)")
        prev = en
        if dur is not None and en > dur:
            errs.append(f"{w}: end 超出片長 ({s['end']} > {v['duration']})")
        if rg and not any(a <= st and en <= b for a, b in rg):
            errs.append(f"{w}: 超出框限 {v['diagnostic_segment_range']}")
        if len(str(s.get("title", "")).strip()) < 4:
            errs.append(f"{w}: title 太短")
        if len(str(s.get("summary", "")).strip()) < 10:
            errs.append(f"{w}: summary 太短")
        if not isinstance(s.get("detail"), list) or not s["detail"]:
            errs.append(f"{w}: detail 空")
    if not str(entry.get("note", "")).strip():
        errs.append(f"{vid}: note 缺")
    return errs


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(pathlib.Path("/tmp/sh-drafts").glob("*.json"))
    bad = 0
    for f in files:
        f = pathlib.Path(f)
        vid = f.stem
        e = check(vid, json.loads(f.read_text()))
        if e:
            bad += 1
            print(f"❌ {vid}")
            for m in e:
                print("   ", m)
        else:
            n = len(json.loads(f.read_text())["segments"])
            print(f"✅ {vid} {n} 段")
    print(f"--- {len(files)} 支，{bad} 支有問題 ---")
