"""Shared workshop validation and accessible rendering; publication has a separate gate."""

import html
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]


def esc(value):
    return html.escape(str(value), quote=True)


def listing(items):
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def validate(package, root=ROOT, expected_status="draft"):
    if package["status"] != expected_status or package["clinical_approval"] is not None:
        raise ValueError("This renderer only accepts unapproved drafts")
    refs = {ref["id"]: ref for ref in package["sources"]}
    if len(refs) != len(package["sources"]):
        raise ValueError("Duplicate source ID")
    config = json.loads((root / "course/course.config.json").read_text())
    if package["site"] != config["site"]["project"]:
        raise ValueError("Site project mismatch")
    course = json.loads((root / "course/data/syllabus.json").read_text())
    prior = {u["id"] for chapter in course["chapters"] for u in chapter["units"]}
    ids = set()
    for ref in refs.values():
        if ref["url"] != f"https://pubmed.ncbi.nlm.nih.gov/{ref['pmid']}/":
            raise ValueError("Source PMID/URL mismatch")
    for unit in package["units"]:
        if unit["status"] != expected_status or not set(unit["prerequisite_units"]) <= prior:
            raise ValueError("Invalid unit status or prerequisite")
        for field in (
            "source_ids",
            "objectives",
            "required_views",
            "interpretation_steps",
            "pitfalls",
            "evidence_boundary",
            "reporting_template",
            "questions",
            "cases",
        ):
            if not unit[field]:
                raise ValueError(f"Empty {field}")
        if not set(unit["source_ids"]) <= refs.keys():
            raise ValueError("Unknown unit reference")
        for item in [unit, *unit["questions"], *unit["cases"]]:
            if item["id"] in ids:
                raise ValueError("Duplicate learning item ID")
            ids.add(item["id"])
            if not set(item["source_ids"]) <= refs.keys():
                raise ValueError("Unknown learning item reference")
        for question in unit["questions"]:
            if (
                len(question["options"]) < 3
                or sum(o["correct"] is True for o in question["options"]) != 1
            ):
                raise ValueError("Question must have one correct answer and at least three choices")
            if any(
                not o["rationale"].strip() or not o["text"].strip() for o in question["options"]
            ):
                raise ValueError("Missing option rationale")
        for case in unit["cases"]:
            if case["kind"] not in {"source_figure", "synthetic"} or not case["rubric"]:
                raise ValueError("Invalid case kind or missing rubric")
            if case["kind"] == "source_figure":
                url = urlparse(case["source_url"])
                if (
                    url.scheme != "https"
                    or url.netloc != "pmc.ncbi.nlm.nih.gov"
                    or not url.fragment
                    or case["source"] not in refs
                ):
                    raise ValueError("Invalid source figure URL")
            elif case["source_url"] or case["figure"]:
                raise ValueError("Synthetic case must not masquerade as a source figure")


