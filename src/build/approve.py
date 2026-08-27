#!/usr/bin/env python3
"""approve.py — 醫師簽核工具：segments（逐段筆記）、questions（知識檢核）、glossary（名詞表）。

用法：
  uv run python src/build/approve.py segments <youtube-id-或-url> --by 姓名 --role 職稱
  uv run python src/build/approve.py questions <unit-id|all> --by 姓名 --role 職稱
  uv run python src/build/approve.py glossary --by 姓名 --role 職稱

行為：把目標的 review_status 設為 approved，寫入 reviewed_by / reviewer_role /
reviewed_at / reviewed_commit（當前 HEAD）。簽核代表具名醫師已逐項確認內容；
本工具只記錄事實，不做任何內容驗證——先跑 make audit 確保結構通過。
"""
from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "course" / "data"


def head_commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()


def stamp(entry: dict, by: str, role: str, commit: str) -> None:
    entry["review_status"] = "approved"
    entry["reviewed_by"] = by
    entry["reviewer_role"] = role
    entry["reviewed_at"] = datetime.date.today().isoformat()
    entry["reviewed_commit"] = commit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["segments", "questions", "glossary"])
    ap.add_argument("target", nargs="?", help="segments: youtube id/url；questions: unit id 或 all")
    ap.add_argument("--by", required=True)
    ap.add_argument("--role", required=True)
    args = ap.parse_args()

    commit = head_commit()
    if args.kind == "glossary":
        path = DATA / "glossary.json"
        blob = json.loads(path.read_text())
        stamp(blob, args.by, args.role, commit)
        path.write_text(json.dumps(blob, ensure_ascii=False, indent=2) + "\n")
        print(f"glossary → approved（{len(blob.get('terms') or [])} 條）@ {commit[:8]}")
        return 0

    if not args.target:
        print("此類型需要 target", file=sys.stderr)
        return 1

    if args.kind == "segments":
        path = DATA / "segments.json"
        blob = json.loads(path.read_text())
        hits = [v for v in blob.get("videos", []) if args.target in (v.get("video_url") or "")]
        if len(hits) != 1:
            print(f"匹配 {len(hits)} 支影片，需恰好 1 支", file=sys.stderr)
            return 1
        stamp(hits[0], args.by, args.role, commit)
        path.write_text(json.dumps(blob, ensure_ascii=False, indent=2) + "\n")
        print(f"segments {hits[0]['video_url']} → approved（{len(hits[0]['segments'])} 段）@ {commit[:8]}")
        return 0

    path = DATA / "questions.json"
    blob = json.loads(path.read_text())
    units = blob.get("units") or {}
    targets = list(units) if args.target == "all" else [args.target]
    for uid in targets:
        if uid not in units:
            print(f"找不到題組：{uid}", file=sys.stderr)
            return 1
        stamp(units[uid], args.by, args.role, commit)
        print(f"questions {uid} → approved（{len(units[uid]['questions'])} 題）@ {commit[:8]}")
    path.write_text(json.dumps(blob, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
