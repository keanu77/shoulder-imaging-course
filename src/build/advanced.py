"""Publish only digest-bound, approved workshop content; preserve reviewed candidates."""

import copy
import hashlib
import json
import shutil
from pathlib import Path

from workshop import render, validate

ROOT = Path(__file__).resolve().parents[2]


def read_approved(root=ROOT):
    path = root / "course/data/advanced-workshop.json"
    if not path.exists():
        return None
    package = json.loads(path.read_text())
    receipt = json.loads((root / "course/research/2026-09-09-advanced/approval.json").read_text())
    candidate = root / "course/research/2026-09-09-advanced/package.json"
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if receipt["candidate_path"] != candidate.relative_to(root).as_posix():
        raise ValueError("Unexpected candidate path")
    if receipt["candidate_sha256"] != digest or package.get("curation_approval") != receipt:
        raise ValueError("Approval digest or receipt mismatch")
    draft = json.loads(candidate.read_text())
    validate(draft, root)
    if receipt["site"] != draft["site"] or receipt["unit_ids"] != [u["id"] for u in draft["units"]]:
        raise ValueError("Approval scope mismatch")
    expected = copy.deepcopy(draft)
    expected["status"] = "approved"
    expected["curation_approval"] = receipt
    for unit in expected["units"]:
        for item in [unit, *unit["questions"], *unit["cases"]]:
            item.update(status="approved", approval_digest=digest)
    normalized = copy.deepcopy(package)
    for item in [
        normalized,
        *(i for u in normalized["units"] for i in [u, *u["questions"], *u["cases"]]),
    ]:
        if item.get("status") not in {"approved", "draft", "withdrawn"}:
            raise ValueError("Invalid review status")
        item["status"] = "approved"
    if normalized != expected:
        raise ValueError("Approved content differs from the reviewed candidate")
    if receipt["decision"] != "approved" or package["status"] != "approved":
        return None
    package["units"] = [u for u in package["units"] if u["status"] == "approved"]
    for unit in package["units"]:
        unit["questions"] = [q for q in unit["questions"] if q["status"] == "approved"]
        unit["cases"] = [c for c in unit["cases"] if c["status"] == "approved"]
    return package if package["units"] else None


def generate(dist, root=ROOT):
    out = dist / "advanced"
    if out.is_symlink():
        raise ValueError("Refusing a symlink in generated workshop output")
    if out.exists():
        shutil.rmtree(out)
    package = read_approved(root)
    if not package:
        return None
    digest = package["curation_approval"]["candidate_sha256"]
    questions = {q["id"]: q for u in package["units"] for q in u["questions"]}
    questions_raw = json.dumps(questions, ensure_ascii=False).encode()
    question_file = f"questions.{hashlib.sha256(questions_raw).hexdigest()[:12]}.json"
    out.mkdir(parents=True)
    (out / question_file).write_bytes(questions_raw)
    assets = {}
    for ext in ("css", "js"):
        raw = (root / f"tools/advanced-review/review.{ext}").read_bytes()
        name = f"workshop.{hashlib.sha256(raw).hexdigest()[:12]}.{ext}"
        (out / name).write_bytes(raw)
        assets[ext] = name

    def document(data, prefix):
        doc = render(data, digest, "", root=root, published=True)
        doc = doc.replace('<html lang="zh-Hant-TW">', '<html lang="zh-Hant-TW" data-theme="dark">')
        doc = doc.replace('</head>', f'<script src="{prefix}../js/theme.js"></script></head>')
        doc = doc.replace('<header>', '<a class="HubReturn" href="https://imaging-course-hub.sportsmedicine.tw/" aria-label="返回運動醫學影像學習站首頁"><span aria-hidden="true">←</span> 學習站首頁</a><header>', 1)
        doc = doc.replace('href="review.css"', f'href="{prefix}{assets["css"]}"')
        doc = doc.replace(
            'src="review.js"', f'src="{prefix}{assets["js"]}" data-questions="{question_file}"'
        )
        return doc.replace('content="noindex,nofollow"', 'content="noindex,follow"')

    (out / "index.html").write_text(document(package, ""))
    (out / "units").mkdir()
    for unit in package["units"]:
        subset = {**package, "units": [unit]}
        (out / "units" / f"{unit['id']}.html").write_text(document(subset, "../"))
    summary = {
        "status": "approved",
        "package_sha256": digest,
        "url": f"advanced/?v={digest[:12]}",
        "questions": len(questions),
        "cases": sum(len(u["cases"]) for u in package["units"]),
        "units": [
            {
                "id": u["id"],
                "title": u["title"],
                "prerequisite_units": u["prerequisite_units"],
                "summary": u["objectives"][0],
                "url": f"advanced/units/{u['id']}.html?v={digest[:12]}",
                "workshop_url": f"advanced/?v={digest[:12]}#{u['id']}",
            }
            for u in package["units"]
        ],
    }
    (out / "manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(
        f"   Approved workshop: {len(package['units'])} units / {len(questions)} questions / {summary['cases']} exercises"
    )
    return summary
