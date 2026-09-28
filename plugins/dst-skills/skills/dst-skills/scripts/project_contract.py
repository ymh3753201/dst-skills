#!/usr/bin/env python3
"""Backward-compatible project contract for dst-skills v7.0 through v9.0."""

import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path


PROMPT_SECTIONS = (
    "【页面任务】",
    "【商品身份】",
    "【构图蓝图】",
    "【文案系统】",
    "【视觉执行】",
    "【负面约束】",
)

LAYOUT_BLUEPRINT_FIELDS = (
    "product_scale",
    "product_multiplicity",
    "focal_zone",
    "copy_zone",
    "hierarchy",
    "graphic_devices",
    "lighting",
    "depth",
    "information_density",
    "composition_rationale",
    "content_modules",
)

SAFE_COPY_KINDS = {
    "safe_commercial",
    "scenario_narrative",
    "category_education",
    "buyer_guidance",
}
FACT_COPY_KINDS = {"product_fact", "visual_fact", "platform_fact"}
ALLOWED_COPY_KINDS = SAFE_COPY_KINDS | FACT_COPY_KINDS
COPY_PLACEHOLDER_MARKERS = (
    "待填写",
    "从可见设计出发，让商品更容易被理解",
    "一页只讲一个购买理由",
    "文字、商品与光影共同完成表达",
)

