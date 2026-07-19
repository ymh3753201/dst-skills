import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
sys.path.insert(0, str(SKILL_DIR / "tests"))

from project_contract import validate_project
from test_v81_confirmation_gate import v81_project


PROMPT_SECTIONS = (
    "【页面任务】",
    "【商品身份】",
    "【构图蓝图】",
    "【文案系统】",
    "【视觉执行】",
    "【负面约束】",
)


def _copy_block(text, kind="safe_commercial", fact_ids=None):
    return {
        "text": text,
        "kind": kind,
        "fact_ids": list(fact_ids or []),
    }


def _structured_copy(index):
    if index == 1:
        return {}
    content = {
        2: (
            "先看整体轮廓",
            "商品结构与比例，一眼建立清晰认知",
            "正面关系完整呈现",
            "主视觉只保留一个核心焦点",
        ),
        3: (
            "放进真实场景再理解",
            "通过环境关系，感受商品进入生活后的状态",
            "场景只负责建立使用代入",
            "商品结构仍以参考素材为准",
        ),
        4: (
            "关键结构，放大看清",
            "从局部关系理解商品设计",
            "近景聚焦本页唯一结构证据",
            "引导线只说明可见位置关系",
        ),
        5: (
            "多个角度，一次看懂",
            "正面、侧面与背面关系更清楚",
            "不同视角保持同一商品身份",
            "结构数量与几何比例不漂移",
        ),
        6: (
            "选购之前，先核对关键信息",
            "把规格关系转成容易理解的选择指引",
            "已确认内容清晰标注",
            "缺失参数保留买前核对提示",
        ),
        7: (
            "把风险与边界说清楚",
            "购买前需要确认的内容集中呈现",
            "事实证据与安全提示明确分层",
            "未确认服务不写成店铺承诺",
        ),
        8: (
            "从认识商品到安心选择",
            "把整套信息收束成清晰的购买路径",
            "回顾外观、场景与选购重点",
            "最后一步提醒核对实际商品信息",
        ),
    }[index]
    headline, subheadline, point_one, point_two = content
    return {
        "headline": _copy_block(headline),
        "subheadline": _copy_block(subheadline),
        "supporting_points": [
            _copy_block(point_one),
            _copy_block(point_two, "scenario_narrative"),
        ],
        "microcopy": [],
    }


def _content_modules(composition_type):
    return {
        "hero": ["hero_product", "benefit_labels"],
        "scene": ["lifestyle_scene", "benefit_labels"],
        "detail": ["macro_proof", "callout"],
        "angles": ["multi_angle_proof", "callout"],
        "diagram": ["decision_diagram", "buyer_guidance"],
        "trust": ["trust_evidence", "buyer_guidance"],
        "closing": ["brand_closing", "benefit_labels"],
    }[composition_type]


def _layout_blueprint(page):
    return {
        "product_scale": "商品占画面 62%-70%",
        "product_multiplicity": "只呈现一套售卖商品；多角度仅为同一商品视图，不代表多件",
        "focal_zone": "右中部主视觉焦点",
        "copy_zone": "左侧约 32% 图文信息区",
        "hierarchy": "主标题 > 利益副标题 > 两条支撑信息",
        "graphic_devices": ["与商品轮廓呼应的细线", "少量半透明弧面"],
        "lighting": "主光塑造商品，辅助光保留结构细节",
        "depth": "前景引导、中景商品、背景环境逐层退后",
        "information_density": "medium_high" if page["surface"] == "detail" else "medium",
        "composition_rationale": "让买家先看到商品，再读取利益和支撑信息",
        "content_modules": _content_modules(page["composition_type"]),
    }


def _flatten_copy(copy_value):
    texts = []
    for key in ("headline", "subheadline"):
        block = copy_value.get(key)
        if block:
            texts.append(block["text"])
    for key in ("supporting_points", "microcopy"):
        texts.extend(block["text"] for block in copy_value.get(key, []))
    return texts


