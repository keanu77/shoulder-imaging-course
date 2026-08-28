"""掃字幕密度（字元數÷片長秒數），找出沒有有效字幕、不值得派逐段筆記工的影片。

派工前先跑這支。實務上正常影片落在 19–35 字元/秒；明顯離群的低值代表該片
只有片頭片尾字幕、主體講解沒有字幕軌，產出的段落沒有教學價值。
"""

import json
import re
import sys
from pathlib import Path

TRANSCRIPTS = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/sh-transcripts")
SYLLABUS = Path(sys.argv[2] if len(sys.argv) > 2 else "course/data/syllabus.json")
THRESHOLD = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0


def to_seconds(clock: str) -> int:
    parts = [int(p) for p in str(clock).split(":")]
    return parts[0] * 60 + parts[1] if len(parts) == 2 else parts[0] * 3600 + parts[1] * 60 + parts[2]


def main() -> int:
    syllabus = json.loads(SYLLABUS.read_text())
    rows = []
    for chapter in syllabus["chapters"]:
        for unit in chapter["units"]:
            for drill in unit.get("drills", []):
                video_id = drill["url"].split("v=")[-1]
                path = TRANSCRIPTS / f"{video_id}.txt"
                if not path.exists():
                    rows.append((0.0, 0, video_id, drill["name"], "逐字稿缺漏"))
                    continue
                body = [ln for ln in path.read_text().splitlines() if ln.startswith("[")]
                chars = sum(len(re.sub(r"^\[[\d:]+\]\s*", "", ln)) for ln in body)
                seconds = max(to_seconds(drill["duration"]), 1)
                rows.append((chars / seconds, chars, video_id, drill["name"], ""))

    rows.sort()
    sparse = [r for r in rows if r[0] < THRESHOLD]
    print(f"{'字元/秒':>7} {'字元':>7}  video_id      單元名")
    for density, chars, video_id, name, note in rows:
        flag = "  ⚠️ 稀疏" if density < THRESHOLD else ""
        print(f"{density:7.1f} {chars:7d}  {video_id:12s} {name[:34]}{flag}{note}")
    print(f"\n{len(rows)} 支，{len(sparse)} 支低於 {THRESHOLD} 字元/秒")
    return 1 if sparse else 0


if __name__ == "__main__":
    raise SystemExit(main())
