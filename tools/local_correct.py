"""用本地 ollama 判斷字幕候選詞是訛誤還是正常詞，並給出正確術語。"""

import contextlib
import json
import sys
import time
import urllib.request
from pathlib import Path

CAND = Path(sys.argv[1])
OUT = Path(sys.argv[2])
MODEL = "qwen3.8:27b-mlx"
BATCH = 25

SYS = """You audit YouTube auto-caption transcripts of SHOULDER musculoskeletal ultrasound
lectures given by physicians. Auto-captions mangle anatomical and radiological terms.

For each candidate word you are given (with real usage context from the transcripts),
decide ONE of:
- "misrecognition": it is a mangled form of a real anatomical/radiological/clinical term
- "ok": it is a legitimate word, abbreviation, brand, proper noun, or clinical shorthand
        that simply is not in a plain English dictionary
- "unclear": you cannot tell from the context

Only mark "misrecognition" when you are confident what the intended term is.
Use the context lines - they show how the word is actually used.

Return ONLY a JSON array, one object per candidate, no prose, no markdown fence:
[{"word":"<as given>","verdict":"misrecognition|ok|unclear","correct":"<intended term, or null>","why":"<max 12 words>"}]
"""


def ask(items):
    lines = []
    for it in items:
        ctx = " / ".join(c.split("] ", 1)[-1][:90] for c in it["context"][:2])
        lines.append(f'- "{it["word"]}" (x{it["count"]}) ctx: {ctx}')
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYS},
            {"role": "user", "content": "Candidates:\n" + "\n".join(lines)},
        ],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.1, "num_ctx": 16384},
    }
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.load(r)["message"]["content"]


def salvage(raw):
    s = raw.strip()
    i = s.find("[{")
    if i < 0:
        i = s.find("[")
    if i >= 0:
        j = s.rfind("]")
        if j > i:
            try:
                return json.loads(s[i : j + 1])
            except Exception:
                pass
    import re

    out = []
    for m in re.finditer(r'\{[^{}]*"word"[^{}]*\}', s):
        # 逐物件救回：模型偶爾會在陣列中途截斷，能救幾筆是幾筆
        with contextlib.suppress(Exception):
            out.append(json.loads(m.group(0)))
    return out


cands = json.loads(CAND.read_text())
results, t0 = [], time.time()
for i in range(0, len(cands), BATCH):
    chunk = cands[i : i + BATCH]
    try:
        got = salvage(ask(chunk))
    except Exception as e:
        print(f"batch {i // BATCH + 1} 失敗: {e}", file=sys.stderr)
        got = []
    results.extend(got)
    print(
        f"batch {i // BATCH + 1}/{(len(cands) + BATCH - 1) // BATCH}  +{len(got)}  累計 {len(results)}  {time.time() - t0:.0f}s",
        file=sys.stderr,
        flush=True,
    )

OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2))
mis = [r for r in results if r.get("verdict") == "misrecognition"]
print(f"→ {OUT}：{len(results)} 判定，其中 misrecognition {len(mis)}", file=sys.stderr)
