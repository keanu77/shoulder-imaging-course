#!/usr/bin/env python3
"""逐段筆記搜尋的行為測試。

這些函式決定「學員搜一個詞，會不會被帶到正確的那一段」，錯了不會有任何畫面報錯，
所以用反例把邊界釘死：空查詢不得標亮全頁、HTML 不得被注入、命中位置不得錯位。
用 node 直接載入 src/web/js/segment-search.js（該模組刻意零相依）。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "src" / "web" / "js" / "segment-search.js"

HARNESS_TEMPLATE = """
import { segmentMatches, segmentHitCount, highlight, escapeHtml, segmentHaystack }
  from "__MODULE_URI__";
const cases = JSON.parse(process.env.SEGMENT_SEARCH_CASES);
const out = cases.map((c) => {
  switch (c.fn) {
    case "segmentMatches":  return segmentMatches(c.args[0], c.args[1]);
    case "segmentHitCount": return segmentHitCount(c.args[0], c.args[1]);
    case "highlight":       return highlight(c.args[0], c.args[1]);
    case "escapeHtml":      return escapeHtml(c.args[0]);
    case "segmentHaystack": return segmentHaystack(c.args[0]);
    default: throw new Error("unknown fn " + c.fn);
  }
});
process.stdout.write(JSON.stringify(out));
"""

HARNESS = HARNESS_TEMPLATE.replace("__MODULE_URI__", MODULE.as_uri())


def run(cases: list[dict]):
    p = subprocess.run(
        ["node", "--input-type=module", "--eval", HARNESS],
        capture_output=True,
        text=True,
        env={**os.environ, "SEGMENT_SEARCH_CASES": json.dumps(cases, ensure_ascii=False)},
    )
    if p.returncode != 0:
        print(p.stderr.strip(), file=sys.stderr)
        raise SystemExit("node 執行失敗")
    return json.loads(p.stdout)


SEG = {
    "title": "棘上肌長軸與附著面",
    "summary": "以 Crass 或 modified Crass 姿勢取得棘上肌長軸。",
    "detail": ["注意 anisotropy 造成的假性低回音", "對照對側可減少過度解讀"],
}

CASES = [
    # --- 正例：三個欄位都要搜得到 ---
    ({"fn": "segmentMatches", "args": [SEG, "棘上肌"]}, True, "標題命中"),
    ({"fn": "segmentMatches", "args": [SEG, "Crass"]}, True, "摘要命中（大小寫不敏感）"),
    ({"fn": "segmentMatches", "args": [SEG, "crass"]}, True, "摘要命中（小寫查詢）"),
    ({"fn": "segmentMatches", "args": [SEG, "anisotropy"]}, True, "詳解命中"),
    ({"fn": "segmentMatches", "args": [SEG, "  棘上肌  "]}, True, "查詢前後空白要忽略"),
    # --- 反例 ---
    ({"fn": "segmentMatches", "args": [SEG, "棘下肌"]}, False, "沒提到就不能命中"),
    ({"fn": "segmentMatches", "args": [SEG, ""]}, False, "空查詢不得命中（否則整頁標亮）"),
    ({"fn": "segmentMatches", "args": [SEG, "   "]}, False, "純空白查詢不得命中"),
    ({"fn": "segmentMatches", "args": [None, "棘上肌"]}, False, "段落是 null 不得爆掉"),
    ({"fn": "segmentHaystack", "args": [None]}, "", "null 段落攤平成空字串"),
    # --- 命中計數 ---
    ({"fn": "segmentHitCount", "args": [[SEG, SEG, {"title": "後側"}], "棘上肌"]}, 2, "只算命中的段"),
    ({"fn": "segmentHitCount", "args": [[SEG], ""]}, 0, "空查詢命中數為 0"),
    ({"fn": "segmentHitCount", "args": [None, "棘上肌"]}, 0, "segments 是 null 不得爆掉"),
    # --- 標亮：位置正確且不得注入 ---
    (
        {"fn": "highlight", "args": ["棘上肌長軸", "棘上肌"]},
        '<mark class="Hit">棘上肌</mark>長軸',
        "命中處包 mark",
    ),
    (
        {"fn": "highlight", "args": ["Crass 與 modified Crass", "crass"]},
        '<mark class="Hit">Crass</mark> 與 modified <mark class="Hit">Crass</mark>',
        "多處命中都要標，且保留原文大小寫",
    ),
    (
        {"fn": "highlight", "args": ["<script>alert(1)</script>", ""]},
        "&lt;script&gt;alert(1)&lt;/script&gt;",
        "空查詢時仍必須 escape",
    ),
    (
        {"fn": "highlight", "args": ["<b>棘上肌</b>", "棘上肌"]},
        '&lt;b&gt;<mark class="Hit">棘上肌</mark>&lt;/b&gt;',
        "標亮不得繞過 escape",
    ),
    (
        {"fn": "highlight", "args": ["a<b", "<"]},
        'a<mark class="Hit">&lt;</mark>b',
        "查詢字本身是 HTML 特殊字元時也要 escape",
    ),
    ({"fn": "highlight", "args": [None, "x"]}, "", "null 文字回空字串"),
]

results = run([c[0] for c in CASES])
fails = 0
for (case, want, why), got in zip(CASES, results, strict=True):
    if got != want:
        fails += 1
        print(f"✗ {why}\n    {case['fn']}{case['args']!r}\n    期望 {want!r}\n    實際 {got!r}")

if fails:
    print(f"\n✗ {fails}/{len(CASES)} 項失敗")
    raise SystemExit(1)
print(f"✅ 全部 {len(CASES)} 項通過（正例 5 / 反例與邊界 {len(CASES) - 5}）")
