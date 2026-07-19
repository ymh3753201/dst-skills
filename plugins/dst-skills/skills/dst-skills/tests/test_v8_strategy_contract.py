import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from project_contract import validate_project


def v80_project():
    placements = [
        {
            "id": "square-main",
            "name": "方形搜索首图与图库",
            "surface": "search_main",
            "selected_size": "1200x1200",
            "aspect_ratio": "1:1",
            "quantity": 5,
            "basis": "设计建议；上线前按当前后台复核",
            "research_ids": ["platform-01"],
        },
        {
            "id": "portrait-main",
            "name": "3:4 主图",
            "surface": "gallery",
            "selected_size": "1200x1600",
            "aspect_ratio": "3:4",
            "quantity": 2,
            "basis": "平台存在独立 3:4 主图落点；像素为设计建议",
            "research_ids": ["platform-01"],
        },
        {
            "id": "detail-module",
            "name": "纵向详情模块",
            "surface": "detail",
            "selected_size": "1200x1600",
            "aspect_ratio": "3:4",
            "quantity": 3,
            "basis": "店铺内容区设计建议",
            "research_ids": ["platform-01"],
        },
    ]
    decisions = [
        {
            "id": "decision-identity",
            "question": "买家能否第一眼认清商品？",
            "priority": "high",
            "status": "covered",
            "basis": "visible",
            "fact_ids": ["fact-01"],
            "page_ids": ["page-01", "page-02"],
            "reason": "参考图可证明商品外观",
        },
        {
            "id": "decision-use",
            "question": "商品放入真实空间后的关系如何？",
            "priority": "high",
            "status": "covered",
            "basis": "model_inferred",
            "fact_ids": [],
            "page_ids": ["page-03"],
            "reason": "基于参考图的 AI 场景渲染，不作为新增事实",
        },
        {
            "id": "decision-detail",
            "question": "关键结构细节是否看得清？",
            "priority": "high",
            "status": "covered",
            "basis": "visible",
            "fact_ids": ["fact-01"],
            "page_ids": ["page-04", "page-05"],
            "reason": "参考图可见关键结构",
        },
        {
            "id": "decision-fit",
            "question": "规格是否适合目标使用空间？",
            "priority": "medium",
            "status": "covered",
            "basis": "user",
            "fact_ids": ["fact-02"],
            "page_ids": ["page-06"],
            "reason": "用户规格表可追溯",
        },
        {
            "id": "decision-trust",
            "question": "还有哪些风险和服务边界需要说明？",
            "priority": "medium",
            "status": "covered",
            "basis": "user",
            "fact_ids": ["fact-02"],
            "page_ids": ["page-07", "page-08"],
            "reason": "用户确认的服务信息",
        },
    ]
    compositions = [
        "hero",
        "hero",
        "scene",
        "detail",
        "angles",
        "diagram",
        "trust",
        "closing",
    ]
    placement_ids = [
        "square-main",
        "portrait-main",
        "portrait-main",
        "square-main",
        "square-main",
        "detail-module",
        "detail-module",
        "detail-module",
    ]
    decision_ids = [
        ["decision-identity"],
        ["decision-identity"],
        ["decision-use"],
        ["decision-detail"],
        ["decision-detail"],
        ["decision-fit"],
        ["decision-trust"],
        ["decision-trust"],
    ]
    sizes = [
        "1200x1200",
        "1200x1600",
        "1200x1600",
        "1200x1200",
        "1200x1200",
        "1200x1600",
        "1200x1600",
        "1200x1600",
    ]
    pages = []
    for index in range(8):
        copy_text = [] if index == 0 else [f"页面标题 {index + 1}"]
        prompt = "生成完整、可直接交付的电商成图"
        if copy_text:
            prompt += f"，逐字包含“{copy_text[0]}”"
        pages.append(
            {
                "id": f"page-{index + 1:02d}",
                "placement_id": placement_ids[index],
                "surface": next(
                    item["surface"]
                    for item in placements
                    if item["id"] == placement_ids[index]
                ),
                "role": compositions[index],
                "composition_type": compositions[index],
                "buyer_question": next(
                    item["question"]
                    for item in decisions
                    if item["id"] == decision_ids[index][0]
                ),
                "decision_ids": decision_ids[index],
                "size": sizes[index],
                "references": ["asset-01"],
                "fact_ids": (
                    ["fact-01"]
                    if index in {0, 1, 3, 4}
                    else ["fact-02"] if index in {5, 6, 7} else []
                ),
                "copy": copy_text,
                "visual_brief": f"第 {index + 1} 页独立视觉任务",
                "prompt": prompt,
                "output": "",
            }
        )
    return {
        "schema_version": "8.0",
        "skill_version": "8.0.0",
        "status": "planned",
        "product": {
            "name": "通用测试商品",
            "category": "家居",
            "identity_summary": "锁定参考图中的颜色、结构、比例和关键细节",
            "identity_lock": ["主体轮廓", "结构分区", "颜色与比例"],
            "source_diagnosis": ["原图背景干扰主体识别"],
            "design_opportunities": ["重建干净首图并扩展真实使用场景"],
        },
        "target": {
            "platform": "示例平台",
            "market": "CN",
            "use": "多落点完整套图",
            "full_set": True,
            "mode": "standard",
            "placements": placements,
        },
        "source_assets": [
            {
                "id": "asset-01",
                "file": "source/product.png",
                "sha256": "a" * 64,
                "role": "商品身份主参考",
                "proves": ["颜色", "结构", "比例"],
                "limitations": ["只有一个角度"],
            }
        ],
        "facts": [
            {
                "id": "fact-01",
                "text": "可见商品结构与颜色",
                "source": "visible",
                "source_ref": "asset-01",
            },
            {
                "id": "fact-02",
                "text": "用户确认的规格和服务信息",
                "source": "user",
                "source_ref": "用户资料",
            },
        ],
        "research": [
            {
                "id": "platform-01",
                "kind": "platform_delivery",
                "source_type": "official",
                "url": "https://example.com/platform",
                "checked_at": "2026-07-15",
                "finding": "平台存在多个图片落点，具体像素分别记录。",
            }
        ],
        "decision_map": decisions,
        "visual_direction": {
            "positioning": "解决目标买家最重要的购买决策",
            "audience": "目标买家与使用场景",
            "purchase_motivations": ["识别商品", "理解价值"],
            "purchase_barriers": ["规格", "信任"],
            "creative_concept": "一个贯穿整套的视觉主题",
            "message_hierarchy": ["核心定位", "利益点", "证据"],
            "style": "专业、克制、可信",
            "palette": ["#F2EEE7", "#342A24"],
            "typography": "现代中文无衬线",
            "layout_system": "统一品牌语法，不复制同一版式",
            "consistency_rules": ["商品身份不漂移"],
        },
        "pages": pages,
        "confirmation": {"status": "pending", "confirmed_at": "", "method": ""},
        "generation_log": [],
        "review": {
            "status": "planned",
            "reviewer_type": "",
            "contact_sheet": "",
            "contact_sheet_sha256": "",
            "set_checks": {},
            "pages": [],
        },
    }


