import json
import math
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class ReleaseShapeCompatibilityTests(unittest.TestCase):
    def test_version_is_v9(self):
        self.assertEqual((SKILL_DIR / "VERSION").read_text(encoding="utf-8").strip(), "9.0.0")

    def test_main_skill_is_a_thin_orchestrator(self):
        skill_lines = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").splitlines()

        self.assertLessEqual(len(skill_lines), 220)

    def test_skill_assigns_analysis_and_planning_to_active_codex_multimodal_model(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("多模态读图", skill)
        self.assertIn("设计整套视觉策略", skill)

    def test_plan_separates_ecommerce_delivery_placements(self):
        plan = (SKILL_DIR / "templates" / "plan_template.md").read_text(encoding="utf-8")
        platform = (SKILL_DIR / "references" / "platform_delivery.md").read_text(
            encoding="utf-8"
        )

        for surface in ("方形搜索首图/图库", "3:4 主图/导购图", "纵向详情模块"):
            self.assertIn(surface, plan)
        for surface in ("SKU 图", "详情模块", "内容封面或活动图"):
            self.assertIn(surface, platform)
        self.assertIn("placement_id", plan)
        self.assertIn("尺寸依据", plan)

    def test_confirmed_page_plan_is_the_generation_source_of_truth(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        plan = (SKILL_DIR / "templates" / "plan_template.md").read_text(encoding="utf-8")

        self.assertIn("确认后的数量、页面任务、事实、核心文案、商品身份和 placement 是生图依据", skill)
        self.assertIn("实质变化需更新方案并重新确认", plan)

    def test_plan_is_validated_before_user_confirmation(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("确认前专业度预审", skill)
        self.assertIn("--schema-only", skill)

    def test_full_set_cannot_hide_evidence_gaps_with_more_scene_pages(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        design = (SKILL_DIR / "references" / "ecommerce_design.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("不能用更多场景图填满", skill)
        self.assertIn("不能用场景页掩盖证据缺口", design)

    def test_openai_capability_reference_covers_prompting_and_image_evals(self):
        reference = (SKILL_DIR / "references" / "openai_image_capability.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("image-gen-models-prompting-guide", reference)
        self.assertIn("multimodal/image_evals", reference)
        self.assertIn("逐字文字", reference)
        self.assertIn("人工视觉复核", reference)

    def test_example_plan_uses_the_same_placement_vocabulary(self):
        example = (SKILL_DIR / "examples" / "example_plan.md").read_text(encoding="utf-8")

        self.assertIn("placement", example)
        self.assertIn("商品媒体方形图库", example)
        self.assertIn("店铺主题纵向详情模块", example)
        self.assertIn("2048×2048", example)
        self.assertIn("1536×2048", example)

    def test_full_set_example_is_not_an_unjustified_eight_square_template(self):
        example = json.loads(
            (SKILL_DIR / "examples" / "example_project.json").read_text(encoding="utf-8")
        )
        surfaces = {page.get("surface") for page in example["pages"]}
        ratios = set()
        for page in example["pages"]:
            width, height = map(int, page["size"].split("x"))
            divisor = math.gcd(width, height)
            ratios.add((width // divisor, height // divisor))

        self.assertTrue(example["target"]["full_set"])
        self.assertIn("search_main", surfaces)
        self.assertIn("detail", surfaces)
        self.assertGreaterEqual(len(ratios), 2)

    def test_full_set_example_declares_the_current_contract_version(self):
        example = json.loads(
            (SKILL_DIR / "examples" / "example_project.json").read_text(encoding="utf-8")
        )

        self.assertEqual(example["schema_version"], "9.0")
        self.assertEqual(example["skill_version"], "9.0.0")

    def test_full_set_example_has_platform_evidence_and_composition_types(self):
        example = json.loads(
            (SKILL_DIR / "examples" / "example_project.json").read_text(encoding="utf-8")
        )
        composition_types = {page.get("composition_type") for page in example["pages"]}

        self.assertTrue(
            any(item.get("kind") == "platform_delivery" for item in example["research"])
        )
        self.assertGreaterEqual(len(composition_types), 4)

    def test_skill_only_collects_decision_critical_missing_information(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("关键缺口", skill)
        self.assertIn("集中询问用户一次", skill)

    def test_skill_rejects_eight_square_as_a_cross_platform_default(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        platform = (SKILL_DIR / "references" / "platform_delivery.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("一个平台不是一种尺寸", skill)
        self.assertIn("一个平台通常同时存在", platform)
        self.assertIn("两种实际选定尺寸", platform)

    def test_skill_never_fakes_requested_pixels_with_external_resizing(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        platform = (SKILL_DIR / "references" / "platform_delivery.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("实际像素不合格", skill)
        self.assertIn("不能用脚本裁切、缩放、补边或重新排版", platform)

    def test_old_docs_and_contract_maze_are_removed(self):
        self.assertFalse((SKILL_DIR / "docs").exists())
        scripts = {path.name for path in (SKILL_DIR / "scripts").glob("*.py")}

        self.assertEqual(
            scripts,
            {
                "project_contract.py",
                "validate_project.py",
                "build_contact_sheet.py",
                "compile_prompts.py",
                "validate_skill_release.py",
            },
        )

    def test_retired_overlay_and_migration_entrypoints_are_absent(self):
        forbidden = {
            "render_text_overlay.py",
            "migrate_manifest_to_v3.py",
            "migrate_manifest_v1_to_v2.py",
            "migrate_manifest_v4_to_v5.py",
        }
        scripts = {path.name for path in (SKILL_DIR / "scripts").glob("*.py")}

        self.assertTrue(forbidden.isdisjoint(scripts))

    def test_progressive_disclosure_is_small_and_routed(self):
        references = sorted((SKILL_DIR / "references").glob("*.md"))

        self.assertGreaterEqual(len(references), 4)
        self.assertLessEqual(len(references), 7)

    def test_project_template_stays_lightweight(self):
        template_path = SKILL_DIR / "templates" / "project_template.json"
        self.assertTrue(template_path.is_file(), "missing v7 project template")
        if not template_path.is_file():
            return
        project = json.loads(template_path.read_text(encoding="utf-8"))

        self.assertLessEqual(len(project), 16)
        self.assertLessEqual(len(project["pages"][0]), 18)

    def test_project_template_demonstrates_surface_specific_ratios(self):
        project = json.loads(
            (SKILL_DIR / "templates" / "project_template.json").read_text(
                encoding="utf-8"
            )
        )
        surfaces = {page.get("surface") for page in project["pages"]}
        ratios = set()
        for page in project["pages"]:
            width, height = map(int, page["size"].split("x"))
            divisor = math.gcd(width, height)
            ratios.add((width // divisor, height // divisor))

        self.assertGreaterEqual(len(project["target"]["placements"]), 2)
        self.assertGreaterEqual(
            len({item["selected_size"] for item in project["target"]["placements"]}),
            2,
        )
        self.assertIn("search_main", surfaces)
        self.assertIn("detail", surfaces)
        self.assertGreaterEqual(len(ratios), 2)

    def test_only_four_user_facing_templates_remain(self):
        templates = {path.name for path in (SKILL_DIR / "templates").glob("*") if path.is_file()}

        self.assertEqual(
            templates,
            {
                "project_template.json",
                "plan_template.md",
                "prompt_template.md",
                "review_template.md",
            },
        )

    def test_cross_platform_evals_cover_ratio_strategy_boundaries(self):
        evals = json.loads(
            (SKILL_DIR / "evals" / "evals.json").read_text(encoding="utf-8")
        )["evals"]
        corpus = json.dumps(evals, ensure_ascii=False)

        self.assertIn("只做 Shopify 商品图库", corpus)
        self.assertIn("主图和详情图", corpus)
        self.assertIn("淘宝标准的电商图片", corpus)
        self.assertIn("多个图片落点", corpus)
        self.assertIn("1080x1440", corpus)
        self.assertIn("800x800", corpus)


if __name__ == "__main__":
    unittest.main()
