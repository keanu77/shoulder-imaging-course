#!/usr/bin/env python3
"""驗證課程參考來源連結，以及舊式 PubMed 引用的 PMID／標題配對。

不信任任何上游宣稱（含 agent 自稱已驗證），一律重打 PubMed E-utilities。
捏造的引用比沒有引用更糟，這是最後一道關卡。

用法：
    python3 verify_refs.py           # 驗證並列出不符者
    python3 verify_refs.py --fix     # 額外用 API 回傳值覆寫 title/journal/year
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COURSE_DIR = Path(os.environ.get("COURSE") or ROOT / "course").resolve()
DATA = COURSE_DIR / "data"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
BATCH = 180
_SITE = json.loads((COURSE_DIR / "course.config.json").read_text(encoding="utf-8"))["site"]
USER_AGENT = f"{_SITE['project']}/1.0 (+{_SITE['url']})"


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def fetch(pmids: list[str]) -> dict:
    data = urllib.parse.urlencode(
        {"db": "pubmed", "retmode": "json", "id": ",".join(pmids)}
    ).encode()
    req = urllib.request.Request(ESUMMARY, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.loads(res.read()).get("result", {})


BLOBS: dict[Path, dict] = {}


def collect() -> list[tuple[str, str, str, dict]]:
    """回傳 (檔名, 類別／單元 id, pmid, citation dict)。citation 是可就地修改的參照。

    兩層都要驗：`drill-evidence-*.json` 的類別層級，以及 `oe-*.json` 的單元層級。
    只驗其中一層等於留了一半的門沒鎖。
    """
    out = []
    sources = [
        ("drill-evidence-*.json", "categories", "id"),
        ("oe-*.json", "conditions", "unit"),
    ]
    for pattern, key, id_field in sources:
        for path in sorted(DATA.glob(pattern)):
            blob = json.loads(path.read_text())
            BLOBS[path] = blob
            for entry in blob.get(key, []):
                if not isinstance(entry, dict):
                    continue
                eid = entry.get(id_field, "?")
                for c in entry.get("citations", []):
                    pmid = str(c.get("pmid") or "").strip()
                    out.append((path.name, eid, pmid if pmid.isdigit() else "", c))
    return out


def collect_reference_urls() -> list[tuple[str, str, str]]:
    """回傳 syllabus 等來源檔內 reference_catalog 的 id、title、url。"""
    out = []
    for path in sorted(DATA.glob("*.json")):
        try:
            blob = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        for reference_id, reference in (blob.get("reference_catalog") or {}).items():
            url = reference.get("url", "")
            if url:
                out.append((reference_id, reference.get("title", ""), url))
    return out


def check_url(url: str) -> tuple[bool, str]:
    """以小型 GET 驗證公開來源；Range 可避免下載完整 PDF。"""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Range": "bytes=0-2047"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return 200 <= response.status < 400, str(response.status)
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError) as exc:
        return False, str(exc.reason if isinstance(exc, urllib.error.URLError) else exc)


def main() -> int:
    fix = "--fix" in sys.argv
    rows = collect()
    bad_pmid = [r for r in rows if not r[2]]
    rows = [r for r in rows if r[2]]
    pmids = sorted({r[2] for r in rows})

    catalog_urls = collect_reference_urls()
    print(
        f"檢查 {len(catalog_urls)} 筆 reference_catalog 來源，"
        f"以及 {len(rows)} 筆舊式引用（{len(pmids)} 個不重複 PMID）…\n"
    )

    bad_urls = []
    for reference_id, title, url in catalog_urls:
        ok_url, status = check_url(url)
        print(f"{'✓' if ok_url else '✗'} {reference_id} · {status} · {title[:68]}")
        if not ok_url:
            bad_urls.append((reference_id, status, url))

    meta: dict = {}
    for i in range(0, len(pmids), BATCH):
        meta.update(fetch(pmids[i : i + BATCH]))
        time.sleep(0.4)

    missing, mismatch = [], []
    for fname, cid, pmid, c in rows:
        rec = meta.get(pmid)
        if not rec or rec.get("error") or not rec.get("title"):
            missing.append((fname, cid, pmid, c.get("title", "")))
            continue
        actual, claimed = rec["title"].rstrip("."), c.get("title", "")
        a, b = norm(actual), norm(claimed)
        if not (a.startswith(b[:55]) or b.startswith(a[:55]) or b[:55] in a):
            mismatch.append((fname, cid, pmid, claimed, actual))
        if fix:
            c["title"] = actual
            c["journal"] = rec.get("source", c.get("journal"))
            year = (rec.get("pubdate") or "")[:4]
            if year.isdigit():
                c["year"] = int(year)

    if bad_pmid:
        print(f"✗ PMID 格式無效 {len(bad_pmid)} 筆：")
        for f, cid, _, c in bad_pmid[:10]:
            print(f"   {f} · {cid} · {c.get('title', '')[:60]}")

    if missing:
        print(f"\n✗ PubMed 查無此筆 {len(missing)} 個（極可能是捏造的）：")
        for f, cid, p, t in missing[:20]:
            print(f"   {f} · {cid} · PMID {p} · {t[:56]}")

    if mismatch:
        print(f"\n⚠ 標題與 PMID 不符 {len(mismatch)} 筆：")
        for _f, cid, p, claimed, actual in mismatch[:15]:
            print(f"   {cid} · PMID {p}")
            print(f"      宣稱: {claimed[:78]}")
            print(f"      實際: {actual[:78]}")

    ok = len(rows) - len(missing) - len(mismatch)
    if rows:
        print(f"\nPubMed 配對通過 {ok} / {len(rows)}（{ok / len(rows) * 100:.1f}%）")
    print(f"來源連結通過 {len(catalog_urls) - len(bad_urls)} / {len(catalog_urls)}")

    if fix:
        for path, blob in BLOBS.items():
            path.write_text(json.dumps(blob, ensure_ascii=False, indent=1))
        print(f"→ --fix：已用 PubMed 回傳值覆寫 {len(BLOBS)} 個檔案的 title/journal/year")

    return 1 if (missing or bad_pmid or bad_urls) else 0


if __name__ == "__main__":
    sys.exit(main())
