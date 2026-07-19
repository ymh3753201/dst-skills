#!/usr/bin/env python3
"""Compile v8.2 page strategy into executable Image 2 prompts."""

import argparse
import json
from pathlib import Path


def _copy_blocks(copy_value):
    if not isinstance(copy_value, dict):
        return []
    blocks = []
    for key in ("headline", "subheadline"):
        block = copy_value.get(key)
        if isinstance(block, dict):
            blocks.append((key, block))
    for key in ("supporting_points", "microcopy"):
        value = copy_value.get(key, [])
        if isinstance(value, list):
            blocks.extend((key, block) for block in value if isinstance(block, dict))
    return blocks


def _joined(value):
    if isinstance(value, list):
        return "、".join(str(item) for item in value)
    if isinstance(value, dict):
        return "；".join(f"{key}={item}" for key, item in value.items())
    return str(value)


def compile_page_prompt(project, page):
    """Build one complete prompt from approved strategy, copy and layout fields."""
    product = project.get("product", {})
    target = project.get("target", {})
    visual = project.get("visual_direction", {})
    blueprint = page.get("visual_brief", {})
    copy_blocks = _copy_blocks(page.get("copy", {}))

    if copy_blocks:
        copy_lines = []
        for role, block in copy_blocks:
            fact_note = ""
            if block.get("fact_ids"):
                fact_note = f"，事实依据 {', '.join(block['fact_ids'])}"
            copy_lines.append(
                f"{role}：“{block.get('text', '')}”（{block.get('kind', '')}{fact_note}）"
            )
        copy_instruction = "；".join(copy_lines)
    else:
        copy_instruction = "本页按平台落点要求保持无附加文案。"

    identity_lock = _joined(product.get("identity_lock", []))
    references = "、".join(page.get("references", []))
    graphic_devices = _joined(blueprint.get("graphic_devices", []))
    content_modules = _joined(blueprint.get("content_modules", []))
    palette = _joined(visual.get("palette", []))
    consistency_rules = _joined(visual.get("consistency_rules", []))
    prohibited = _joined(
        visual.get("copy_strategy", {}).get("prohibited_inferences", [])
    )

    return (
        f"【页面任务】生成一张完整、可直接交付的 {page.get('size')} "
        f"电商成图，平台为 {target.get('platform')}，落点为 {page.get('placement_id')} / "
        f"{page.get('surface')}，页面角色为 {page.get('role')}。回答买家问题："
        f"“{page.get('buyer_question')}”。本页唯一价值是：{page.get('unique_evidence')}。"
        f"【商品身份】参考素材：{references}。商品身份摘要："
        f"{product.get('identity_summary', '')}。必须锁定：{identity_lock}。"
        f"【构图蓝图】商品尺度：{blueprint.get('product_scale', '')}；"
        f"商品数量与重复视图：{blueprint.get('product_multiplicity', '')}；"
        f"主焦点：{blueprint.get('focal_zone', '')}；文案区：{blueprint.get('copy_zone', '')}；"
        f"信息层级：{blueprint.get('hierarchy', '')}；内容模块：{content_modules}；"
        f"构图原因：{blueprint.get('composition_rationale', '')}。"
        f"【文案系统】{copy_instruction}逐字准确原生绘制，不省略支撑信息。"
        f"字体气质：{visual.get('typography', '')}。文案必须与商品、光影和图形"
        "建立可见关系，不做顶部悬浮大字。"
        f"【视觉执行】核心概念：{visual.get('creative_concept', '')}；"
        f"风格：{visual.get('style', '')}；色彩：{palette}；光线：{blueprint.get('lighting', '')}；"
        f"空间层次：{blueprint.get('depth', '')}；图形语言：{graphic_devices}；"
        f"信息密度：{blueprint.get('information_density', '')}。"
        f"【负面约束】商品一致性规则：{consistency_rules}。"
        f"不得推断：{prohibited}。不改变商品结构、数量、颜色、Logo、"
        "接口、缝线或比例；不生成空白文案框、重复圆角卡片、PPT 式排版"
        "或与页面任务无关的道具。"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_json")
    parser.add_argument(
        "--write",
        action="store_true",
        help="write compiled prompts back to project.json",
    )
    args = parser.parse_args()
    project_path = Path(args.project_json)
    project = json.loads(project_path.read_text(encoding="utf-8"))
    for page in project.get("pages", []):
        page["prompt"] = compile_page_prompt(project, page)
    if args.write:
        project_path.write_text(
            json.dumps(project, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    else:
        print(json.dumps({page["id"]: page["prompt"] for page in project["pages"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