def _professional_prompt(page):
    copy_text = "、".join(f"“{text}”" for text in _flatten_copy(page["copy"])) or "无附加文案"
    blueprint = page["visual_brief"]
    return (
        f"【页面任务】生成一张完整、可直接交付的{page['size']}电商成图，回答“{page['buyer_question']}”。"
        "【商品身份】以 asset-01 为唯一商品身份参考，保持轮廓、部件数量、颜色、Logo 位置与几何比例。"
        f"【构图蓝图】{blueprint['product_scale']}；{blueprint['focal_zone']}；{blueprint['copy_zone']}；"
        f"{blueprint.get('product_multiplicity', '')}；"
        f"信息层级为{blueprint['hierarchy']}；内容模块为{'、'.join(blueprint['content_modules'])}。"
        f"【文案系统】逐字准确原生绘制{copy_text}，主副标题与支撑信息形成清晰层级。"
        f"【视觉执行】{blueprint['lighting']}；{blueprint['depth']}；"
        f"使用{'、'.join(blueprint['graphic_devices'])}，信息密度为{blueprint['information_density']}，"
        f"构图原因是{blueprint['composition_rationale']}。"
        "【负面约束】不改变商品身份，不生成未证实参数、功能、配件、品牌名或售后承诺，不做空白卡片和 PPT 式堆叠。"
    )


def v82_project():
    project = copy.deepcopy(v81_project())
    project["schema_version"] = "8.2"
    project["skill_version"] = "8.2.0"
    project["target"]["delivery_scope"] = "full_evidence"
    project["visual_direction"]["commercial_completeness"] = "complete"
    project["visual_direction"]["copy_strategy"] = {
        "principle": "缺少硬参数不等于缺少商业文案，但安全文案不得伪装成商品性能。",
        "fact_copy_rule": "参数、功能、材质、配件与服务必须绑定已批准事实。",
        "safe_copy_pillars": ["可见设计语言", "审美利益", "场景情绪", "类目教育", "买家引导"],
        "density_by_surface": {"search_main": "none_or_low", "gallery": "medium", "detail": "medium_high"},
        "prohibited_inferences": ["未证实参数", "未证实功能", "未证实服务"],
    }
    for decision in project["decision_map"]:
        decision["blocking_scope"] = "none"
        decision["safe_fallback"] = ""
    for index, page in enumerate(project["pages"], start=1):
        page["copy"] = _structured_copy(index)
        page["visual_brief"] = _layout_blueprint(page)
        page["has_factual_claims"] = False
        page["claim_fact_ids"] = []
        page["prompt"] = _professional_prompt(page)
    for placement in project["target"]["placements"]:
        placement["quantity"] = sum(
            page["placement_id"] == placement["id"] for page in project["pages"]
        )
    project["confirmation"].update(
        {
            "plan_sha256": "",
            "execution_manifest_sha256": "",
        }
    )
    return project


def _execution_manifest_sha256(project):
    fields = (
        "id",
        "placement_id",
        "surface",
        "role",
        "composition_type",
        "buyer_question",
        "decision_ids",
        "primary_decision_id",
        "unique_evidence",
        "has_factual_claims",
        "claim_fact_ids",
        "size",
        "references",
        "fact_ids",
        "copy",
        "visual_brief",
        "prompt",
    )
    payload = [{key: page.get(key) for key in fields} for page in project["pages"]]
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _review_project():
    project = v82_project()
    project["status"] = "review"
    project["confirmation"].update(
        {
            "status": "confirmed",
            "confirmed_at": "2026-07-18T10:00:00+08:00",
            "method": "用户确认生成",
            "plan_sha256": "b" * 64,
        }
    )
    project["confirmation"]["execution_manifest_sha256"] = _execution_manifest_sha256(
        project
    )
    project["generation_log"] = []
    for index, page in enumerate(project["pages"], start=1):
        page["output"] = f"images/{page['id']}.png"
        prompt_hash = hashlib.sha256(page["prompt"].encode("utf-8")).hexdigest()
        project["generation_log"].append(
            {
                "page_id": page["id"],
                "attempt": 1,
                "tool": "image_gen.imagegen",
                "model": "gpt-image-2",
                "request_id": f"request-{index:02d}",
                "generated_at": f"2026-07-18T10:{index:02d}:00+08:00",
                "prompt": page["prompt"],
                "prompt_sha256": prompt_hash,
                "plan_sha256": project["confirmation"]["plan_sha256"],
                "source_asset_ids": page["references"],
                "output": page["output"],
                "output_sha256": "c" * 64,
                "post_processing": [],
            }
        )
    project["confirmation"]["execution_manifest_sha256"] = _execution_manifest_sha256(
        project
    )
    project["review"] = {
        "status": "manual_review",
        "reviewer_type": "same_agent",
        "contact_sheet": "review/contact-sheet.jpg",
        "contact_sheet_sha256": "d" * 64,
        "set_checks": {
            name: {"status": "pass", "evidence": "填写了一段通过说明"}
            for name in (
                "commercial_coverage",
                "surface_difference",
                "composition_diversity",
                "text_integration",
                "product_consistency",
            )
        },
        "pages": [
            {
                "page_id": page["id"],
                "status": "pass",
                "evidence": "人工原图复核通过",
            }
            for page in project["pages"]
        ],
    }
    return project


