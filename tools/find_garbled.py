"""機械預篩：找出逐字稿裡不在英文字典、也不在 MSK 術語白名單的候選訛誤詞。"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

TR = Path(sys.argv[1])
OUT = Path(sys.argv[2])

words = set()
for p in ("/usr/share/dict/words", "/usr/share/dict/web2"):
    f = Path(p)
    if f.exists():
        words |= {
            w.strip().lower() for w in f.read_text(errors="replace").splitlines() if w.strip()
        }

# 正確的 MSK／肩部術語白名單（字典裡沒有但不是訛誤）
# 正確的 MSK 術語白名單（字典裡沒有但不是訛誤）。換部位時把這裡換成該部位的術語。
# 正確的 MSK 術語白名單（字典裡沒有但不是訛誤）。換部位時把這裡換成該部位的術語。
_MSK_TERMS = """
abducted abduction acr acromial acromioclavicular acromion adducted adduction
adhesive aium alpsa anechoic anisotropic anisotropy arthrogram arthrography atrophy
axial bankart biceps bicipital buford bursa bursae bursitis calcific calcification
capsular capsule capsulitis clavicle clavicular coracoacromial coracohumeral
coracoid coronal cortex cortical crass cuff delamination deltoid density doppler
echogenic echogenicity effusion empty enthesis enthesopathy essr external
extraarticular fatsat fatty footprint gadolinium glad glenohumeral glenoid
goutallier hagl hawkins hillsachs humeral humerus hydroxyapatite hyperechoic
hypoechoic infiltration infraspinatus internal intraarticular isoechoic jobe labral
labrum latissimus ligament ligamentous modified mri msk musculotendinous
myotendinous neer ntuh oblique osteoarthritis osteophyte osteophytes pectoralis
perthes physiatrist prone proton radiologist retraction rhomboid rmsk rotation
rotator rsna sagittal scapula scapular slap sonoanatomy sonographer sonographic
sonography sternoclavicular stir subacromial subchondral subdeltoid subscapularis
supine supraspinatus synovial synovitis tendinopathy tendinosis tendinous teres
transducer transverse trapezius tuberosities tuberosity ultrasonography ultrasound
"""

white = set(_MSK_TERMS.split())

_STOP_TERMS = "um uh okay yeah gonna wanna kinda sorta ok yep nope hmm mm nbsp"
STOP = set(_STOP_TERMS.split())

SUF = ["s", "es", "ed", "d", "ing", "er", "est", "ly", "ers", "ings"]


def known(w):
    """詞形還原後查字典／白名單，濾掉 called / located / using 這類雜訊。"""
    if w in words or w in white:
        return True
    for suf in SUF:
        if w.endswith(suf) and len(w) > len(suf) + 2:
            base = w[: -len(suf)]
            for cand in (
                base,
                base + "e",
                base[:-1] if len(base) > 3 and base[-1] == base[-2] else None,
            ):
                if cand and (cand in words or cand in white):
                    return True
            if base.endswith("i"):
                cand = base[:-1] + "y"
                if cand in words or cand in white:
                    return True
    return False


def toks(t):
    return re.findall(r"[a-zA-Z][a-zA-Z'\-]{2,}", t)


counts = Counter()
ctx = defaultdict(list)
per_video = defaultdict(Counter)

for f in sorted(TR.glob("*.txt")):
    vid = f.stem
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        m = re.match(r"^\[([\d:]+)\]\s*(.*)$", line)
        if not m:
            continue
        ts, text = m.groups()
        for w in toks(text):
            lw = w.lower().strip("-'")
            if not lw or lw in STOP or lw in white or lw in words:
                continue
            if "'" in lw:
                continue  # 縮寫（you're / don't）不是訛誤
            if known(lw):
                continue
            counts[lw] += 1
            per_video[vid][lw] += 1
            if len(ctx[lw]) < 3:
                ctx[lw].append(f"{vid} [{ts}] {text[:110]}")

out = []
for w, n in counts.most_common():
    if n < 2:
        continue  # 只出現一次的多半是雜訊
    out.append(
        {
            "word": w,
            "count": n,
            "videos": dict(
                sorted(
                    ((v, c) for v, cc in per_video.items() for w2, c in cc.items() if w2 == w),
                    key=lambda x: -x[1],
                )
            ),
            "context": ctx[w],
        }
    )

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
print(
    f"字典詞數 {len(words)}；候選訛誤詞 {len(out)}（出現 ≥2 次）；總命中 {sum(o['count'] for o in out)}"
)
for o in out[:40]:
    print(f"  {o['count']:4}  {o['word']}")
