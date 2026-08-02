#!/usr/bin/env python3
"""由 public/course.json 產生 SEO 資產。

- 把 Course JSON-LD 注入 index.html 的 <script id="schema">
- 產生 sitemap.xml / robots.txt / llms.txt

數字全部取自 course.json，不手寫，避免結構化資料與實際內容對不上。
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COURSE = Path(os.environ.get("COURSE") or ROOT / "course").resolve()
PUB = Path(os.environ.get("DIST") or ROOT / "dist").resolve()

CFG = json.loads((COURSE / "course.config.json").read_text())
SITE_CFG = CFG["site"]
SITE = SITE_CFG["url"].rstrip("/")
NAME = SITE_CFG["name"]
TITLE = SITE_CFG["title"]
DESC = SITE_CFG["description"]
LOCALE = SITE_CFG.get("locale", "zh-Hant")
ALLOW_INDEXING = CFG.get("medical", {}).get("allowIndexing", False)


def iso_duration(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    return f"PT{h}H{rem // 60}M"


def build_schema(course: dict) -> dict:
    meta = course["meta"]
    chapters = course["chapters"]

    teaches = [u["name"] for ch in chapters for u in ch["units"]]

    syllabus = [
        {
            "@type": "Syllabus",
            "position": i,
            "name": f"{ch['code']} {ch['title']}",
            "description": (
                f"{len(ch['units'])} 個單元"
                + (
                    f"：{'、'.join(u['name'] for u in ch['units'])}"
                    if len(ch["units"]) <= 4
                    else ""
                )
                + (
                    f"，附 {sum(len(u.get('drills') or []) for u in ch['units'])} 支精選影片"
                    if any(u.get("drills") for u in ch["units"])
                    else ""
                )
            ),
        }
        for i, ch in enumerate(chapters, 1)
    ]

    # 立場聲明的引用，讓機器也讀得到這門課的實證基礎
    citations = []
    for s in course.get("stance", []):
        for c in s.get("citations", [])[:3]:
            if c.get("url"):
                citations.append(
                    {
                        "@type": "CreativeWork",
                        "name": c.get("title", ""),
                        "url": c["url"],
                        **({"datePublished": str(c["year"])} if c.get("year") else {}),
                    }
                )

    org = {
        "@type": "Organization",
        "@id": f"{SITE}/#org",
        "name": NAME,
        "url": f"{SITE}/",
    }

    return {
        "@context": "https://schema.org",
        "@graph": [
            org,
            {
                "@type": "WebSite",
                "@id": f"{SITE}/#website",
                "url": f"{SITE}/",
                "name": NAME,
                "description": DESC,
                "inLanguage": LOCALE,
                "publisher": {"@id": f"{SITE}/#org"},
            },
            {
                "@type": "Course",
                "@id": f"{SITE}/#course",
                "url": f"{SITE}/",
                "name": TITLE,
                "description": DESC,
                "image": f"{SITE}/og.png",
                "inLanguage": LOCALE,
                "isAccessibleForFree": True,
                "isFamilyFriendly": True,
                "provider": {"@id": f"{SITE}/#org"},
                "educationalLevel": "Professional",
                "learningResourceType": SITE_CFG.get("learningResourceType", []),
                "timeRequired": iso_duration(meta["duration_seconds"]),
                "teaches": teaches,
                "about": [{"@type": "Thing", "name": x} for x in SITE_CFG.get("about", [])],
                "audience": {
                    "@type": "Audience",
                    "audienceType": SITE_CFG.get("audience", ""),
                },
                "hasCourseInstance": {
                    "@type": "CourseInstance",
                    "courseMode": "online",
                    "courseWorkload": iso_duration(meta["duration_seconds"]),
                    "inLanguage": LOCALE,
                    "isAccessibleForFree": True,
                    "location": {"@type": "VirtualLocation", "url": f"{SITE}/"},
                },
                "syllabusSections": syllabus,
                "numberOfLessons": meta["units"],
                **({"citation": citations} if citations else {}),
            },
        ],
    }


def render_template(meta: dict) -> None:
    """把 {{a.b}} 換成課程設定裡的值。

    文案在 build 時就寫進 HTML，而不是等 JS 跑完才填——首屏就有真實內容，
    對搜尋引擎與未執行 JS 的爬蟲都友善。
    """
    path = PUB / "index.html"
    html = path.read_text()

    def lookup(dotted: str):
        node = CFG
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    def sub(m):
        val = lookup(m.group(1))
        if val is None:
            return m.group(0)
        return str(val).replace("{units}", str(meta["units"])).replace(
            "{problems}", str(meta.get("problem_units", 0))
        )

    html, n = re.subn(r"\{\{([\w.]+)\}\}", sub, html)
    path.write_text(html)
    left = re.findall(r"\{\{[\w.]+\}\}", html)
    print(f"   index.html  文案注入 {n} 處" + (f"，未解析 {left}" if left else ""))


def inject_schema(schema: dict) -> None:
    """把 JSON-LD 寫進 index.html 的佔位 script。"""
    path = PUB / "index.html"
    html = path.read_text()
    # JSON 內出現 </script> 會提前結束標籤，必須跳脫
    payload = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    new, n = re.subn(
        r'(<script type="application/ld\+json" id="schema">).*?(</script>)',
        lambda m: m.group(1) + payload + m.group(2),
        html,
        flags=re.S,
    )
    if n != 1:
        print("✗ index.html 找不到 JSON-LD 佔位 script", file=sys.stderr)
        sys.exit(1)
    path.write_text(new)
    print(f"   index.html  JSON-LD 已注入（{len(payload) / 1024:.1f} KB）")


HEAD_TAGS = """    <link rel="canonical" href="{site}/" />
    <meta name="robots" content="{robots}" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="{name}" />
    <meta property="og:locale" content="{oglocale}" />
    <meta property="og:url" content="{site}/" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{ogdesc}" />
    <meta property="og:image" content="{site}/og.png" />
    <meta property="og:image:type" content="image/png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{title}" />
    <meta name="twitter:description" content="{ogdesc}" />
    <meta name="twitter:image" content="{site}/og.png" />
    <meta name="description" content="{desc}" />
