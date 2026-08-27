#!/usr/bin/env python3
"""PubMed E-utilities 查詢小工具。

實證查核時用來找文獻、確認 takeaway。PMID 一律從這裡取，不可憑記憶填寫。

用法：
  python3 src/build/pubmed.py search "<query>" [retmax]     # 回傳 PMID + 標題 + 期刊 + 年 + 類型
  python3 src/build/pubmed.py abs <PMID> [<PMID> ...]       # 回傳摘要
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _get(path: str, params: dict) -> str:
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as res:
                return res.read().decode()
        except Exception as exc:
            if attempt == 3:
                raise
            print(f"  retry {attempt + 1}: {exc}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    return ""


def search(query: str, retmax: int = 12) -> None:
    data = json.loads(
        _get(
            "esearch.fcgi",
            {
                "db": "pubmed",
                "retmode": "json",
                "term": query,
                "retmax": retmax,
                "sort": "relevance",
            },
        )
    )
    ids = data["esearchresult"]["idlist"]
    if not ids:
        print("(no hits)")
        return
    time.sleep(0.4)
    summ = json.loads(
        _get("esummary.fcgi", {"db": "pubmed", "retmode": "json", "id": ",".join(ids)})
    )["result"]
    for pmid in ids:
        r = summ.get(pmid, {})
        types = ",".join(t for t in r.get("pubtype", []) if t not in ("Journal Article",))
        year = (r.get("pubdate") or "")[:4]
        print(f"{pmid}\t{year}\t{r.get('source', '')}\t{types}\t{r.get('title', '')}")


def abstracts(pmids: list[str]) -> None:
    text = _get(
        "efetch.fcgi",
        {"db": "pubmed", "retmode": "xml", "rettype": "abstract", "id": ",".join(pmids)},
    )
    for chunk in text.split("<PubmedArticle>")[1:]:
        pmid = re.search(r"<PMID[^>]*>(\d+)</PMID>", chunk)
        title = re.search(r"<ArticleTitle[^>]*>(.*?)</ArticleTitle>", chunk, re.S)
        parts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", chunk, re.S)
        clean = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()  # noqa: E731
        print(f"### {pmid.group(1) if pmid else '?'} — {clean(title.group(1)) if title else ''}")
        print(clean(" ".join(parts))[:1800])
        print()


if __name__ == "__main__":
    if sys.argv[1] == "search":
        search(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 12)
    else:
        abstracts(sys.argv[2:])
