"""Validate and render the draft workshop outside deployment output."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "course/research/2026-09-09-advanced/package.json"
SPEC = importlib.util.spec_from_file_location("workshop_render", ROOT / "src/build/workshop.py")
SHARED = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SHARED)


def validate(package, root=ROOT):
    SHARED.validate(package, root, expected_status="draft")


def render(package, digest, base_url):
    return SHARED.render(package, digest, base_url, root=ROOT)


def output_path(path):
    resolved = path.resolve()
    if any(part in {"dist", "public", "src", "course", ".git"} for part in resolved.parts):
        raise ValueError("Review output cannot enter deployment/source directories")
    if resolved == ROOT or resolved == Path.home() or resolved == Path("/"):
        raise ValueError("Choose a dedicated preview directory")
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()
    raw = args.package.read_bytes()
    package = json.loads(raw)
    validate(package)
    dest = output_path(args.output)
    digest = hashlib.sha256(raw).hexdigest()
    document = render(package, digest, args.base_url)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "index.html").write_text(document)
    for filename in ("review.css", "review.js"):
        (dest / filename).write_bytes((ROOT / "tools/advanced-review" / filename).read_bytes())
    (dest / "questions.json").write_text(
        json.dumps(
            {q["id"]: q for u in package["units"] for q in u["questions"]}, ensure_ascii=False
        )
    )
    (dest / "manifest.json").write_text(
        json.dumps(
            {
                "status": "draft",
                "package_sha256": digest,
                "units": len(package["units"]),
                "questions": sum(len(u["questions"]) for u in package["units"]),
                "cases": sum(len(u["cases"]) for u in package["units"]),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Draft only → {dest} · SHA-256 {digest}")


if __name__ == "__main__":
    main()
