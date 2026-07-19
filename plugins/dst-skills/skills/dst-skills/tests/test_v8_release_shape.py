import json
import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from project_contract import validate_project


class V80ReleaseShapeTests(unittest.TestCase):
    def test_release_version_is_v81(self):
        self.assertEqual((SKILL_DIR / "VERSION").read_text(encoding="utf-8").strip(), "8.2.0")

    def test_skill_defines_visual_director_role_and_pre_confirmation_gates(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        for phrase in (
            "电商视觉策略总监",
            "商品身份审核",
            "素材诊断",
            "买家决策地图",
            "一个平台不是一种尺寸",
            "placement",
            "draft",
            "确认前专业度预审",
        ):
            self.assertIn(phrase, skill)

    def test_platform_reference_models_multiple_real_placements(self):
        platform = (SKILL_DIR / "references" / "platform_delivery.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("平台不是一种尺寸", platform)
        self.assertIn("placement", platform)
        self.assertIn("方形", platform)
        self.assertIn("3:4", platform)
        self.assertIn("详情", platform)

    def test_image_reference_records_gpt_image_2_size_constraints(self):
        reference = (SKILL_DIR / "references" / "openai_image_capability.md").read_text(
            encoding="utf-8"
        )

        for phrase in ("16 的倍数", "3840", "8,294,400", "655,360"):
            self.assertIn(phrase, reference)

    def test_plan_template_contains_diagnosis_strategy_decisions_and_placements(self):
        plan = (SKILL_DIR / "templates" / "plan_template.md").read_text(encoding="utf-8")

        for phrase in (
            "素材诊断",
            "商品身份锁定",
            "定位与创意总纲",
            "买家决策地图",
            "平台图片落点与规格",
            "placement_id",
        ):
            self.assertIn(phrase, plan)

    def test_current_project_template_is_confirmation_ready(self):
        project = json.loads(
            (SKILL_DIR / "templates" / "project_template.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(project["schema_version"], "8.2")
        self.assertEqual(project["skill_version"], "8.2.0")
        self.assertGreaterEqual(len(project["target"]["placements"]), 2)
        self.assertGreaterEqual(len(project["decision_map"]), 5)
        self.assertTrue(project["product"]["identity_lock"])
        self.assertTrue(project["product"]["source_diagnosis"])
        self.assertTrue(project["product"]["design_opportunities"])
        self.assertTrue(all(page["placement_id"] for page in project["pages"]))
        self.assertTrue(all(page["decision_ids"] for page in project["pages"]))
        self.assertEqual(validate_project(project), [])

    def test_example_project_uses_current_strategy_contract(self):
        example = json.loads(
            (SKILL_DIR / "examples" / "example_project.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(example["schema_version"], "8.2")
        self.assertEqual(validate_project(example), [])

    def test_evals_cover_single_image_diagnosis_and_multi_spec_platforms(self):
        evals = json.loads(
            (SKILL_DIR / "evals" / "evals.json").read_text(encoding="utf-8")
        )
        corpus = json.dumps(evals, ensure_ascii=False)

        self.assertIn("黑色外框", corpus)
        self.assertIn("前景单椅", corpus)
        self.assertIn("多个图片落点", corpus)
        self.assertIn("1080x1440", corpus)

    def test_release_checker_separates_static_and_full_verification(self):
        checker = (SKILL_DIR / "scripts" / "validate_skill_release.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("--full", checker)
        self.assertIn("SKILL STATIC CHECK OK", checker)
        self.assertIn("SKILL FULL RELEASE CHECK OK", checker)
        self.assertIn("unittest", checker)


if __name__ == "__main__":
    unittest.main()
