import json
import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from project_contract import validate_project


class V81ReleaseShapeTests(unittest.TestCase):
    def test_current_release_preserves_v81_gates(self):
        self.assertEqual(
            (SKILL_DIR / "VERSION").read_text(encoding="utf-8").strip(),
            "9.0.0",
        )

    def test_skill_closes_confirmation_gate_loopholes(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        for phrase in (
            "缺失不等于超出范围",
            "用户明确排除",
            "五个核心决策维度",
            "事实文案",
            "每页独特证据",
            "同一主要决策最多两页",
            "plan.md",
        ):
            self.assertIn(phrase, skill)

    def test_plan_template_exposes_claim_and_commercial_coverage_fields(self):
        plan = (SKILL_DIR / "templates" / "plan_template.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "decision dimension",
            "claim type",
            "evidence status",
            "approved for copy",
            "primary decision",
            "unique evidence",
            "商业完整度",
        ):
            self.assertIn(phrase, plan)

    def test_project_template_uses_v81_confirmation_contract(self):
        project = json.loads(
            (SKILL_DIR / "templates" / "project_template.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(project["schema_version"], "9.0")
        self.assertEqual(project["skill_version"], "9.0.0")
        self.assertEqual(project["plan_document"], "plan.md")
        self.assertEqual(validate_project(project), [])

    def test_example_project_uses_v81_confirmation_contract(self):
        project = json.loads(
            (SKILL_DIR / "examples" / "example_project.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(project["schema_version"], "9.0")
        self.assertEqual(validate_project(project), [])

    def test_evals_cover_jd_earbud_confirmation_gate_regression(self):
        corpus = (SKILL_DIR / "evals" / "evals.json").read_text(encoding="utf-8")

        for phrase in (
            "300mAh",
            "45小时",
            "140小时",
            "out_of_scope",
            "重复场景页",
            "用户可读的详细方案",
        ):
            self.assertIn(phrase, corpus)

    def test_jd_earbud_poor_output_is_frozen_as_immutable_fixture(self):
        project_path = (
            SKILL_DIR / "evals" / "fixtures" / "jd-earbuds-poor-project-v81.json"
        )
        project = json.loads(
            project_path.read_text(encoding="utf-8")
        )

        self.assertEqual(project["schema_version"], "8.1")
        self.assertEqual(project["status"], "review")
        self.assertEqual(
            sum(len(page["copy"]) == 2 for page in project["pages"]),
            7,
        )
        self.assertTrue(
            (SKILL_DIR / "evals" / "fixtures" / "jd-earbuds-poor-contact-sheet-v81.jpg").is_file()
        )

    def test_jd_fixture_reproduces_detail_pages_that_are_only_still_life(self):
        project = json.loads(
            (SKILL_DIR / "evals" / "fixtures" / "jd-earbuds-poor-project-v81.json").read_text(
                encoding="utf-8"
            )
        )
        detail_pages = [page for page in project["pages"] if page["surface"] == "detail"]

        self.assertEqual(len(detail_pages), 3)
        self.assertEqual(
            {page["role"] for page in detail_pages},
            {"commute_still_life", "travel_still_life", "home_lifestyle_closing"},
        )


if __name__ == "__main__":
    unittest.main()