EXECUTION_MANIFEST_FIELDS = (
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


def _copy_blocks(copy_value):
    """Return structured v8.2 copy blocks while keeping legacy lists valid."""
    if isinstance(copy_value, list):
        return [
            {"text": text, "kind": "legacy", "fact_ids": []}
            for text in copy_value
            if isinstance(text, str)
        ]
    if not isinstance(copy_value, dict):
        return []
    blocks = []
    for key in ("headline", "subheadline"):
        block = copy_value.get(key)
        if isinstance(block, dict):
            blocks.append(block)
    for key in ("supporting_points", "microcopy"):
        value = copy_value.get(key, [])
        if isinstance(value, list):
            blocks.extend(block for block in value if isinstance(block, dict))
    return blocks


def _copy_texts(copy_value):
    return [
        block.get("text")
        for block in _copy_blocks(copy_value)
        if isinstance(block.get("text"), str) and block.get("text").strip()
    ]


def _execution_manifest_sha256(project):
    pages = [
        {field: page.get(field) for field in EXECUTION_MANIFEST_FIELDS}
        for page in project.get("pages", [])
    ]
    payload = pages
    if project.get("schema_version") == "9.0":
        payload = {
            "generation_channel": project.get("generation_channel"),
            "pages": pages,
        }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _parse_datetime(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _contains_copy_placeholder(text):
    return any(marker in text for marker in COPY_PLACEHOLDER_MARKERS) or bool(
        re.search(r"第\s*\d+\s*页核心价值", text)
    )

def validate_project(project, project_dir=None):
    """Return validation errors for one project document."""
    errors = []
    pages = project.get("pages", [])
    target = project.get("target", {})
    research = project.get("research", [])

    schema_version = project.get("schema_version")
    supported_versions = {
        "7.0": "7.0.0",
        "7.1": "7.1.0",
        "7.2": "7.2.0",
        "8.0": "8.0.0",
        "8.1": "8.1.0",
        "8.2": "8.2.0",
        "9.0": "9.0.0",
    }
    if schema_version not in supported_versions:
        errors.append("unsupported-schema-version")
    elif project.get("skill_version") != supported_versions[schema_version]:
        errors.append(
            f"skill-version-must-be-{supported_versions[schema_version]}"
        )
    uses_surface_contract = schema_version in {"7.1", "7.2", "8.0", "8.1", "8.2", "9.0"}
    uses_composition_contract = schema_version in {"7.2", "8.0", "8.1", "8.2", "9.0"}
    is_v8x = schema_version in {"8.0", "8.1", "8.2", "9.0"}
    is_v81 = schema_version == "8.1"
    is_v82 = schema_version in {"8.2", "9.0"}
    is_v9 = schema_version == "9.0"
    raw_generation_channel = project.get("generation_channel")
    generation_channel = (
        raw_generation_channel if isinstance(raw_generation_channel, str) else None
    )
    if is_v9 and generation_channel not in {
        "codex_image_with_arkcli_fallback",
        "codex_image",
        "arkcli_seedream_5_pro",
    }:
        errors.append(f"unsupported-generation-channel:{raw_generation_channel}")
    uses_claim_contract = schema_version in {"8.1", "8.2", "9.0"}
    if project.get("status") in {"generating", "review", "accepted"}:
        if project.get("confirmation", {}).get("status") != "confirmed":
            errors.append("generation-requires-confirmed-plan")

    if target.get("full_set") and len(pages) < 8:
        errors.append("full-set-requires-at-least-8-pages")

    if uses_surface_contract and not is_v8x:
        ratio_strategy = target.get("ratio_strategy")
        if not ratio_strategy:
            errors.append("target:missing-ratio-strategy")
        elif ratio_strategy not in {
            "mixed_by_surface",
            "uniform_by_platform",
            "single_surface",
        }:
            errors.append(f"target:unsupported-ratio-strategy:{ratio_strategy}")
        if not target.get("ratio_basis"):
            errors.append("target:missing-ratio-basis")
        surfaces = {page.get("surface") for page in pages}
        concrete_surfaces = surfaces - {None}
        uniform_multi_surface_evidence = any(
            isinstance(item, dict)
            and item.get("kind") == "platform_delivery"
            and item.get("source_type") in {"official", "user", "store_theme"}
            and item.get("uniform_across_surfaces") is True
            and set(item.get("applies_to_surfaces", [])) >= concrete_surfaces
            for item in research
        )
        if (
            target.get("full_set")
            and len(concrete_surfaces) > 1
            and ratio_strategy != "mixed_by_surface"
            and not (
                ratio_strategy == "uniform_by_platform"
                and uniform_multi_surface_evidence
            )
        ):
            errors.append(
                "full-set-multiple-surfaces-requires-mixed-ratio-strategy"
            )
        if target.get("full_set") and "detail" not in surfaces:
            errors.append("full-set-requires-detail-surface")
        if target.get("full_set") and "search_main" not in surfaces:
            errors.append("full-set-requires-search-main-surface")
        if ratio_strategy == "single_surface" and len(surfaces - {None}) > 1:
            errors.append("single-surface-strategy-has-multiple-surfaces")
        platform_name = str(target.get("platform", "")).strip().lower()
        if target.get("full_set") and platform_name not in {"", "generic", "通用"}:
            delivery_evidence = [
                item
                for item in research
                if isinstance(item, dict)
                and item.get("kind") == "platform_delivery"
                and item.get("source_type") in {"official", "user", "store_theme"}
                and item.get("id")
                and item.get("finding")
                and item.get("checked_at")
                and (
                    item.get("source_type") != "official" or item.get("url")
                )
            ]
            if not delivery_evidence:
                errors.append("platform-full-set-requires-delivery-evidence")

    if (
        uses_surface_contract
        and not is_v8x
        and target.get("ratio_strategy") == "mixed_by_surface"
    ):
        aspect_ratios = set()
        for page in pages:
            try:
                width, height = map(int, str(page.get("size", "")).split("x"))
                divisor = math.gcd(width, height)
                aspect_ratios.add((width // divisor, height // divisor))
            except (TypeError, ValueError, ZeroDivisionError):
                continue
        if len(aspect_ratios) < 2:
            errors.append("mixed-ratio-strategy-requires-multiple-aspect-ratios")

    if uses_composition_contract:
        allowed_composition_types = {
            "hero",
            "scene",
            "detail",
            "angles",
            "diagram",
            "process",
            "comparison",
            "package",
            "trust",
            "closing",
        }
        composition_types = {page.get("composition_type") for page in pages}
        if target.get("full_set"):
            if len(composition_types - {None}) < 4:
                errors.append("full-set-requires-composition-diversity")
            if not is_v8x:
                buyer_questions = {
                    str(page.get("buyer_question", "")).strip() for page in pages
                } - {""}
                if len(buyer_questions) < 6:
                    errors.append("full-set-requires-distinct-buyer-questions")
            scene_count = sum(
                page.get("composition_type") in {"scene", "closing"}
                for page in pages
            )
            if pages and scene_count > len(pages) // 2:
                errors.append("full-set-has-too-many-scene-pages")
            detail_composition_types = {
                page.get("composition_type")
                for page in pages
                if page.get("surface") == "detail"
            }
            if detail_composition_types and not detail_composition_types.intersection(
                {"detail", "diagram", "process", "comparison", "package", "trust"}
            ):
                errors.append("full-set-detail-needs-informational-composition")

    placement_by_id = {}
    if is_v8x:
        if uses_claim_contract and project.get("status") == "planned" and not str(
            project.get("plan_document", "")
        ).strip():
            errors.append("planned-project-requires-plan-document")

        product = project.get("product", {})
        for field in (
            "identity_lock",
            "source_diagnosis",
            "design_opportunities",
        ):
            value = product.get(field)
            if not isinstance(value, list) or not value:
                errors.append(f"product:missing-analysis-field:{field}")

        strategy = project.get("visual_direction", {})
        for field in (
            "positioning",
            "audience",
            "purchase_motivations",
            "purchase_barriers",
            "creative_concept",
            "message_hierarchy",
            "style",
            "palette",
            "typography",
            "layout_system",
            "consistency_rules",
        ):
            value = strategy.get(field)
            if value is None or value == "" or value == []:
                errors.append(f"visual-direction:missing-field:{field}")

        if is_v82:
            if target.get("delivery_scope") not in {
                "full_evidence",
                "evidence_safe",
            }:
                errors.append("target:invalid-delivery-scope")
            completeness = strategy.get("commercial_completeness")
            if completeness not in {"complete", "evidence_safe_limited"}:
                errors.append("visual-direction:invalid-commercial-completeness")
            copy_strategy = strategy.get("copy_strategy")
            required_copy_strategy_fields = (
                "principle",
                "fact_copy_rule",
                "safe_copy_pillars",
                "density_by_surface",
                "prohibited_inferences",
            )
            if not isinstance(copy_strategy, dict):
                errors.append("visual-direction:missing-copy-strategy")
            else:
                for field in required_copy_strategy_fields:
                    value = copy_strategy.get(field)
                    if value is None or value == "" or value == [] or value == {}:
                        errors.append(
                            f"visual-direction:copy-strategy-missing:{field}"
                        )

        research_ids = {
            item.get("id") for item in research if isinstance(item, dict)
        }
        if uses_claim_contract:
            platform_validation = target.get("platform_validation")
            if platform_validation not in {
                "design_recommendation",
                "backend_verified",
            }:
                errors.append("target:invalid-platform-validation-level")
            if (
                target.get("mode") == "platform_preflight"
                and platform_validation != "backend_verified"
            ):
                errors.append(
                    "platform-preflight-requires-backend-verified-specs"
                )
        placements = target.get("placements", [])
        if target.get("full_set") and len(placements) < 2:
            errors.append("full-set-requires-multiple-placement-specs")
        selected_sizes = {
            item.get("selected_size")
            for item in placements
            if isinstance(item, dict) and item.get("selected_size")
        }
        if target.get("full_set") and len(selected_sizes) < 2:
            errors.append("full-set-requires-multiple-selected-sizes")

        placement_ids = [
            item.get("id") for item in placements if isinstance(item, dict)
        ]
        placement_by_id = {
            item.get("id"): item
            for item in placements
            if isinstance(item, dict) and item.get("id")
        }
        for placement_id in placement_ids:
            if placement_id and placement_ids.count(placement_id) > 1:
                error = f"duplicate-placement-id:{placement_id}"
                if error not in errors:
                    errors.append(error)
        required_placement_fields = (
            "id",
            "name",
            "surface",
            "selected_size",
            "aspect_ratio",
            "quantity",
            "basis",
            "research_ids",
        )
        for placement in placements:
            if not isinstance(placement, dict):
                errors.append("target:invalid-placement")
                continue
            placement_id = placement.get("id", "unknown-placement")
            for field in required_placement_fields:
                value = placement.get(field)
                if value is None or value == "" or value == []:
                    errors.append(f"{placement_id}:missing-placement-field:{field}")
            if placement.get("surface") not in {
                "search_main",
                "gallery",
                "sku",
                "detail",
                "campaign",
            }:
                errors.append(
                    f"{placement_id}:unsupported-placement-surface:"
                    f"{placement.get('surface')}"
                )
            try:
                quantity = int(placement.get("quantity", 0))
                if quantity <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"{placement_id}:invalid-placement-quantity")
            for research_id in placement.get("research_ids", []):
                if research_id not in research_ids:
                    errors.append(
                        f"{placement_id}:unknown-placement-research:{research_id}"
                    )
            size = str(placement.get("selected_size", ""))
            try:
                width, height = map(int, size.split("x"))
                if width <= 0 or height <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"{placement_id}:invalid-selected-size:{size}")
                continue
            pixels = width * height
            uses_seedream_size_contract = is_v9 and generation_channel in {
                "codex_image_with_arkcli_fallback",
                "arkcli_seedream_5_pro",
            }
            uses_image2_size_contract = generation_channel != "arkcli_seedream_5_pro"
            if uses_seedream_size_contract:
                if max(width, height) / min(width, height) > 16:
                    errors.append(
                        f"{placement_id}:seedream-pro-size-ratio-too-extreme:{size}"
                    )
                if pixels < 921600 or pixels > 4624220:
                    errors.append(
                        f"{placement_id}:seedream-pro-size-pixel-count-invalid:{size}"
                    )
            if uses_image2_size_contract:
                if width % 16 or height % 16:
                    errors.append(
                        f"{placement_id}:image2-size-edge-must-be-multiple-of-16:{size}"
                    )
                if max(width, height) >= 3840:
                    errors.append(f"{placement_id}:image2-size-edge-too-long:{size}")
                if max(width, height) / min(width, height) > 3:
                    errors.append(f"{placement_id}:image2-size-ratio-too-extreme:{size}")
                if pixels < 655360 or pixels > 8294400:
                    errors.append(
                        f"{placement_id}:image2-size-pixel-count-invalid:{size}"
                    )
            divisor = math.gcd(width, height)
            actual_ratio = f"{width // divisor}:{height // divisor}"
            if placement.get("aspect_ratio") != actual_ratio:
                errors.append(
                    f"{placement_id}:aspect-ratio-does-not-match-size:"
                    f"{placement.get('aspect_ratio')}!={actual_ratio}"
                )

        if target.get("full_set") and str(target.get("platform", "")).lower() not in {
            "",
            "generic",
            "通用",
        }:
            platform_evidence = [
                item
                for item in research
                if isinstance(item, dict)
                and item.get("kind") == "platform_delivery"
                and item.get("source_type") in {"official", "user", "store_theme"}
                and item.get("id")
                and item.get("finding")
                and item.get("checked_at")
                and (item.get("source_type") != "official" or item.get("url"))
            ]
            if not platform_evidence:
                errors.append("platform-full-set-requires-delivery-evidence")

    asset_ids = {item.get("id") for item in project.get("source_assets", [])}
    facts = project.get("facts", [])
    fact_ids = {item.get("id") for item in facts}
    fact_by_id = {
        item.get("id"): item
        for item in facts
        if isinstance(item, dict) and item.get("id")
    }
    if uses_claim_contract:
        allowed_evidence_statuses = {
            "verified",
            "source_claim",
            "ambiguous",
            "missing",
        }
        for fact in facts:
            if not isinstance(fact, dict):
                errors.append("invalid-fact")
                continue
            fact_id = fact.get("id", "unknown-fact")
            if fact.get("evidence_status") not in allowed_evidence_statuses:
                errors.append(f"{fact_id}:invalid-evidence-status")
            if not str(fact.get("claim_scope", "")).strip():
                errors.append(f"{fact_id}:missing-claim-scope")
            if not isinstance(fact.get("approved_for_copy"), bool):
                errors.append(f"{fact_id}:missing-copy-approval")
            if (
                fact.get("evidence_status") in {"ambiguous", "missing"}
                and fact.get("approved_for_copy") is True
            ):
                errors.append(f"{fact_id}:ambiguous-fact-cannot-be-approved")
    generation_by_page = {
        item.get("page_id"): item for item in project.get("generation_log", [])
    }

    page_ids = [page.get("id") for page in pages]
    for page_id in page_ids:
        if page_id and page_ids.count(page_id) > 1:
            duplicate_error = f"duplicate-page-id:{page_id}"
            if duplicate_error not in errors:
                errors.append(duplicate_error)

    decision_by_id = {}
    if is_v8x:
        for asset in project.get("source_assets", []):
            asset_id = asset.get("id", "unknown-asset")
            for field in ("role", "proves", "limitations"):
                value = asset.get(field)
                if value is None or value == "" or value == []:
                    errors.append(f"{asset_id}:missing-asset-audit-field:{field}")

        decision_map = project.get("decision_map", [])
        if target.get("full_set") and len(decision_map) < 5:
            errors.append("full-set-requires-buyer-decision-map")
        decision_ids = [
            item.get("id") for item in decision_map if isinstance(item, dict)
        ]
        decision_by_id = {
            item.get("id"): item
            for item in decision_map
            if isinstance(item, dict) and item.get("id")
        }
        for decision_id in decision_ids:
            if decision_id and decision_ids.count(decision_id) > 1:
                error = f"duplicate-decision-id:{decision_id}"
                if error not in errors:
                    errors.append(error)

        high_priority = 0
        required_decision_fields = (
            "id",
            "question",
            "priority",
            "status",
            "basis",
            "fact_ids",
            "page_ids",
            "reason",
        )
        if uses_claim_contract:
            required_decision_fields = required_decision_fields + (
                "dimension",
                "claim_type",
            )
        if is_v82:
            required_decision_fields = required_decision_fields + (
                "blocking_scope",
                "safe_fallback",
            )
        allowed_dimensions = {
            "identity",
            "usage_fit",
            "benefit",
            "proof",
            "selection",
            "trust",
            "risk",
            "platform",
        }
        allowed_claim_types = {
            "product_fact",
            "platform_fact",
            "creative_simulation",
            "style_recommendation",
            "missing_fact",
            "scope_exclusion",
        }
        for decision in decision_map:
            if not isinstance(decision, dict):
                errors.append("invalid-buyer-decision")
                continue
            decision_id = decision.get("id", "unknown-decision")
            for field in required_decision_fields:
                if field not in decision:
                    errors.append(f"{decision_id}:missing-decision-field:{field}")
            if decision.get("priority") not in {"high", "medium", "low"}:
                errors.append(f"{decision_id}:unsupported-decision-priority")
            if decision.get("priority") == "high":
                high_priority += 1
            if decision.get("status") not in {"covered", "blocking", "out_of_scope"}:
                errors.append(f"{decision_id}:unsupported-decision-status")
            if decision.get("basis") not in {
                "visible",
                "user",
                "research",
                "model_inferred",
                "missing",
                "out_of_scope",
            }:
                errors.append(f"{decision_id}:unsupported-decision-basis")
            if uses_claim_contract:
                claim_type = decision.get("claim_type")
                if decision.get("dimension") not in allowed_dimensions:
                    errors.append(f"{decision_id}:unsupported-decision-dimension")
                if claim_type not in allowed_claim_types:
                    errors.append(f"{decision_id}:unsupported-claim-type")
                if (
                    claim_type == "product_fact"
                    and decision.get("basis") == "model_inferred"
                ):
                    errors.append(
                        f"{decision_id}:product-fact-cannot-use-model-inference"
                    )
                if (
                    claim_type in {"creative_simulation", "style_recommendation"}
                    and decision.get("basis") != "model_inferred"
                ):
                    errors.append(
                        f"{decision_id}:creative-claim-requires-model-inference-basis"
                    )
                if claim_type == "missing_fact" and decision.get("status") != "blocking":
                    errors.append(
                        f"{decision_id}:missing-fact-must-remain-blocking"
                    )
                if claim_type == "scope_exclusion" and decision.get("status") != "out_of_scope":
                    errors.append(
                        f"{decision_id}:scope-exclusion-must-be-out-of-scope"
                    )
                if decision.get("status") == "out_of_scope":
                    if decision.get("basis") != "out_of_scope":
                        errors.append(
                            f"{decision_id}:out-of-scope-requires-out-of-scope-basis"
                        )
                    if decision.get("scope_basis") not in {
                        "user_explicit",
                        "placement_not_required",
                    }:
                        errors.append(
                            f"{decision_id}:out-of-scope-requires-explicit-scope-basis"
                        )
                    if not str(decision.get("scope_ref", "")).strip():
                        errors.append(
                            f"{decision_id}:out-of-scope-requires-scope-ref"
                        )
                if is_v82:
                    blocking_scope = decision.get("blocking_scope")
                    if blocking_scope not in {
                        "none",
                        "claim",
                        "acceptance",
                        "project",
                    }:
                        errors.append(f"{decision_id}:invalid-blocking-scope")
                    if decision.get("status") == "blocking":
                        if blocking_scope == "none":
                            errors.append(
                                f"{decision_id}:blocking-decision-needs-scope"
                            )
                        if not str(decision.get("safe_fallback", "")).strip():
                            errors.append(
                                f"{decision_id}:blocking-decision-needs-safe-fallback"
                            )
                    elif blocking_scope != "none":
                        errors.append(
                            f"{decision_id}:nonblocking-decision-must-use-none-scope"
                        )
            if decision.get("status") == "covered" and not decision.get("page_ids"):
                errors.append(f"{decision_id}:covered-decision-requires-pages")
            if decision.get("basis") in {"visible", "user", "research"} and not decision.get(
                "fact_ids"
            ):
                errors.append(f"{decision_id}:evidence-backed-decision-requires-facts")
            for fact_id in decision.get("fact_ids", []):
                if fact_id not in fact_ids:
                    errors.append(f"{decision_id}:unknown-decision-fact:{fact_id}")
            for page_id in decision.get("page_ids", []):
                if page_id not in page_ids:
                    errors.append(f"{decision_id}:unknown-decision-page:{page_id}")
            if project.get("status") == "planned" and decision.get("status") == "blocking":
                if is_v81:
                    errors.append(
                        f"{decision_id}:planned-project-has-blocking-decision"
                    )
                elif is_v82:
                    blocking_scope = decision.get("blocking_scope")
                    if blocking_scope == "project":
                        errors.append(
                            f"{decision_id}:planned-project-has-project-blocker"
                        )
                    elif target.get("delivery_scope") != "evidence_safe":
                        errors.append(
                            f"{decision_id}:claim-blocker-requires-evidence-safe-scope"
                        )
                    elif project.get("visual_direction", {}).get(
                        "commercial_completeness"
                    ) != "evidence_safe_limited":
                        errors.append(
                            f"{decision_id}:claim-blocker-requires-limited-completeness"
                        )
                elif decision.get("priority") == "high":
                    errors.append(
                        f"{decision_id}:planned-project-has-blocking-high-priority-decision"
                    )
        if target.get("full_set") and high_priority < 3:
            errors.append("full-set-requires-at-least-3-high-priority-decisions")
        if uses_claim_contract and target.get("full_set"):
            dimensions = {
                decision.get("dimension")
                for decision in decision_map
                if isinstance(decision, dict)
            }
            for dimension in ("identity", "usage_fit", "proof", "selection", "trust"):
                if dimension not in dimensions:
                    errors.append(
                        f"full-set-missing-decision-dimension:{dimension}"
                    )

    required_page_fields = (
        "id",
        "role",
        "buyer_question",
        "size",
        "references",
        "fact_ids",
        "copy",
        "visual_brief",
        "prompt",
        "output",
    )
    if uses_surface_contract:
        required_page_fields = ("id", "surface") + required_page_fields[1:]
    if uses_composition_contract:
        required_page_fields = required_page_fields + ("composition_type",)
    if is_v8x:
        required_page_fields = required_page_fields + ("placement_id", "decision_ids")
    if uses_claim_contract:
        required_page_fields = required_page_fields + (
            "primary_decision_id",
            "unique_evidence",
            "has_factual_claims",
            "claim_fact_ids",
        )

    for page in pages:
        page_id = page.get("id", "unknown-page")
        for field in required_page_fields:
            if field not in page:
                errors.append(f"{page_id}:missing-page-field:{field}")
        if uses_composition_contract:
            for field in ("role", "buyer_question", "size", "visual_brief", "prompt"):
                if field in page and not str(page.get(field, "")).strip():
                    errors.append(f"{page_id}:empty-page-field:{field}")
            if "references" in page and not page.get("references"):
                errors.append(f"{page_id}:empty-page-field:references")
        if uses_surface_contract and page.get("surface") not in {
            "search_main",
            "gallery",
            "sku",
            "detail",
            "campaign",
        }:
            if page.get("surface") is not None:
                errors.append(f"{page_id}:unsupported-surface:{page.get('surface')}")
        if uses_composition_contract and page.get("composition_type") not in allowed_composition_types:
            if page.get("composition_type") is not None:
                errors.append(
                    f"{page_id}:unsupported-composition-type:"
                    f"{page.get('composition_type')}"
                )
        if (
            uses_composition_contract
            and not is_v82
            and page.get("copy")
            and page.get("composition_type")
            in {"detail", "diagram", "process", "comparison", "package", "trust"}
            and not page.get("fact_ids")
        ):
            errors.append(f"{page_id}:informational-copy-requires-facts")
        if uses_surface_contract:
            try:
                page_width, page_height = map(
                    int, str(page.get("size", "")).split("x")
                )
                if page_width <= 0 or page_height <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"{page_id}:invalid-page-size:{page.get('size')}")
        for reference in page.get("references", []):
            if reference not in asset_ids:
                errors.append(f"{page_id}:unknown-reference:{reference}")
        for fact_id in page.get("fact_ids", []):
            if fact_id not in fact_ids:
                errors.append(f"{page_id}:unknown-fact:{fact_id}")
        if is_v8x:
            placement_id = page.get("placement_id")
            placement = placement_by_id.get(placement_id)
            if not placement:
                errors.append(f"{page_id}:unknown-placement:{placement_id}")
            else:
                if page.get("surface") != placement.get("surface"):
                    errors.append(f"{page_id}:surface-does-not-match-placement")
                if page.get("size") != placement.get("selected_size"):
                    errors.append(
                        f"{page_id}:size-does-not-match-placement:{page.get('size')}"
                    )
            linked_decisions = page.get("decision_ids", [])
            if not linked_decisions:
                errors.append(f"{page_id}:missing-decision-link")
            for decision_id in linked_decisions:
                if decision_id not in decision_by_id:
                    errors.append(f"{page_id}:unknown-decision:{decision_id}")
            if uses_claim_contract:
                primary_decision_id = page.get("primary_decision_id")
                if primary_decision_id not in linked_decisions:
                    errors.append(
                        f"{page_id}:primary-decision-not-linked:{primary_decision_id}"
                    )
                if not str(page.get("unique_evidence", "")).strip():
                    errors.append(f"{page_id}:missing-unique-evidence")
                has_factual_claims = page.get("has_factual_claims")
                claim_fact_ids = page.get("claim_fact_ids", [])
                if not isinstance(has_factual_claims, bool):
                    errors.append(f"{page_id}:invalid-factual-claim-flag")
                if has_factual_claims is True and not claim_fact_ids:
                    errors.append(f"{page_id}:factual-copy-requires-claim-facts")
                for claim_fact_id in claim_fact_ids:
                    if claim_fact_id not in fact_ids:
                        errors.append(
                            f"{page_id}:unknown-claim-fact:{claim_fact_id}"
                        )
                        continue
                    if claim_fact_id not in page.get("fact_ids", []):
                        errors.append(
                            f"{page_id}:claim-fact-not-in-page-facts:{claim_fact_id}"
                        )
                    if not fact_by_id.get(claim_fact_id, {}).get(
                        "approved_for_copy", False
                    ):
                        errors.append(
                            f"{page_id}:claim-fact-not-approved:{claim_fact_id}"
                        )

        if is_v82:
            copy_value = page.get("copy")
            if not isinstance(copy_value, dict):
                errors.append(f"{page_id}:copy-must-be-structured")
            elif not copy_value:
                if page.get("surface") != "search_main":
                    errors.append(f"{page_id}:non-search-page-requires-copy-system")
            else:
                headline = copy_value.get("headline")
                subheadline = copy_value.get("subheadline")
                supporting_points = copy_value.get("supporting_points")
                if not isinstance(headline, dict) or not str(
                    headline.get("text", "")
                ).strip():
                    errors.append(f"{page_id}:commercial-copy-needs-headline")
                if not isinstance(subheadline, dict) or not str(
                    subheadline.get("text", "")
                ).strip():
                    errors.append(f"{page_id}:commercial-copy-needs-subheadline")
                if not isinstance(supporting_points, list) or len(
                    supporting_points
                ) < 2:
                    errors.append(
                        f"{page_id}:commercial-copy-needs-supporting-content"
                    )

                blocks = _copy_blocks(copy_value)
                declared_claim_facts = set()
                has_safe_copy = False
                has_fact_copy = False
                for block_index, block in enumerate(blocks, start=1):
                    text = block.get("text")
                    kind = block.get("kind")
                    block_fact_ids = block.get("fact_ids")
                    if not isinstance(text, str) or not text.strip():
                        errors.append(
                            f"{page_id}:copy-block-{block_index}-missing-text"
                        )
                    elif _contains_copy_placeholder(text):
                        error = f"{page_id}:commercial-copy-contains-placeholder"
                        if error not in errors:
                            errors.append(error)
                    if kind not in ALLOWED_COPY_KINDS:
                        errors.append(
                            f"{page_id}:copy-block-{block_index}-invalid-kind:{kind}"
                        )
                    if not isinstance(block_fact_ids, list):
                        errors.append(
                            f"{page_id}:copy-block-{block_index}-fact-ids-must-be-list"
                        )
                        block_fact_ids = []
                    if kind in SAFE_COPY_KINDS:
                        has_safe_copy = True
                        if block_fact_ids:
                            errors.append(
                                f"{page_id}:safe-copy-must-not-claim-product-facts"
                            )
                    if kind in FACT_COPY_KINDS:
                        has_fact_copy = True
                        if not block_fact_ids:
                            errors.append(f"{page_id}:fact-copy-needs-fact-ids")
                        for block_fact_id in block_fact_ids:
                            declared_claim_facts.add(block_fact_id)
                            if block_fact_id not in page.get("fact_ids", []):
                                errors.append(
                                    f"{page_id}:copy-fact-not-in-page-facts:{block_fact_id}"
                                )
                            if not fact_by_id.get(block_fact_id, {}).get(
                                "approved_for_copy", False
                            ):
                                errors.append(
                                    f"{page_id}:copy-fact-not-approved:{block_fact_id}"
                                )
                if not has_safe_copy:
                    errors.append(f"{page_id}:copy-system-needs-safe-commercial-layer")
                if page.get("has_factual_claims") is not has_fact_copy:
                    errors.append(f"{page_id}:factual-claim-flag-does-not-match-copy")
                if set(page.get("claim_fact_ids", [])) != declared_claim_facts:
                    errors.append(f"{page_id}:claim-facts-do-not-match-copy-blocks")

            blueprint = page.get("visual_brief")
            if not isinstance(blueprint, dict):
                errors.append(f"{page_id}:visual-brief-must-be-layout-blueprint")
            else:
                for field in LAYOUT_BLUEPRINT_FIELDS:
                    value = blueprint.get(field)
                    if value is None or value == "" or value == []:
                        errors.append(f"{page_id}:layout-blueprint-missing:{field}")
                content_modules = set(blueprint.get("content_modules", []))
                informational_modules = {
                    "macro_proof",
                    "callout",
                    "material_proof",
                    "structure_proof",
                    "decision_diagram",
                    "spec_diagram",
                    "size_diagram",
                    "fit_diagram",
                    "buyer_guidance",
                    "process_steps",
                    "operation_steps",
                    "comparison_matrix",
                    "package_inventory",
                    "trust_evidence",
                    "service_evidence",
                }
                if (
                    page.get("composition_type")
                    in {"detail", "diagram", "process", "comparison", "package", "trust"}
                    and not content_modules.intersection(informational_modules)
                ):
                    errors.append(
                        f"{page_id}:{page.get('composition_type')}-composition-"
                        "lacks-informational-module"
                    )

                prompt_text = str(page.get("prompt", ""))
                for field in LAYOUT_BLUEPRINT_FIELDS:
                    value = blueprint.get(field)
                    if isinstance(value, list):
                        represented = bool(value) and all(
                            str(item) in prompt_text for item in value
                        )
                    else:
                        represented = bool(str(value or "").strip()) and str(
                            value
                        ) in prompt_text
                    if not represented:
                        errors.append(
                            f"{page_id}:prompt-missing-blueprint-field:{field}"
                        )

            prompt = str(page.get("prompt", ""))
            for section in PROMPT_SECTIONS:
                if section not in prompt:
                    errors.append(f"{page_id}:prompt-missing-section:{section}")

        for copy_text in _copy_texts(page.get("copy", [])):
            if copy_text not in page.get("prompt", ""):
                errors.append(f"{page_id}:copy-not-in-prompt:{copy_text}")

        if (
            target.get("mode") == "regulated"
            and page.get("copy")
            and not page.get("fact_ids")
        ):
            errors.append(f"{page_id}:regulated-copy-requires-facts")

        if (
            str(target.get("platform", "")).lower() == "amazon"
            and (
                (uses_surface_contract and page.get("surface") == "search_main")
                or (not uses_surface_contract and page.get("role") == "search_main")
            )
            and page.get("copy")
        ):
            errors.append(f"{page_id}:amazon-search-main-must-be-copy-free")

        if project.get("status") in {"review", "accepted"}:
            if page_id not in generation_by_page:
                errors.append(f"{page_id}:missing-generation-record")

    if is_v82:
        for placement_id, placement in placement_by_id.items():
            try:
                declared_quantity = int(placement.get("quantity", 0))
            except (TypeError, ValueError):
                continue
            bound_page_count = sum(
                page.get("placement_id") == placement_id for page in pages
            )
            if declared_quantity != bound_page_count:
                errors.append(
                    f"{placement_id}:quantity-does-not-match-pages:"
                    f"{declared_quantity}!={bound_page_count}"
                )

        commercial_lines = []
        for page in pages:
            copy_value = page.get("copy")
            if not isinstance(copy_value, dict):
                continue
            for field in ("headline", "subheadline"):
                block = copy_value.get(field)
                if isinstance(block, dict):
                    text = str(block.get("text", "")).strip()
                    if text:
                        commercial_lines.append(text)
            for block in copy_value.get("supporting_points", []):
                if isinstance(block, dict):
                    text = str(block.get("text", "")).strip()
                    if text:
                        commercial_lines.append(text)
        for text in set(commercial_lines):
            count = commercial_lines.count(text)
            if len(text) >= 8 and count >= 3:
                errors.append(f"commercial-copy-repetition:{text}:{count}")

    if uses_claim_contract:
        unique_evidence_values = [
            str(page.get("unique_evidence", "")).strip()
            for page in pages
            if str(page.get("unique_evidence", "")).strip()
        ]
        for evidence in unique_evidence_values:
            if unique_evidence_values.count(evidence) > 1:
                error = f"duplicate-page-unique-evidence:{evidence}"
                if error not in errors:
                    errors.append(error)
        if project.get("status") == "planned" and target.get("full_set"):
            primary_decisions = [
                page.get("primary_decision_id") for page in pages
            ]
            for decision_id in set(primary_decisions) - {None}:
                count = primary_decisions.count(decision_id)
                if count > 2:
                    errors.append(
                        f"planned-full-set-repeats-primary-decision:"
                        f"{decision_id}:{count}"
                    )

    common_generation_fields = (
        "tool",
        "model",
        "generated_at",
        "prompt",
        "source_asset_ids",
        "output",
        "output_sha256",
        "post_processing",
    )
    if is_v82:
        common_generation_fields = common_generation_fields + (
            "attempt",
            "prompt_sha256",
            "plan_sha256",
        )

    confirmation = project.get("confirmation", {})
    confirmed_at = _parse_datetime(confirmation.get("confirmed_at"))
    if is_v82 and project.get("status") in {"generating", "review", "accepted"}:
        if not str(confirmation.get("plan_sha256", "")).strip():
            errors.append("confirmation:missing-plan-sha256")
        if not str(confirmation.get("execution_manifest_sha256", "")).strip():
            errors.append("confirmation:missing-execution-manifest-sha256")
        elif confirmation.get("execution_manifest_sha256") != _execution_manifest_sha256(
            project
        ):
            errors.append("confirmation:execution-manifest-changed-after-confirmation")
        if confirmed_at is None:
            errors.append("confirmation:invalid-confirmed-at")

    for record in project.get("generation_log", []):
        page_id = record.get("page_id", "unknown-page")
        is_ark_record = is_v9 and record.get("tool") == "arkcli.+gen"
        required_generation_fields = common_generation_fields + (
            (
                "status",
                "arkcli_version",
                "resource_id",
                "watermark",
            )
            if is_ark_record
            else ("request_id",)
        )
        for field in required_generation_fields:
            value = record.get(field)
            if value is None or value == "":
                errors.append(f"{page_id}:incomplete-generation-record:{field}")
        if record.get("post_processing"):
            errors.append(f"{page_id}:consumer-post-processing-forbidden")
        for source_asset_id in record.get("source_asset_ids", []):
            if source_asset_id not in asset_ids:
                errors.append(f"{page_id}:unknown-generation-source:{source_asset_id}")
        if is_v9 and generation_channel == "arkcli_seedream_5_pro":
            if not is_ark_record:
                errors.append(f"{page_id}:final-image-tool-must-be-arkcli-gen")
        elif is_v9 and generation_channel == "codex_image":
            if is_ark_record:
                errors.append(f"{page_id}:final-image-tool-must-be-codex-imagegen")
        elif is_v9 and generation_channel == "codex_image_with_arkcli_fallback":
            if is_ark_record:
                fallback = record.get("fallback_from")
                if not isinstance(fallback, dict):
                    errors.append(f"{page_id}:arkcli-fallback-requires-codex-failure")
                else:
                    for field in (
                        "channel",
                        "tool",
                        "attempted_at",
                        "error_type",
                        "error_summary",
                    ):
                        value = fallback.get(field)
                        if not isinstance(value, str) or not value.strip():
                            errors.append(
                                f"{page_id}:incomplete-fallback-record:{field}"
                            )
                    if fallback.get("channel") != "codex_image":
                        errors.append(f"{page_id}:fallback-source-must-be-codex-image")
                    if not isinstance(fallback.get("tool"), str) or fallback.get("tool") not in {
                        "codex_image_gen",
                        "codex_image_edit",
                        "image_gen.imagegen",
                    }:
                        errors.append(f"{page_id}:invalid-fallback-source-tool")
                    if not isinstance(fallback.get("error_type"), str) or fallback.get("error_type") not in {
                        "tool_unavailable",
                        "request_failed",
                        "no_image_output",
                    }:
                        errors.append(f"{page_id}:invalid-fallback-trigger")
                    fallback_at = _parse_datetime(fallback.get("attempted_at"))
                    if fallback_at is None:
                        errors.append(f"{page_id}:invalid-fallback-attempted-at")
                    else:
                        generated_at = _parse_datetime(record.get("generated_at"))
                        if generated_at is not None and generated_at <= fallback_at:
                            errors.append(
                                f"{page_id}:fallback-generation-must-follow-codex-failure"
                            )

        if is_ark_record:
            if record.get("model") != "doubao-seedream-5-0-pro-260628":
                errors.append(f"{page_id}:final-image-model-must-be-seedream-5-pro")
            if record.get("status") != "succeeded":
                errors.append(f"{page_id}:arkcli-generation-must-succeed")
            resource_id = str(record.get("resource_id", ""))
            if resource_id != "doubao-seedream-5-0-pro-260628" and not resource_id.startswith(
                "ep-"
            ):
                errors.append(f"{page_id}:invalid-arkcli-generation-resource")
            if record.get("watermark") is not False:
                errors.append(f"{page_id}:arkcli-watermark-must-be-false")
        elif record.get("tool") not in {
            "codex_image_gen",
            "codex_image_edit",
            "image_gen.imagegen",
        }:
            errors.append(f"{page_id}:final-image-tool-must-be-codex-imagegen")
        page_prompt = next(
            (page.get("prompt") for page in pages if page.get("id") == page_id), None
        )
        page_output = next(
            (page.get("output") for page in pages if page.get("id") == page_id), None
        )
        if page_prompt is not None and record.get("prompt") != page_prompt:
            errors.append(f"{page_id}:generation-prompt-does-not-match-page")
        if page_output is not None and record.get("output") != page_output:
            errors.append(f"{page_id}:generation-output-does-not-match-page")

        if is_v82:
            try:
                attempt = int(record.get("attempt", 0))
                if attempt <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"{page_id}:invalid-generation-attempt")
            generated_at = _parse_datetime(record.get("generated_at"))
            if generated_at is None:
                errors.append(f"{page_id}:invalid-generated-at")
            elif confirmed_at is not None and generated_at <= confirmed_at:
                errors.append(f"{page_id}:generation-must-follow-confirmation")
            if page_prompt is not None:
                prompt_hash = hashlib.sha256(page_prompt.encode("utf-8")).hexdigest()
                if record.get("prompt_sha256") != prompt_hash:
                    errors.append(f"{page_id}:prompt-sha256-mismatch")
            if record.get("plan_sha256") != confirmation.get("plan_sha256"):
                errors.append(f"{page_id}:generation-plan-sha256-mismatch")

        if project_dir and record.get("output"):
            output_path = Path(project_dir) / record["output"]
            if not output_path.is_file():
                errors.append(f"{page_id}:missing-output-file")
                continue
            actual_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
            if record.get("output_sha256") != actual_hash:
                errors.append(f"{page_id}:output-sha256-mismatch")
            expected_size = next(
                (page.get("size") for page in pages if page.get("id") == page_id), None
            )
            if expected_size:
                try:
                    from PIL import Image
                except ImportError:
                    errors.append("pillow-required-for-image-validation")
                    continue
                try:
                    expected_width, expected_height = map(int, expected_size.split("x"))
                    with Image.open(output_path) as image:
                        actual_width, actual_height = image.size
                    if (actual_width, actual_height) != (
                        expected_width,
                        expected_height,
                    ):
                        errors.append(
                            f"{page_id}:output-size-mismatch:"
                            f"{actual_width}x{actual_height}!={expected_size}"
                        )
                except (OSError, ValueError):
                    errors.append(f"{page_id}:invalid-image-output")

    if project.get("status") == "accepted":
        review = project.get("review", {})
        reviewer_type = review.get("reviewer_type")
        if review.get("status") != "accepted":
            errors.append("accepted-project-requires-accepted-review-status")
        if reviewer_type not in {"user", "independent"}:
            errors.append("accepted-project-requires-user-or-independent-review")
        if not review.get("contact_sheet") or not review.get("contact_sheet_sha256"):
            errors.append("accepted-project-requires-contact-sheet")
        page_review = {
            item.get("page_id"): item.get("status") for item in review.get("pages", [])
        }
        for page in pages:
            if page_review.get(page.get("id")) != "pass":
                errors.append(f"{page.get('id', 'unknown-page')}:accepted-page-requires-pass-review")

    if project.get("status") in {"review", "accepted"}:
        review = project.get("review", {})
        if uses_composition_contract and target.get("full_set"):
            set_checks = review.get("set_checks", {})
            required_set_checks = (
                "commercial_coverage",
                "surface_difference",
                "composition_diversity",
                "text_integration",
                "product_consistency",
            )
            if is_v82:
                required_set_checks = required_set_checks + (
                    "copy_richness",
                    "buyer_value",
                    "prompt_fidelity",
                    "claim_safety",
                )
            for check_name in required_set_checks:
                check = set_checks.get(check_name)
                if not isinstance(check, dict):
                    errors.append(f"review:missing-set-check:{check_name}")
                    continue
                if check.get("status") != "pass":
                    errors.append(f"review:set-check-failed:{check_name}")
                if not check.get("evidence"):
                    errors.append(f"review:set-check-missing-evidence:{check_name}")
        if project.get("status") == "review" and (
            review.get("status") != "manual_review"
            or review.get("reviewer_type") not in {"same_agent", "user", "independent"}
        ):
            errors.append("review-stage-requires-manual-review-metadata")
        if not review.get("contact_sheet") or not review.get("contact_sheet_sha256"):
            errors.append("review-requires-contact-sheet")
        page_review = {
            item.get("page_id"): item.get("status") for item in review.get("pages", [])
        }
        for page in pages:
            if page.get("id") not in page_review:
                errors.append(f"{page.get('id', 'unknown-page')}:review-requires-page-result")
            elif page_review.get(page.get("id")) != "pass":
                errors.append(f"{page.get('id', 'unknown-page')}:visual-review-failed")
        if is_v82:
            required_score_names = (
                "commercial_value",
                "copy_hierarchy",
                "product_consistency",
                "prompt_fidelity",
                "visual_polish",
            )
            review_by_page = {
                item.get("page_id"): item
                for item in review.get("pages", [])
                if isinstance(item, dict)
            }
            for page in pages:
                page_id = page.get("id", "unknown-page")
                page_result = review_by_page.get(page_id, {})
                scores = page_result.get("scores")
                if not isinstance(scores, dict) or any(
                    name not in scores for name in required_score_names
                ):
                    errors.append(f"{page_id}:review-requires-quality-scores")
                else:
                    for score_name in required_score_names:
                        score = scores.get(score_name)
                        if not isinstance(score, int) or not 1 <= score <= 5:
                            errors.append(
                                f"{page_id}:invalid-review-score:{score_name}"
                            )
                        elif page_result.get("status") == "pass" and score < 4:
                            errors.append(
                                f"{page_id}:pass-review-score-too-low:{score_name}"
                            )
                evidence = str(page_result.get("evidence", "")).strip()
                generic_evidence = {
                    "人工原图复核通过",
                    "原图复核通过",
                    "全部通过",
                    "视觉复核通过",
                }
                if len(evidence) < 30 or evidence in generic_evidence:
                    errors.append(f"{page_id}:review-evidence-too-generic")
        if project_dir and review.get("contact_sheet"):
            contact_path = Path(project_dir) / review["contact_sheet"]
            if not contact_path.is_file():
                errors.append("missing-contact-sheet-file")
            else:
                contact_hash = hashlib.sha256(contact_path.read_bytes()).hexdigest()
                if review.get("contact_sheet_sha256") != contact_hash:
                    errors.append("contact-sheet-sha256-mismatch")

    if project_dir:
        project_dir = Path(project_dir)
        if uses_claim_contract and str(project.get("plan_document", "")).strip():
            plan_path = (project_dir / project["plan_document"]).resolve()
            try:
                plan_path.relative_to(project_dir.resolve())
            except ValueError:
                errors.append("invalid-plan-document-path")
            else:
                if not plan_path.is_file():
                    errors.append("missing-plan-document-file")
                elif is_v82 and project.get("status") in {
                    "generating",
                    "review",
                    "accepted",
                }:
                    plan_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest()
                    if project.get("confirmation", {}).get("plan_sha256") != plan_hash:
                        errors.append("confirmation:plan-changed-after-confirmation")
        for asset in project.get("source_assets", []):
            asset_id = asset.get("id", "unknown-asset")
            source_path = project_dir / asset.get("file", "")
            if not source_path.is_file():
                errors.append(f"{asset_id}:missing-source-file")
                continue
            source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
            if asset.get("sha256") != source_hash:
                errors.append(f"{asset_id}:source-sha256-mismatch")
        forbidden_roots = {"base", "layouts", "copy-layout"}
        for path in sorted(project_dir.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(project_dir)
            if relative.parts[0] in forbidden_roots or path.name.startswith("layout-"):
                errors.append(f"forbidden-production-artifact:{relative.as_posix()}")

    return errors