"""


def inject_meta(course: dict) -> None:
    """用設定重建 head 裡的 SEO 標籤，取代模板中的佔位區塊。"""
    path = PUB / "index.html"
    html = path.read_text()
    block = HEAD_TAGS.format(
        site=SITE,
        robots=(
            "index, follow, max-image-preview:large, max-snippet:-1"
            if ALLOW_INDEXING
            else "noindex, follow"
        ),
        name=NAME,
        title=TITLE,
        desc=DESC,
        ogdesc=SITE_CFG.get("ogDescription", DESC),
        oglocale=SITE_CFG.get("ogLocale", "zh_TW"),
    )
    html, n = re.subn(
        r"<!-- seo:start -->.*?<!-- seo:end -->",
        lambda _: f"<!-- seo:start -->\n{block}    <!-- seo:end -->",
        html,
        flags=re.S,
    )
    path.write_text(html)
    print(f"   index.html  SEO 標籤{'已注入' if n else '找不到佔位區塊'}")


def write_indexing_header() -> None:
    """審閱站以 HTTP header 再加一道 noindex；核准後建置會自動移除。"""
    path = PUB / "_headers"
    if ALLOW_INDEXING or not path.exists():
        return
    text = path.read_text()
    text = text.replace("/*\n", "/*\n  X-Robots-Tag: noindex, follow\n", 1)
    path.write_text(text)
    print("   _headers  X-Robots-Tag=noindex（medical-review gate）")


def write_sitemap() -> None:
    (PUB / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
        "  <url>\n"
        f"    <loc>{SITE}/</loc>\n"
        f"    <lastmod>{date.today().isoformat()}</lastmod>\n"
        "    <changefreq>monthly</changefreq>\n"
        "    <priority>1.0</priority>\n"
        "    <image:image>\n"
        f"      <image:loc>{SITE}/og.png</image:loc>\n"
        f"      <image:title>{NAME}</image:title>\n"
        "    </image:image>\n"
        "  </url>\n"
        "</urlset>\n"
    )
    print("   sitemap.xml")


AI_CRAWLERS = ("GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended")


def write_robots() -> None:
    """一般搜尋引擎放行＋noindex；AI 檢索器依醫療審查閘門切換。

    搜尋引擎不用 Disallow：擋掉抓取會讓爬蟲讀不到 noindex，反而可能留下
    URL-only 索引。但 noindex 管不到 AI 語料擷取，所以簽核前另行封鎖 AI 檢索器。
    """
    if ALLOW_INDEXING:
        rule = "Allow: /"
        note = "# AI 檢索器放行 —— 這門課的實證註記正是希望被引用到的內容"
    else:
        rule = "Disallow: /"
        note = (
            "# 醫療審查閘門：單元尚未經醫師簽核，AI 檢索器一律擋下。\n"
            "# 搜尋引擎維持 Allow + noindex（擋抓取會讀不到 noindex，"
            "反而可能留下 URL-only 索引）；\n"
            "# 但 noindex 管不到語料擷取，故 AI 檢索器另行封鎖。"
        )
    blocks = "\n\n".join(f"User-agent: {agent}\n{rule}" for agent in AI_CRAWLERS)
    (PUB / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"{note}\n"
        f"{blocks}\n"
        "\n"
        f"Sitemap: {SITE}/sitemap.xml\n"
    )
    state = "放行" if ALLOW_INDEXING else "封鎖"
    print(f"   robots.txt  AI 檢索器={state}（medical-review gate）")


def write_llms(course: dict) -> None:
    meta, chapters = course["meta"], course["chapters"]
    llm = CFG.get("llms", {})
    lines = [
        f"# {NAME}",
        "",
        f"> {DESC}",
        "",
        llm.get("summary", "").format(
            units=meta.get("lesson_units", 0),
            problems=meta.get("problem_units", 0),
            evidence=meta.get("evidence_checked", 0),
        )
        + f" 共 {meta['units']} 個教學單元，搭配 {meta['drill_units']} 支精選影片，"
        f"影片總長 {meta['duration']}。",
        "",
        f"## {CFG.get('stance', {}).get('title', '立場')}（重要）",
        "",
        llm.get("stanceIntro", "").format(
            evidence=meta.get("evidence_checked", 0), problems=meta.get("problem_units", 0)
        ),
        "",
    ]
    for s in course.get("stance", []):
        lines.append(f"- **{s['name']}**（{s['evidence_grade']}）：{s.get('summary', '')[:180]}…")
    lines += [
        "",
        llm.get("stanceConclusion", ""),
        "",
        "## 章節",
        "",
    ]
    for ch in chapters:
        names = "、".join(u["name"] for u in ch["units"])
        lines.append(f"- **{ch['code']} {ch['title']}**：{names}")
    lines += [
        "",
        "## 免責",
        "",
        llm.get("disclaimer", ""),
        "",
        f"完整內容：{SITE}/",
        "",
    ]
    (PUB / "llms.txt").write_text("\n".join(lines))
    print("   llms.txt")


def main() -> int:
    course_path = PUB / "course.json"
    if not course_path.exists():
        print("✗ 找不到 public/course.json，請先執行 build.py", file=sys.stderr)
        return 1

    course = json.loads(course_path.read_text())
    print("SEO 資產：")
    render_template(course["meta"])
    inject_meta(course)
    inject_schema(build_schema(course))
    write_sitemap()
    write_robots()
    write_llms(course)
    write_indexing_header()
    return 0


if __name__ == "__main__":
    sys.exit(main())
