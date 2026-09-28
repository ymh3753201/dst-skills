import json
import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from project_contract import validate_project


class V82ReleaseShapeTests(unittest.TestCase):
    def test_release_version_is_v9(self):
        self.assertEqual(
            (SKILL_DIR / "VERSION").read_text(encoding="utf-8").strip(),
            "9.0.0",
        )

    def test_skill_explains_safe_copy_prompt_compilation_and_integrity_gates(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        for phrase in (
            "缺参数不等于缺文案",
            "safe_commercial",
            "blocking_scope",
            "compile_prompts.py",
            "plan_sha256",
            "copy_richness",
            "product_multiplicity",
            "纯买前核对/风险清单页默认最多一张",
        ):
            self.assertIn(phrase, skill)

    def test_prompt_reference_defines_structured_copy_and_six_sections(self):
        prompting = (SKILL_DIR / "references" / "prompting.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "headline",
            "subheadline",
            "supporting_points",
            "safe_commercial",
            "【页面任务】",
            "【商品身份】",
            "【构图蓝图】",
            "【文案系统】",
            "【视觉执行】",
            "【负面约束】",
        ):
            self.assertIn(phrase, prompting)

    def test_project_template_uses_v82_commercial_execution_contract(self):
        project = json.loads(
            (SKILL_DIR / "templates" / "project_template.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(project["schema_version"], "9.0")
        self.assertEqual(project["skill_version"], "9.0.0")
        self.assertEqual(validate_project(project), [])

    def test_example_project_uses_v82_contract(self):
        project = json.loads(
            (SKILL_DIR / "examples" / "example_project.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(project["schema_version"], "9.0")
        self.assertEqual(validate_project(project), [])

    def test_evals_cover_sparse_copy_prompt_and_review_regressions(self):
        evals = json.loads(
            (SKILL_DIR / "evals" / "evals.json").read_text(encoding="utf-8")
        )["evals"]
        corpus = json.dumps(evals, ensure_ascii=False)

        self.assertGreaterEqual(len(evals), 37)
        for phrase in (
            "缺少商品参数",
            "安全商业文案",
            "两行大字",
            "事后补写确认",
            "自己填写 pass",
        ):
            self.assertIn(phrase, corpus)


if __name__ == "__main__":
    unittest.main()
