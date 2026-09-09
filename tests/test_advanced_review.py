"""Guard the boundary between unapproved learning material and deployment."""

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("advanced", ROOT / "tools/build_advanced_review.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AdvancedReviewTests(unittest.TestCase):
    def setUp(self):
        self.package = json.loads(MODULE.DEFAULT_PACKAGE.read_text())

    def test_valid_package(self):
        MODULE.validate(self.package)

    def test_approved_package_is_rejected(self):
        self.package["status"] = "approved"
        with self.assertRaises(ValueError):
            MODULE.validate(self.package)

    def test_approval_record_is_rejected(self):
        self.package["clinical_approval"] = {"reviewed_by": "fixture"}
        with self.assertRaises(ValueError):
            MODULE.validate(self.package)

    def test_site_mismatch_is_rejected(self):
        self.package["site"] = "different-course"
        with self.assertRaises(ValueError):
            MODULE.validate(self.package)

    def test_unknown_prerequisite_is_rejected(self):
        self.package["units"][0]["prerequisite_units"] = ["missing-unit"]
        with self.assertRaises(ValueError):
            MODULE.validate(self.package)

    def test_unknown_reference_is_rejected(self):
        self.package["units"][0]["source_ids"] = ["missing-source"]
        with self.assertRaises(ValueError):
            MODULE.validate(self.package)

    def test_multiple_answers_are_rejected(self):
        for option in self.package["units"][0]["questions"][0]["options"]:
            option["correct"] = True
        with self.assertRaises(ValueError):
            MODULE.validate(self.package)

    def test_missing_rationale_is_rejected(self):
        self.package["units"][0]["questions"][0]["options"][0]["rationale"] = ""
        with self.assertRaises(ValueError):
            MODULE.validate(self.package)

    def test_duplicate_ids_are_rejected(self):
        self.package["units"].append(copy.deepcopy(self.package["units"][0]))
        with self.assertRaises(ValueError):
            MODULE.validate(self.package)

    def test_synthetic_case_cannot_claim_source_figure(self):
        case = next(
            c for u in self.package["units"] for c in u["cases"] if c["kind"] == "synthetic"
        )
        case["source_url"] = "https://example.com"
        with self.assertRaises(ValueError):
            MODULE.validate(self.package)

    def test_figure_requires_safe_original_url(self):
        case = next(
            c for u in self.package["units"] for c in u["cases"] if c["kind"] == "source_figure"
        )
        case["source_url"] = "javascript:alert(1)"
        with self.assertRaises(ValueError):
            MODULE.validate(self.package)

    def test_output_rejects_deployment_directories(self):
        for directory in ("dist", "public", "src", "course", ".git"):
            with self.subTest(directory=directory), self.assertRaises(ValueError):
                MODULE.output_path(ROOT / directory / "review")

    def test_output_resolves_symlink_before_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            (path / "public").mkdir()
            (path / "harmless-name").symlink_to(path / "public", target_is_directory=True)
            with self.assertRaises(ValueError):
                MODULE.output_path(path / "harmless-name" / "review")

    def test_render_escapes_content(self):
        self.package["units"][0]["title"] = '<img src=x onerror="alert(1)">'
        document = MODULE.render(self.package, "test-digest", "http://127.0.0.1:8913")
        self.assertNotIn("<img src=x", document)
        self.assertIn("&lt;img", document)
        self.assertIn('content="noindex,nofollow"', document)


if __name__ == "__main__":
    unittest.main()
