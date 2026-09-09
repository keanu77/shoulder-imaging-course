"""Publication must match the reviewed bytes and honor later withdrawals."""

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/build"))
SPEC = importlib.util.spec_from_file_location("advanced", ROOT / "src/build/advanced.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "course", self.root / "course")
        shutil.copytree(ROOT / "tools/advanced-review", self.root / "tools/advanced-review")
        self.path = self.root / "course/data/advanced-workshop.json"
        self.data = json.loads(self.path.read_text())

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        self.path.write_text(json.dumps(self.data))

    def test_approved_content_and_all_pages(self):
        result = MODULE.generate(self.root / "dist", self.root)
        self.assertEqual((len(result["units"]), result["questions"], result["cases"]), (3, 9, 6))
        for unit in self.data["units"]:
            page = self.root / "dist/advanced/units" / f'{unit["id"]}.html'
            self.assertIn(unit["title"], page.read_text())
            self.assertNotIn("尚待臨床審閱", page.read_text())

    def test_modified_claim_cannot_inherit_approval(self):
        self.data["units"][0]["interpretation_steps"][0] += " Changed."
        self.save()
        with self.assertRaises(ValueError):
            MODULE.read_approved(self.root)

    def test_changed_receipt_is_rejected(self):
        self.data["curation_approval"]["candidate_sha256"] = "0" * 64
        self.save()
        with self.assertRaises(ValueError):
            MODULE.read_approved(self.root)

    def test_changed_candidate_is_rejected(self):
        candidate = self.root / "course/research/2026-09-09-advanced/package.json"
        candidate.write_text(candidate.read_text() + " ")
        with self.assertRaises(ValueError):
            MODULE.read_approved(self.root)

    def test_withdrawn_unit_removes_old_page_and_its_exercises(self):
        MODULE.generate(self.root / "dist", self.root)
        unit = self.data["units"][0]
        unit["status"] = "withdrawn"
        self.save()
        result = MODULE.generate(self.root / "dist", self.root)
        self.assertEqual((len(result["units"]), result["questions"], result["cases"]), (2, 6, 4))
        self.assertFalse((self.root / "dist/advanced/units" / f'{unit["id"]}.html').exists())
        self.assertNotIn(unit["id"], (self.root / "dist/advanced/index.html").read_text())

    def test_withdrawn_question_and_case_are_not_published(self):
        self.data["units"][0]["questions"][0]["status"] = "withdrawn"
        self.data["units"][0]["cases"][0]["status"] = "draft"
        self.save()
        result = MODULE.generate(self.root / "dist", self.root)
        self.assertEqual((result["questions"], result["cases"]), (8, 5))

    def test_withdrawn_package_cleans_generated_directory(self):
        MODULE.generate(self.root / "dist", self.root)
        self.data["status"] = "withdrawn"
        self.save()
        self.assertIsNone(MODULE.generate(self.root / "dist", self.root))
        self.assertFalse((self.root / "dist/advanced").exists())

    def test_absent_package_cleans_generated_directory(self):
        MODULE.generate(self.root / "dist", self.root)
        self.path.unlink()
        self.assertIsNone(MODULE.generate(self.root / "dist", self.root))
        self.assertFalse((self.root / "dist/advanced").exists())


if __name__ == "__main__":
    unittest.main()
