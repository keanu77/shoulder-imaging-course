#!/usr/bin/env python3
"""checklist.py — 從 syllabus 產生可列印的一頁式判讀檢核表（dist/checklist.html）。

只收 review_status == "approved" 的單元：檢核表是給實機掃描/判讀用的臨床工件，
未簽核內容不出現（與 segments 只輸出 approved 的治理一致）。
"""
from __future__ import annotations

import datetime
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def esc(s: str) -> str:
    return html.escape(str(s or ""), quote=True)


def generate(dist: Path) -> int:
    cfg = json.loads((ROOT / "course" / "course.config.json").read_text())
    syl = json.loads((ROOT / "course" / "data" / "syllabus.json").read_text())
    site = cfg.get("site", {})
    nav = cfg.get("nav", [])
    ch_by_code = {c["chapter"]: c for c in syl["chapters"]}

    today = datetime.date.today().isoformat()
    sections: list[str] = []
    n_units = 0
    for group in nav:
        group_units: list[str] = []
        for code in group.get("chapters", []):
            ch = ch_by_code.get(code)
            if not ch:
                continue
            for u in ch.get("units", []):
                if u.get("review_status") != "approved":
                    continue
                n_units += 1
                views = "".join(
                    f'<li><span class="box" aria-hidden="true"></span>{esc(v)}</li>'
                    for v in u.get("required_views", []))
                keys = "".join(f"<li>{esc(k)}</li>" for k in u.get("key_points", []))
                pits = "".join(f"<li>{esc(p)}</li>" for p in u.get("pitfalls", []))
                group_units.append(f"""
<article class="unit">
  <h3>{esc(ch.get('title'))}｜{esc(u.get('name'))}</h3>
  <div class="cols">
    <section><h4>必備視圖（逐項打勾）</h4><ul class="check">{views}</ul></section>
    <section><h4>操作重點</h4><ul>{keys}</ul></section>
    <section class="warn"><h4>常見陷阱</h4><ul>{pits}</ul></section>
  </div>
</article>""")
        if group_units:
            sections.append(
                f'<section class="group"><h2>{esc(group.get("title"))}</h2>{"".join(group_units)}</section>')

    doc = f"""<!doctype html>
<html lang="zh-Hant-TW"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{esc(site.get('name'))}｜判讀檢核表</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, "Noto Sans TC", "PingFang TC", sans-serif;
         margin: 0 auto; max-width: 960px; padding: 24px; font-size: 14px;
         line-height: 1.6; color: #1f2328; background: #fff; }}
  header h1 {{ font-size: 22px; margin: 0 0 4px; }}
  header p {{ margin: 2px 0; color: #59636e; font-size: 12px; max-width: 76ch; }}
  .group > h2 {{ font-size: 17px; border-bottom: 2px solid #1f2328; padding-bottom: 4px;
                 margin: 28px 0 8px; page-break-after: avoid; }}
  .unit {{ border: 1px solid #d1d9e0; border-radius: 8px; padding: 12px 16px;
           margin: 10px 0; page-break-inside: avoid; }}
  .unit h3 {{ font-size: 14px; margin: 0 0 8px; }}
  .cols {{ display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 16px; }}
  @media (max-width: 720px) {{ .cols {{ grid-template-columns: 1fr; }} }}
  h4 {{ font-size: 12px; margin: 0 0 6px; color: #59636e; text-transform: none; }}
  ul {{ margin: 0; padding-left: 18px; }}
  ul.check {{ list-style: none; padding-left: 0; }}
  ul.check li {{ display: flex; gap: 8px; margin: 4px 0; }}
  .box {{ flex: none; width: 13px; height: 13px; margin-top: 3px;
          border: 1.5px solid #1f2328; border-radius: 3px; }}
  li {{ margin: 3px 0; }}
  .warn h4 {{ color: #9a6700; }}
  .print-btn {{ position: fixed; right: 16px; top: 16px; padding: 8px 14px;
                border: 1px solid #d1d9e0; border-radius: 6px; background: #f6f8fa;
                font: inherit; cursor: pointer; }}
  footer {{ margin-top: 24px; padding-top: 12px; border-top: 1px solid #d1d9e0;
            font-size: 11px; color: #59636e; max-width: 76ch; }}
  @media print {{ .print-btn {{ display: none; }} body {{ padding: 0; font-size: 12px; }} }}
</style></head><body>
<button class="print-btn" onclick="print()">列印／存成 PDF</button>
<header>
  <h1>{esc(site.get('name'))}｜判讀檢核表</h1>
  <p>由已簽核（approved）單元自動彙整（{n_units} 個單元）・產生日期 {today}・{esc(site.get('url'))}</p>
  <p>僅供醫師專業教育；不取代 hands-on training、合格督導與機構 credentialing。未簽核章節（草稿）不收錄。</p>
</header>
{"".join(sections)}
<footer>{esc(cfg.get('stance', {}).get('intro', ''))}</footer>
</body></html>"""
    out = dist / "checklist.html"
    out.write_text(doc)
    print(f"   checklist.html（{n_units} 個 approved 單元）")
    return n_units