class V82CommercialExecutionTests(unittest.TestCase):
    def test_professional_v82_project_is_valid(self):
        self.assertEqual(validate_project(v82_project()), [])

    def test_non_search_page_requires_supporting_commercial_content(self):
        project = v82_project()
        project["pages"][1]["copy"]["supporting_points"] = []
        project["pages"][1]["prompt"] = _professional_prompt(project["pages"][1])

        errors = validate_project(project)

        self.assertIn("page-02:commercial-copy-needs-supporting-content", errors)

    def test_generic_placeholder_copy_is_rejected(self):
        project = v82_project()
        page = project["pages"][1]
        page["copy"]["headline"]["text"] = "第12页核心价值"
        page["prompt"] = _professional_prompt(page)

        errors = validate_project(project)

        self.assertIn("page-02:commercial-copy-contains-placeholder", errors)

    def test_repeated_supporting_copy_across_pages_is_rejected(self):
        project = v82_project()
        repeated = "同一句辅助信息不应跨页重复出现"
        for page in project["pages"][1:4]:
            page["copy"]["supporting_points"][0]["text"] = repeated
            page["prompt"] = _professional_prompt(page)

        errors = validate_project(project)

        self.assertIn(
            "commercial-copy-repetition:同一句辅助信息不应跨页重复出现:3",
            errors,
        )

    def test_safe_commercial_copy_does_not_require_product_fact(self):
        project = v82_project()
        page = project["pages"][1]
        self.assertFalse(page["has_factual_claims"])
        self.assertEqual(page["claim_fact_ids"], [])

        self.assertEqual(validate_project(project), [])

    def test_evidence_safe_information_page_can_use_guidance_without_facts(self):
        project = v82_project()
        page = project["pages"][5]
        page["fact_ids"] = []

        errors = validate_project(project)

        self.assertNotIn("page-06:informational-copy-requires-facts", errors)

    def test_visual_brief_requires_executable_layout_blueprint(self):
        project = v82_project()
        project["pages"][1]["visual_brief"] = "高级、简约、商业感"

        errors = validate_project(project)

        self.assertIn("page-02:visual-brief-must-be-layout-blueprint", errors)

    def test_layout_blueprint_requires_product_multiplicity_rule(self):
        project = v82_project()
        project["pages"][1]["visual_brief"].pop("product_multiplicity")
        project["pages"][1]["prompt"] = _professional_prompt(project["pages"][1])

        errors = validate_project(project)

        self.assertIn("page-02:layout-blueprint-missing:product_multiplicity", errors)

    def test_detail_label_cannot_disguise_a_lifestyle_scene(self):
        project = v82_project()
        page = project["pages"][3]
        page["visual_brief"]["content_modules"] = ["lifestyle_scene"]
        page["prompt"] = _professional_prompt(page)

        errors = validate_project(project)

        self.assertIn("page-04:detail-composition-lacks-informational-module", errors)

    def test_placement_quantity_must_match_bound_pages(self):
        project = v82_project()
        project["target"]["placements"][0]["quantity"] += 1

        errors = validate_project(project)

        self.assertIn("square-main:quantity-does-not-match-pages:4!=3", errors)

    def test_prompt_requires_all_professional_execution_sections(self):
        project = v82_project()
        project["pages"][1]["prompt"] = "生成一张高级电商图，文字位于左上。"

        errors = validate_project(project)

        for section in PROMPT_SECTIONS:
            self.assertIn(f"page-02:prompt-missing-section:{section}", errors)

    def test_prompt_must_carry_layout_blueprint_into_generation(self):
        project = v82_project()
        project["pages"][1]["prompt"] = "".join(
            f"{section}通用描述。" for section in PROMPT_SECTIONS
        )

        errors = validate_project(project)

        self.assertIn(
            "page-02:prompt-missing-blueprint-field:product_multiplicity",
            errors,
        )

    def test_claim_level_blocker_allows_evidence_safe_plan(self):
        project = v82_project()
        decision = project["decision_map"][3]
        decision.update(
            {
                "status": "blocking",
                "basis": "missing",
                "claim_type": "missing_fact",
                "fact_ids": [],
                "blocking_scope": "claim",
                "safe_fallback": "不生成规格数字，改用买家核对指引和安全商业文案。",
            }
        )
        project["target"]["delivery_scope"] = "evidence_safe"
        project["visual_direction"]["commercial_completeness"] = "evidence_safe_limited"

        self.assertEqual(validate_project(project), [])

    def test_project_level_blocker_still_prevents_confirmation(self):
        project = v82_project()
        decision = project["decision_map"][0]
        decision.update(
            {
                "status": "blocking",
                "basis": "missing",
                "claim_type": "missing_fact",
                "fact_ids": [],
                "blocking_scope": "project",
                "safe_fallback": "需要补齐商品身份参考后再生成。",
            }
        )

        errors = validate_project(project)

        self.assertIn("decision-identity:planned-project-has-project-blocker", errors)

    def test_generation_timestamp_must_be_after_confirmed_plan(self):
        project = v82_project()
        project["status"] = "generating"
        project["confirmation"].update(
            {
                "status": "confirmed",
                "confirmed_at": "2026-07-18T10:00:00+08:00",
                "method": "用户确认生成",
            }
        )
        page = project["pages"][0]
        page["output"] = "images/page-01.png"
        prompt_sha256 = hashlib.sha256(page["prompt"].encode("utf-8")).hexdigest()
        with tempfile.TemporaryDirectory() as project_dir:
            plan_path = Path(project_dir) / "plan.md"
            plan_path.write_text("用户已确认的完整视觉方案", encoding="utf-8")
            plan_sha256 = hashlib.sha256(plan_path.read_bytes()).hexdigest()
            project["confirmation"]["plan_sha256"] = plan_sha256
            project["confirmation"]["execution_manifest_sha256"] = _execution_manifest_sha256(project)
            project["generation_log"] = [
                {
                    "page_id": page["id"],
                    "attempt": 1,
                    "tool": "image_gen.imagegen",
                    "model": "gpt-image-2",
                    "request_id": "request-01",
                    "generated_at": "2026-07-18T10:00:00+08:00",
                    "prompt": page["prompt"],
                    "prompt_sha256": prompt_sha256,
                    "plan_sha256": plan_sha256,
                    "source_asset_ids": page["references"],
                    "output": page["output"],
                    "output_sha256": "a" * 64,
                    "post_processing": [],
                }
            ]

            errors = validate_project(project, project_dir)

        self.assertIn("page-01:generation-must-follow-confirmation", errors)

    def test_prompt_compiler_builds_all_execution_sections_and_copy(self):
        compiler_path = SKILL_DIR / "scripts" / "compile_prompts.py"
        if not compiler_path.is_file():
            self.fail("prompt compiler is missing")
        spec = importlib.util.spec_from_file_location("compile_prompts", compiler_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        project = v82_project()
        page = project["pages"][1]

        prompt = module.compile_page_prompt(project, page)

        for section in PROMPT_SECTIONS:
            self.assertIn(section, prompt)
        for text in _flatten_copy(page["copy"]):
            self.assertIn(text, prompt)
        self.assertIn(page["visual_brief"]["product_scale"], prompt)
        self.assertIn(page["visual_brief"]["product_multiplicity"], prompt)
        self.assertIn(project["visual_direction"]["creative_concept"], prompt)

    def test_review_requires_commercial_quality_set_checks(self):
        project = _review_project()

        errors = validate_project(project)

        for check_name in (
            "copy_richness",
            "buyer_value",
            "prompt_fidelity",
            "claim_safety",
        ):
            self.assertIn(f"review:missing-set-check:{check_name}", errors)

    def test_page_review_requires_scores_and_specific_evidence(self):
        project = _review_project()

        errors = validate_project(project)

        self.assertIn("page-01:review-requires-quality-scores", errors)
        self.assertIn("page-01:review-evidence-too-generic", errors)

    def test_regression_tests_must_not_depend_on_mutable_generated_projects(self):
        offenders = []
        for test_path in (SKILL_DIR / "tests").glob("test_v*.py"):
            if test_path.resolve() == Path(__file__).resolve():
                continue
            text = test_path.read_text(encoding="utf-8")
            if "WORKSPACE_DIR" in text and '"generated"' in text:
                offenders.append(test_path.name)

        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