def render(package, digest, base_url, *, root=ROOT, published=False):
    parsed = urlparse(base_url)
    if not (published and base_url == "") and (
        parsed.scheme not in {"http", "https"} or not parsed.netloc
    ):
        raise ValueError("Invalid course base URL")
    workshop_link = '<a href="/advanced/" class="workshop-home">工作坊目錄</a>' if published else ""
    label = "策展審閱通過" if published else "草稿"
    review_label = "策展審閱通過" if published else "待審閱"
    scope = package["scope"].replace("尚待臨床審閱，", "") if published else package["scope"]
    limitations = list(package["limitations"])
    if published:
        limitations = [item for item in limitations if "正式 build" not in item]
        limitations.append("本批已通過策展審閱；不代表臨床能力認證或第三方影片全片驗收。")
    state = "本批策展審閱通過；不代表個案醫療背書。" if published else "草稿，尚無臨床核准記錄。"
    footer = "策展審閱通過" if published else "尚待臨床審閱"
    counts = f"{len(package['units'])} 個進階單元 · {sum(len(u['questions']) for u in package['units'])} 題知識題 · {sum(len(u['cases']) for u in package['units'])} 個判讀與報告練習"
    refs = {ref["id"]: ref for ref in package["sources"]}
    course = json.loads((root / "course/data/syllabus.json").read_text())
    prior_names = {u["id"]: u["name"] for c in course["chapters"] for u in c["units"]}
    sections = []
    nav = []
    for number, unit in enumerate(package["units"], 1):
        uid = esc(unit["id"])
        nav.append(
            f'<a href="#{uid}" class="unit-link"><span>{number:02}</span>{esc(unit["title"])}</a>'
        )
        prereqs = " · ".join(
            f'<a href="{esc(base_url.rstrip("/"))}/?tab=course#{esc(prior)}">{esc(prior_names[prior])}</a>'
            for prior in unit["prerequisite_units"]
        )
        questions = []
        for index, question in enumerate(unit["questions"], 1):
            qid = esc(question["id"])
            options = "".join(
                f'<label><input type="radio" name="{qid}" value="{i}" required><span>{esc(option["text"])}</span></label>'
                for i, option in enumerate(question["options"])
            )
            questions.append(
                f'<form class="question" data-question="{qid}"><fieldset><legend>{index}. {esc(question["stem"])}</legend>{options}</fieldset><button type="submit">核對答案</button><div class="feedback" role="status" aria-live="polite"></div></form>'
            )
        cases = []
        for index, case in enumerate(unit["cases"], 1):
            cid = esc(case["id"])
            kind = (
                "原文圖例 · 開放素材練習"
                if case["kind"] == "source_figure"
                else "虛構文字情境 · 非真實病人影像"
            )
            link = (
                f'<a class="source-button" href="{esc(case["source_url"])}" target="_blank" rel="noopener noreferrer">開啟原文 {esc(case["figure"])}（新分頁） ↗</a>'
                if case["source_url"]
                else ""
            )
            cases.append(
                f'<section class="case"><p class="eyebrow">練習 {index} ／ {kind}</p><h4>{esc(case["prompt"])}</h4>{link}<p class="muted">{esc(case["verification"])}</p><label for="{cid}">先寫所見、鑑別與限制</label><textarea id="{cid}" data-case="{cid}" rows="5" placeholder="請勿填入病人姓名或可識別資料。"></textarea><p class="save-state" aria-live="polite"></p><details><summary>查看參考報告與自評重點</summary><p>{esc(case["sample_report"])}</p>{listing(case["rubric"])}<p class="muted">自評重點供比對，尚未驗證為能力評分工具。</p></details></section>'
            )
        unit_refs = "".join(
            f'<li><a href="{esc(refs[r]["url"])}" target="_blank" rel="noopener noreferrer">{esc(refs[r]["title"])}</a>（{esc(refs[r]["year"])}）</li>'
            for r in unit["source_ids"]
        )
        sections.append(f'''<article id="{uid}" class="unit" tabindex="-1">
        <p class="eyebrow">進階工作坊 {number:02} / {len(package["units"]):02} · {label}</p><h2>{esc(unit["title"])}</h2><p>先備單元：{prereqs}</p>
        <div class="study-grid"><section><h3>完成後應能做到</h3>{listing(unit["objectives"])}</section><section><h3>核對視圖與資料</h3>{listing(unit["required_views"])}</section></div>
        <h3>判讀步驟</h3><ol class="steps">{"".join(f"<li>{esc(s)}</li>" for s in unit["interpretation_steps"])}</ol>
        <aside class="caution"><h3>容易誤判的地方</h3>{listing(unit["pitfalls"])}<h3>證據能支持到哪裡</h3><p>{esc(unit["evidence_boundary"])}</p></aside>
        <h3>報告骨架</h3><p class="template">{esc(unit["reporting_template"])}</p>
        <h3>知識核對 · 每個選項都有解析</h3>{"".join(questions)}
        <h3>判讀與報告練習</h3>{"".join(cases)}
        <h3>本單元依據</h3><p class="muted">上述判讀架構、題目與解析依據下列來源；原文圖例另外連到指定面板。請一併閱讀證據限制。</p><ul class="references">{unit_refs}</ul>
        <a class="back-top" href="#workshop">返回工作坊目錄 ↑</a></article>''')
    sources = "".join(
        f'<li><p><a href="{esc(r["url"])}" target="_blank" rel="noopener noreferrer">{esc(r["title"])}</a></p><p>{esc(r["authors"])} {esc(r["year"])} · PMID {esc(r["pmid"])} · DOI {esc(r["doi"])}</p><p class="muted">首次出版：{esc(r["first_publication"])}；核對：{esc(r["verified_on"])}；{esc(r["verification_level"])}</p></li>'
        for r in package["sources"]
    )
    return f'''<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'"><title>{esc(package["title"])}｜{label}</title><link rel="stylesheet" href="review.css"><script src="review.js" defer></script></head>
    <body data-package="{digest}"><a class="skip" href="#workshop">跳至教材</a><header><a href="{esc(base_url)}/?tab=home">← 返回課程</a>{workshop_link}<span>進階判讀工作坊 · {review_label}</span><button id="print" type="button">列印教材</button></header>
    <main id="workshop"><div class="intro"><p class="eyebrow">READ · REASON · REPORT</p><h1>{esc(package["title"])}</h1><p>{esc(scope)}</p><p>{counts}</p><p class="muted">先閱讀與作答，再比對解析。練習筆記僅儲存在此瀏覽器；清除網站資料會移除筆記，請勿填寫病人可識別資料。</p><button id="reset" type="button">清除此版工作坊的作答</button><span id="storage-status" role="status"></span></div>
    <nav aria-label="進階單元">{"".join(nav)}</nav><noscript><p class="caution">JavaScript 未啟用，仍可閱讀全部教材與參考報告；知識題互動及筆記儲存需啟用 JavaScript。</p></noscript>
    {"".join(sections)}<details class="provenance"><summary>研究來源、核對範圍與版本</summary><p>{esc(package["research_method"])}</p>{listing(limitations)}<p>建立：{esc(package["created"])} · 狀態：{state}</p><p class="digest">教材 SHA-256：{digest}</p><ol class="references">{sources}</ol></details></main><footer>醫療專業教育 · {footer} · 不取代完整病史、理學檢查及正式影像判讀</footer></body></html>'''
