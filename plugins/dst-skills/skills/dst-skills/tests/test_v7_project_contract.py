import copy
import importlib.util
import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SKILL_DIR = Path(__file__).resolve().parents[1]
CONTRACT_PATH = SKILL_DIR / "scripts" / "project_contract.py"


def load_contract_module():
    spec = importlib.util.spec_from_file_location("dst_v7_project_contract", CONTRACT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def planned_project():
    return {
        "schema_version": "7.1",
        "skill_version": "7.1.0",
        "status": "planned",
        "product": {
            "name": "便携咖啡机",
            "category": "小家电",
            "identity_summary": "黑色圆柱机身，顶部按键，侧面水仓",
        },
        "target": {
            "platform": "shopify",
            "market": "CN",
            "use": "商品详情页",
            "full_set": False,
            "mode": "standard",
            "ratio_strategy": "single_surface",
            "ratio_basis": "用户当前只要求一个商品图库页面",
        },
        "source_assets": [
            {"id": "asset-front", "file": "source/front.png", "sha256": "a" * 64}
        ],
        "facts": [
            {
                "id": "fact-pressure",
                "text": "15Bar 泵压",
                "source": "user",
                "source_ref": "用户说明",
            }
        ],
        "research": [],
        "visual_direction": {
            "style": "温暖、精致、真实使用感",
            "palette": ["#F2E7D5", "#1B1B1B"],
            "typography": "现代中文无衬线，清晰但不做 PPT 卡片",
            "consistency_rules": ["保持黑色机身、按键、水仓位置一致"],
        },
        "pages": [
            {
                "id": "page-01",
                "surface": "gallery",
                "role": "benefit",
                "buyer_question": "它能否快速制作浓缩咖啡？",
                "size": "1024x1024",
                "references": ["asset-front"],
                "fact_ids": ["fact-pressure"],
                "copy": ["15Bar 泵压", "随时享用浓缩咖啡"],
                "visual_brief": "晨间厨房实景，商品为绝对主角，文案与蒸汽和光线自然融合",
                "prompt": "生成完整的正方形电商成图。晨间厨房实景，商品为绝对主角，保持参考图结构。原生绘制中文标题“15Bar 泵压”和副标题“随时享用浓缩咖啡”，文字与蒸汽和光线自然融合，不要留白框，不要模板卡片。",
                "output": "",
            }
        ],
        "confirmation": {"status": "pending", "confirmed_at": "", "method": ""},
        "generation_log": [],
        "review": {
            "status": "planned",
            "reviewer_type": "",
            "contact_sheet": "",
            "contact_sheet_sha256": "",
            "pages": [],
        },
    }


def generation_record(output_sha256):
    return {
        "page_id": "page-01",
        "tool": "codex_image_gen",
        "model": "gpt-image-2",
        "request_id": "req-001",
        "generated_at": "2026-07-15T10:00:00+08:00",
        "prompt": planned_project()["pages"][0]["prompt"],
        "source_asset_ids": ["asset-front"],
        "output": "images/page-01.png",
        "output_sha256": output_sha256,
        "post_processing": [],
    }


class V7ProjectContractTests(unittest.TestCase):
    def test_single_project_contract_entrypoint_exists(self):
        self.assertTrue(
            CONTRACT_PATH.is_file(),
            "v7 should expose one lightweight project_contract.py entrypoint",
        )

    def test_project_contract_exposes_one_validator(self):
        module = load_contract_module()

        self.assertTrue(
            callable(getattr(module, "validate_project", None)),
            "project_contract.py should expose validate_project(project, project_dir)",
        )

    def test_full_set_requires_at_least_eight_dynamic_pages(self):
        project = planned_project()
        project["target"]["full_set"] = True

        errors = load_contract_module().validate_project(project)

        self.assertIn("full-set-requires-at-least-8-pages", errors)

    def test_schema_and_skill_versions_are_current(self):
        project = planned_project()
        project["schema_version"] = "6.0"

        errors = load_contract_module().validate_project(project)

        self.assertIn("unsupported-schema-version", errors)

    def test_generation_cannot_start_before_one_confirmation(self):
        project = planned_project()
        project["status"] = "generating"

        errors = load_contract_module().validate_project(project)

        self.assertIn("generation-requires-confirmed-plan", errors)

    def test_page_ids_must_be_unique(self):
        project = planned_project()
        project["pages"].append(dict(project["pages"][0]))

        errors = load_contract_module().validate_project(project)

        self.assertIn("duplicate-page-id:page-01", errors)

    def test_every_page_keeps_the_ten_field_prompt_contract(self):
        project = planned_project()
        project["pages"][0].pop("visual_brief")

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:missing-page-field:visual_brief", errors)

    def test_v71_page_contract_requires_delivery_surface(self):
        project = planned_project()
        project["pages"][0].pop("surface")

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:missing-page-field:surface", errors)

    def test_v71_mixed_full_set_rejects_eight_uniform_square_pages(self):
        project = planned_project()
        project["schema_version"] = "7.1"
        project["skill_version"] = "7.1.0"
        project["target"].update(
            {
                "full_set": True,
                "ratio_strategy": "mixed_by_surface",
                "ratio_basis": "商品图库与纵向详情页分别设计",
            }
        )
        pages = []
        for index in range(8):
            page = copy.deepcopy(project["pages"][0])
            page["id"] = f"page-{index + 1:02d}"
            page["surface"] = (
                "search_main" if index == 0 else "gallery" if index < 5 else "detail"
            )
            pages.append(page)
        project["pages"] = pages

        errors = load_contract_module().validate_project(project)

        self.assertIn("mixed-ratio-strategy-requires-multiple-aspect-ratios", errors)

    def test_v71_full_set_cannot_call_multiple_surfaces_one_uniform_platform_gallery(self):
        project = planned_project()
        project["target"].update(
            {
                "full_set": True,
                "ratio_strategy": "uniform_by_platform",
                "ratio_basis": "淘宝商品图库和可复用详情模块统一使用方图",
            }
        )
        pages = []
        for index in range(8):
            page = copy.deepcopy(project["pages"][0])
            page["id"] = f"page-{index + 1:02d}"
            page["surface"] = (
                "search_main" if index == 0 else "gallery" if index < 6 else "detail"
            )
            pages.append(page)
        project["pages"] = pages

        errors = load_contract_module().validate_project(project)

        self.assertIn(
            "full-set-multiple-surfaces-requires-mixed-ratio-strategy", errors
        )

    def test_v71_named_platform_full_set_requires_delivery_evidence_before_confirmation(self):
        project = planned_project()
        project["target"].update(
            {
                "platform": "Taobao",
                "full_set": True,
                "ratio_strategy": "mixed_by_surface",
                "ratio_basis": "方形图库与纵向详情页分别设计",
            }
        )
        pages = []
        for index in range(8):
            page = copy.deepcopy(project["pages"][0])
            page["id"] = f"page-{index + 1:02d}"
            page["surface"] = (
                "search_main" if index == 0 else "gallery" if index < 6 else "detail"
            )
            page["size"] = "1024x1024" if index < 6 else "1024x1365"
            pages.append(page)
        project["pages"] = pages
        project["research"] = []

        errors = load_contract_module().validate_project(project)

        self.assertIn("platform-full-set-requires-delivery-evidence", errors)

    def test_v71_official_platform_delivery_research_unblocks_full_set_planning(self):
        project = planned_project()
        project["target"].update(
            {
                "platform": "Taobao",
                "full_set": True,
                "ratio_strategy": "mixed_by_surface",
                "ratio_basis": "官方资料区分主图、长图和详情页图",
            }
        )
        pages = []
        for index in range(8):
            page = copy.deepcopy(project["pages"][0])
            page["id"] = f"page-{index + 1:02d}"
            page["surface"] = (
                "search_main" if index == 0 else "gallery" if index < 6 else "detail"
            )
            page["size"] = "1024x1024" if index < 6 else "1024x1365"
            pages.append(page)
        project["pages"] = pages
        project["research"] = [
            {
                "id": "platform-taobao-01",
                "kind": "platform_delivery",
                "source_type": "official",
                "url": "https://developer.alibaba.com/docs/api.htm?apiId=68771",
                "checked_at": "2026-07-15",
                "finding": "官方素材类型区分主图、长图、详情页图和主搜3:4图。",
            }
        ]

        errors = load_contract_module().validate_project(project)

        self.assertNotIn("platform-full-set-requires-delivery-evidence", errors)

    def test_v72_explicit_store_rule_can_allow_one_ratio_across_all_surfaces(self):
        project = planned_project()
        project["schema_version"] = "7.2"
        project["skill_version"] = "7.2.0"
        project["target"].update(
            {
                "platform": "custom-store",
                "full_set": True,
                "ratio_strategy": "uniform_by_platform",
                "ratio_basis": "用户的当前店铺主题要求三个交付面全部使用 1:1",
            }
        )
        composition_types = [
            "hero",
            "detail",
            "angles",
            "scene",
            "diagram",
            "process",
            "package",
            "closing",
        ]
        pages = []
        for index, composition_type in enumerate(composition_types):
            page = copy.deepcopy(project["pages"][0])
            page["id"] = f"page-{index + 1:02d}"
            page["surface"] = (
                "search_main" if index == 0 else "gallery" if index < 5 else "detail"
            )
            page["size"] = "1024x1024"
            page["composition_type"] = composition_type
            page["buyer_question"] = f"买家问题 {index + 1}"
            pages.append(page)
        project["pages"] = pages
        project["research"] = [
            {
                "id": "store-theme-01",
                "kind": "platform_delivery",
                "source_type": "store_theme",
                "checked_at": "2026-07-15",
                "finding": "用户的当前店铺主题截图明确要求三个交付面使用同一方形画布。",
                "uniform_across_surfaces": True,
                "applies_to_surfaces": ["search_main", "gallery", "detail"],
            }
        ]

        errors = load_contract_module().validate_project(project)

        self.assertNotIn(
            "full-set-multiple-surfaces-requires-mixed-ratio-strategy", errors
        )

    def test_v72_full_set_rejects_a_contact_sheet_plan_made_of_repeated_scenes(self):
        project = planned_project()
        project["schema_version"] = "7.2"
        project["skill_version"] = "7.2.0"
        project["target"].update(
            {
                "platform": "generic",
                "full_set": True,
                "ratio_strategy": "mixed_by_surface",
                "ratio_basis": "方形图库与纵向详情页分别设计",
            }
        )
        pages = []
        for index in range(8):
            page = copy.deepcopy(project["pages"][0])
            page["id"] = f"page-{index + 1:02d}"
            page["surface"] = (
                "search_main" if index == 0 else "gallery" if index < 6 else "detail"
            )
            page["size"] = "1024x1024" if index < 6 else "1024x1365"
            page["composition_type"] = "scene"
            pages.append(page)
        project["pages"] = pages

        errors = load_contract_module().validate_project(project)

        self.assertIn("full-set-requires-composition-diversity", errors)
        self.assertIn("full-set-has-too-many-scene-pages", errors)

    def test_v72_detail_surface_cannot_be_only_more_lifestyle_scenes(self):
        project = planned_project()
        project["schema_version"] = "7.2"
        project["skill_version"] = "7.2.0"
        project["target"].update(
            {
                "platform": "generic",
                "full_set": True,
                "ratio_strategy": "mixed_by_surface",
                "ratio_basis": "方形图库与纵向详情页分别设计",
            }
        )
        composition_types = [
            "hero",
            "scene",
            "detail",
            "comparison",
            "process",
            "package",
            "scene",
            "closing",
        ]
        pages = []
        for index, composition_type in enumerate(composition_types):
            page = copy.deepcopy(project["pages"][0])
            page["id"] = f"page-{index + 1:02d}"
            page["surface"] = (
                "search_main" if index == 0 else "gallery" if index < 6 else "detail"
            )
            page["size"] = "1024x1024" if index < 6 else "1024x1365"
            page["composition_type"] = composition_type
            pages.append(page)
        project["pages"] = pages

        errors = load_contract_module().validate_project(project)

        self.assertIn("full-set-detail-needs-informational-composition", errors)

    def test_v72_full_set_requires_distinct_buyer_questions(self):
        project = planned_project()
        project["schema_version"] = "7.2"
        project["skill_version"] = "7.2.0"
        project["target"].update(
            {
                "platform": "generic",
                "full_set": True,
                "ratio_strategy": "mixed_by_surface",
                "ratio_basis": "图库与详情页分别设计",
            }
        )
        composition_types = [
            "hero",
            "detail",
            "angles",
            "scene",
            "diagram",
            "process",
            "package",
            "closing",
        ]
        pages = []
        for index, composition_type in enumerate(composition_types):
            page = copy.deepcopy(project["pages"][0])
            page["id"] = f"page-{index + 1:02d}"
            page["surface"] = (
                "search_main" if index == 0 else "gallery" if index < 5 else "detail"
            )
            page["size"] = "1024x1024" if index < 5 else "1024x1365"
            page["composition_type"] = composition_type
            page["buyer_question"] = "这页的商品好看吗？"
            pages.append(page)
        project["pages"] = pages

        errors = load_contract_module().validate_project(project)

        self.assertIn("full-set-requires-distinct-buyer-questions", errors)

    def test_v72_informational_copy_requires_evidence_facts(self):
        project = planned_project()
        project["schema_version"] = "7.2"
        project["skill_version"] = "7.2.0"
        project["pages"][0]["composition_type"] = "diagram"
        project["pages"][0]["fact_ids"] = []

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:informational-copy-requires-facts", errors)

    def test_v72_page_plan_cannot_leave_core_brief_fields_blank(self):
        project = planned_project()
        project["schema_version"] = "7.2"
        project["skill_version"] = "7.2.0"
        project["pages"][0]["composition_type"] = "detail"
        project["pages"][0]["buyer_question"] = ""
        project["pages"][0]["visual_brief"] = ""

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:empty-page-field:buyer_question", errors)
        self.assertIn("page-01:empty-page-field:visual_brief", errors)

    def test_v71_requires_ratio_strategy_and_its_basis(self):
        project = planned_project()
        project["target"].pop("ratio_strategy")
        project["target"].pop("ratio_basis")

        errors = load_contract_module().validate_project(project)

        self.assertIn("target:missing-ratio-strategy", errors)
        self.assertIn("target:missing-ratio-basis", errors)

    def test_v71_complete_set_requires_listing_and_detail_surfaces(self):
        project = planned_project()
        project["schema_version"] = "7.1"
        project["skill_version"] = "7.1.0"
        project["target"].update(
            {
                "full_set": True,
                "ratio_strategy": "uniform_by_platform",
                "ratio_basis": "测试用统一平台规格",
            }
        )
        pages = []
        for index in range(8):
            page = copy.deepcopy(project["pages"][0])
            page["id"] = f"page-{index + 1:02d}"
            page["surface"] = "gallery"
            pages.append(page)
        project["pages"] = pages

        errors = load_contract_module().validate_project(project)

        self.assertIn("full-set-requires-detail-surface", errors)

    def test_v71_complete_set_requires_search_main_surface(self):
        project = planned_project()
        project["schema_version"] = "7.1"
        project["skill_version"] = "7.1.0"
        project["target"].update(
            {
                "full_set": True,
                "ratio_strategy": "uniform_by_platform",
                "ratio_basis": "测试用统一平台规格",
            }
        )
        pages = []
        for index in range(8):
            page = copy.deepcopy(project["pages"][0])
            page["id"] = f"page-{index + 1:02d}"
            page["surface"] = "detail"
            pages.append(page)
        project["pages"] = pages

        errors = load_contract_module().validate_project(project)

        self.assertIn("full-set-requires-search-main-surface", errors)

    def test_v71_rejects_unknown_ratio_strategy_and_surface(self):
        project = planned_project()
        project["schema_version"] = "7.1"
        project["skill_version"] = "7.1.0"
        project["target"].update(
            {
                "ratio_strategy": "eight_square_default",
                "ratio_basis": "没有平台依据",
            }
        )
        project["pages"][0]["surface"] = "主图"

        errors = load_contract_module().validate_project(project)

        self.assertIn("target:unsupported-ratio-strategy:eight_square_default", errors)
        self.assertIn("page-01:unsupported-surface:主图", errors)

    def test_v71_single_surface_strategy_cannot_hide_multiple_surfaces(self):
        project = planned_project()
        project["schema_version"] = "7.1"
        project["skill_version"] = "7.1.0"
        project["target"].update(
            {
                "ratio_strategy": "single_surface",
                "ratio_basis": "用户只要求商品图库",
            }
        )
        project["pages"][0]["surface"] = "gallery"
        second_page = copy.deepcopy(project["pages"][0])
        second_page["id"] = "page-02"
        second_page["surface"] = "detail"
        project["pages"].append(second_page)

        errors = load_contract_module().validate_project(project)

        self.assertIn("single-surface-strategy-has-multiple-surfaces", errors)

    def test_v71_planned_page_requires_concrete_pixel_dimensions(self):
        project = planned_project()
        project["schema_version"] = "7.1"
        project["skill_version"] = "7.1.0"
        project["target"].update(
            {
                "ratio_strategy": "single_surface",
                "ratio_basis": "用户只要求商品图库",
            }
        )
        project["pages"][0]["surface"] = "gallery"
        project["pages"][0]["size"] = "1:1"

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:invalid-page-size:1:1", errors)

    def test_page_references_must_resolve_to_source_assets(self):
        project = planned_project()
        project["pages"][0]["references"] = ["missing-asset"]

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:unknown-reference:missing-asset", errors)

    def test_source_asset_hash_is_checked_when_files_are_available(self):
        project = planned_project()
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            source = project_dir / "source" / "front.png"
            source.parent.mkdir()
            source.write_bytes(b"source-product-pixels")

            errors = load_contract_module().validate_project(project, project_dir)

        self.assertIn("asset-front:source-sha256-mismatch", errors)

    def test_page_fact_ids_must_resolve_to_evidence(self):
        project = planned_project()
        project["pages"][0]["fact_ids"] = ["missing-fact"]

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:unknown-fact:missing-fact", errors)

    def test_every_final_copy_string_must_be_literal_in_page_prompt(self):
        project = planned_project()
        project["pages"][0]["copy"].append("一键萃取")

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:copy-not-in-prompt:一键萃取", errors)

    def test_regulated_copy_requires_evidence_fact_ids(self):
        project = planned_project()
        project["target"]["mode"] = "regulated"
        project["pages"][0]["fact_ids"] = []

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:regulated-copy-requires-facts", errors)

    def test_amazon_search_main_rejects_added_copy(self):
        project = planned_project()
        project["target"]["platform"] = "amazon"
        project["pages"][0]["surface"] = "search_main"

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:amazon-search-main-must-be-copy-free", errors)

    def test_v71_amazon_main_rule_uses_surface_not_content_role(self):
        project = planned_project()
        project["schema_version"] = "7.1"
        project["skill_version"] = "7.1.0"
        project["target"].update(
            {
                "platform": "amazon",
                "ratio_strategy": "single_surface",
                "ratio_basis": "Amazon listing MAIN image",
            }
        )
        project["pages"][0]["surface"] = "search_main"
        project["pages"][0]["role"] = "hero"

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:amazon-search-main-must-be-copy-free", errors)

    def test_review_stage_requires_real_generation_record_for_each_page(self):
        project = planned_project()
        project["status"] = "review"
        project["pages"][0]["output"] = "images/page-01.png"

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:missing-generation-record", errors)

    def test_review_stage_requires_contact_sheet_and_page_result(self):
        project = planned_project()
        project["status"] = "review"
        project["confirmation"]["status"] = "confirmed"
        project["pages"][0]["output"] = "images/page-01.png"
        project["generation_log"] = [generation_record("b" * 64)]
        project["review"]["status"] = "manual_review"
        project["review"]["reviewer_type"] = "same_agent"

        errors = load_contract_module().validate_project(project)

        self.assertIn("review-requires-contact-sheet", errors)
        self.assertIn("page-01:review-requires-page-result", errors)

    def test_full_set_review_requires_evidence_for_set_level_quality_checks(self):
        project = planned_project()
        project["schema_version"] = "7.2"
        project["skill_version"] = "7.2.0"
        project["pages"][0]["composition_type"] = "hero"
        project["target"].update(
            {
                "platform": "generic",
                "full_set": True,
                "ratio_strategy": "mixed_by_surface",
                "ratio_basis": "图库与详情页分别设计",
            }
        )
        project["status"] = "review"
        project["confirmation"]["status"] = "confirmed"
        project["pages"][0]["output"] = "images/page-01.png"
        project["generation_log"] = [generation_record("b" * 64)]
        project["review"].update(
            {
                "status": "manual_review",
                "reviewer_type": "same_agent",
                "contact_sheet": "review/contact-sheet.jpg",
                "contact_sheet_sha256": "c" * 64,
                "pages": [
                    {"page_id": "page-01", "status": "pass", "issues": []}
                ],
            }
        )

        errors = load_contract_module().validate_project(project)

        self.assertIn("review:missing-set-check:commercial_coverage", errors)
        self.assertIn("review:missing-set-check:composition_diversity", errors)
        self.assertIn("review:missing-set-check:surface_difference", errors)

    def test_review_stage_checks_contact_sheet_hash(self):
        project = planned_project()
        project["status"] = "review"
        project["confirmation"]["status"] = "confirmed"
        project["pages"][0]["output"] = "images/page-01.png"
        project["review"].update(
            {
                "status": "manual_review",
                "reviewer_type": "same_agent",
                "contact_sheet": "review/contact-sheet.jpg",
                "contact_sheet_sha256": "0" * 64,
                "pages": [{"page_id": "page-01", "status": "pass", "issues": []}],
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            (project_dir / "source").mkdir()
            source = project_dir / "source" / "front.png"
            source.write_bytes(b"source")
            project["source_assets"][0]["sha256"] = hashlib.sha256(
                source.read_bytes()
            ).hexdigest()
            (project_dir / "images").mkdir()
            output = project_dir / "images" / "page-01.png"
            Image.new("RGB", (1024, 1024), "white").save(output)
            output_hash = hashlib.sha256(output.read_bytes()).hexdigest()
            project["generation_log"] = [generation_record(output_hash)]
            (project_dir / "review").mkdir()
            (project_dir / "review" / "contact-sheet.jpg").write_bytes(b"contact")

            errors = load_contract_module().validate_project(project, project_dir)

        self.assertIn("contact-sheet-sha256-mismatch", errors)

    def test_visual_review_redo_can_never_validate_as_passed(self):
        project = planned_project()
        project["status"] = "review"
        project["confirmation"]["status"] = "confirmed"
        project["pages"][0]["output"] = "images/page-01.png"
        project["generation_log"] = [generation_record("b" * 64)]
        project["review"].update(
            {
                "status": "manual_review",
                "reviewer_type": "same_agent",
                "contact_sheet": "review/contact-sheet.jpg",
                "contact_sheet_sha256": "c" * 64,
                "pages": [
                    {"page_id": "page-01", "status": "redo", "issues": ["PPT感"]}
                ],
            }
        )

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:visual-review-failed", errors)

    def test_review_stage_requires_named_review_state_and_reviewer(self):
        project = planned_project()
        project["status"] = "review"
        project["confirmation"]["status"] = "confirmed"
        project["pages"][0]["output"] = "images/page-01.png"
        project["generation_log"] = [generation_record("b" * 64)]
        project["review"].update(
            {
                "contact_sheet": "review/contact-sheet.jpg",
                "contact_sheet_sha256": "c" * 64,
                "pages": [{"page_id": "page-01", "status": "pass", "issues": []}],
            }
        )

        errors = load_contract_module().validate_project(project)

        self.assertIn("review-stage-requires-manual-review-metadata", errors)

    def test_generation_record_requires_real_tool_model_time_prompt_trace(self):
        project = planned_project()
        project["status"] = "review"
        project["pages"][0]["output"] = "images/page-01.png"
        project["generation_log"] = [{"page_id": "page-01", "post_processing": []}]

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:incomplete-generation-record:tool", errors)

    def test_generation_record_rejects_non_image_model_tool(self):
        project = planned_project()
        project["generation_log"] = [generation_record("b" * 64)]
        project["generation_log"][0]["tool"] = "pillow"

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:final-image-tool-must-be-codex-imagegen", errors)

    def test_generation_record_prompt_must_match_confirmed_page_prompt(self):
        project = planned_project()
        project["generation_log"] = [generation_record("b" * 64)]
        project["generation_log"][0]["prompt"] = "a shortened prompt"

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:generation-prompt-does-not-match-page", errors)

    def test_review_stage_checks_output_hash(self):
        project = planned_project()
        project["status"] = "review"
        project["pages"][0]["output"] = "images/page-01.png"
        project["generation_log"] = [generation_record("0" * 64)]
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            (project_dir / "images").mkdir()
            image_path = project_dir / "images" / "page-01.png"
            Image.new("RGB", (1024, 1024), "white").save(image_path)

            errors = load_contract_module().validate_project(project, project_dir)

        self.assertIn("page-01:output-sha256-mismatch", errors)

    def test_review_stage_checks_real_image_dimensions(self):
        project = planned_project()
        project["status"] = "review"
        project["pages"][0]["output"] = "images/page-01.png"
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            (project_dir / "images").mkdir()
            image_path = project_dir / "images" / "page-01.png"
            Image.new("RGB", (800, 800), "white").save(image_path)
            image_hash = hashlib.sha256(image_path.read_bytes()).hexdigest()
            project["generation_log"] = [generation_record(image_hash)]

            errors = load_contract_module().validate_project(project, project_dir)

        self.assertIn("page-01:output-size-mismatch:800x800!=1024x1024", errors)

    def test_generation_record_rejects_any_consumer_post_processing(self):
        project = planned_project()
        project["generation_log"] = [
            {
                "page_id": "page-01",
                "tool": "codex_image_gen",
                "model": "gpt-image-2",
                "request_id": "req-001",
                "generated_at": "2026-07-15T10:00:00+08:00",
                "source_asset_ids": ["asset-front"],
                "output": "images/page-01.png",
                "output_sha256": "b" * 64,
                "post_processing": ["Pillow text overlay"],
            }
        ]

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:consumer-post-processing-forbidden", errors)

    def test_generation_record_cannot_omit_post_processing_field(self):
        project = planned_project()
        record = generation_record("b" * 64)
        record.pop("post_processing")
        project["generation_log"] = [record]

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:incomplete-generation-record:post_processing", errors)

    def test_generation_record_source_assets_must_resolve(self):
        project = planned_project()
        record = generation_record("b" * 64)
        record["source_asset_ids"] = ["missing-asset"]
        project["generation_log"] = [record]

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:unknown-generation-source:missing-asset", errors)

    def test_generation_output_must_match_page_output(self):
        project = planned_project()
        project["pages"][0]["output"] = "images/page-01.png"
        record = generation_record("b" * 64)
        record["output"] = "images/other.png"
        project["generation_log"] = [record]

        errors = load_contract_module().validate_project(project)

        self.assertIn("page-01:generation-output-does-not-match-page", errors)

    def test_project_directory_rejects_base_or_layout_artifacts(self):
        project = planned_project()
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            (project_dir / "base").mkdir()
            (project_dir / "base" / "page-01.png").write_bytes(b"not-an-image")

            errors = load_contract_module().validate_project(project, project_dir)

        self.assertIn("forbidden-production-artifact:base/page-01.png", errors)

    def test_same_agent_review_cannot_be_final_acceptance(self):
        project = planned_project()
        project["status"] = "accepted"
        project["review"]["status"] = "accepted"
        project["review"]["reviewer_type"] = "same_agent"

        errors = load_contract_module().validate_project(project)

        self.assertIn("accepted-project-requires-user-or-independent-review", errors)

    def test_final_acceptance_requires_accepted_review_status(self):
        project = planned_project()
        project["status"] = "accepted"
        project["confirmation"]["status"] = "confirmed"
        project["pages"][0]["output"] = "images/page-01.png"
        project["generation_log"] = [generation_record("b" * 64)]
        project["review"].update(
            {
                "status": "manual_review",
                "reviewer_type": "user",
                "contact_sheet": "review/contact-sheet.jpg",
                "contact_sheet_sha256": "c" * 64,
                "pages": [{"page_id": "page-01", "status": "pass", "issues": []}],
            }
        )

        errors = load_contract_module().validate_project(project)

        self.assertIn("accepted-project-requires-accepted-review-status", errors)

    def test_accepted_project_requires_contact_sheet_and_page_passes(self):
        project = planned_project()
        project["status"] = "accepted"
        project["review"]["status"] = "accepted"
        project["review"]["reviewer_type"] = "user"

        errors = load_contract_module().validate_project(project)

        self.assertIn("accepted-project-requires-contact-sheet", errors)
        self.assertIn("page-01:accepted-page-requires-pass-review", errors)


if __name__ == "__main__":
    unittest.main()