class V80StrategyContractTests(unittest.TestCase):
    def test_complete_v80_strategy_is_valid(self):
        self.assertEqual(validate_project(v80_project()), [])

    def test_full_set_requires_multiple_platform_placement_specs(self):
        project = v80_project()
        project["target"]["placements"] = project["target"]["placements"][:1]

        errors = validate_project(project)

        self.assertIn("full-set-requires-multiple-placement-specs", errors)

    def test_full_set_cannot_collapse_all_placements_to_one_selected_size(self):
        project = v80_project()
        for placement in project["target"]["placements"]:
            placement["selected_size"] = "1200x1200"
            placement["aspect_ratio"] = "1:1"
        for page in project["pages"]:
            page["size"] = "1200x1200"

        errors = validate_project(project)

        self.assertIn("full-set-requires-multiple-selected-sizes", errors)

    def test_page_must_match_its_placement_and_selected_size(self):
        project = v80_project()
        project["pages"][0]["placement_id"] = "portrait-main"

        errors = validate_project(project)

        self.assertIn("page-01:surface-does-not-match-placement", errors)
        self.assertIn("page-01:size-does-not-match-placement:1200x1200", errors)

    def test_image2_incompatible_size_is_rejected_before_confirmation(self):
        project = v80_project()
        project["target"]["placements"][2]["selected_size"] = "1080x1440"
        for page in project["pages"]:
            if page["placement_id"] == "detail-module":
                page["size"] = "1080x1440"

        errors = validate_project(project)

        self.assertIn(
            "detail-module:image2-size-edge-must-be-multiple-of-16:1080x1440",
            errors,
        )

    def test_planned_project_cannot_hide_high_priority_evidence_gap(self):
        project = v80_project()
        project["decision_map"][2].update(
            {"status": "blocking", "basis": "missing", "fact_ids": [], "page_ids": []}
        )

        errors = validate_project(project)

        self.assertIn("decision-detail:planned-project-has-blocking-high-priority-decision", errors)

    def test_every_page_links_to_a_real_buyer_decision(self):
        project = v80_project()
        project["pages"][3]["decision_ids"] = []

        errors = validate_project(project)

        self.assertIn("page-04:missing-decision-link", errors)

    def test_schema_only_cli_does_not_require_pillow(self):
        project = v80_project()
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "project.json"
            project_path.write_text(json.dumps(project, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    str(SKILL_DIR / "scripts" / "validate_project.py"),
                    str(project_path),
                    "--schema-only",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PROJECT VALIDATION OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
