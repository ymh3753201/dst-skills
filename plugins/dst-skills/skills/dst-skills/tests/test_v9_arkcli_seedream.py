import copy
import hashlib
import json
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(SKILL_DIR / "scripts"))

from project_contract import _execution_manifest_sha256, validate_project


def current_project():
    return json.loads(
        (SKILL_DIR / "templates" / "project_template.json").read_text(
            encoding="utf-8"
        )
    )


def ark_generation_record(page, fallback=False):
    record = {
        "page_id": page["id"],
        "attempt": 1,
        "tool": "arkcli.+gen",
        "model": "doubao-seedream-5-0-pro-260628",
        "arkcli_version": "1.0.18",
        "resource_id": "doubao-seedream-5-0-pro-260628",
        "watermark": False,
        "status": "succeeded",
        "generated_at": "2026-08-21T16:00:00+08:00",
        "prompt": page["prompt"],
        "prompt_sha256": hashlib.sha256(page["prompt"].encode("utf-8")).hexdigest(),
        "plan_sha256": "b" * 64,
        "source_asset_ids": page["references"],
        "output": page["output"],
        "output_sha256": "a" * 64,
        "post_processing": [],
    }
    if fallback:
        record["fallback_from"] = {
            "channel": "codex_image",
            "tool": "image_gen.imagegen",
            "attempted_at": "2026-08-21T15:55:00+08:00",
            "error_type": "request_failed",
            "error_summary": "image generation request failed without an output",
        }
    return record


def codex_generation_record(page):
    return {
        "page_id": page["id"],
        "attempt": 1,
        "tool": "image_gen.imagegen",
        "model": "not_returned_by_imagegen_tool",
        "request_id": "not_returned_by_imagegen_tool",
        "generated_at": "2026-08-21T16:00:00+08:00",
        "prompt": page["prompt"],
        "prompt_sha256": hashlib.sha256(page["prompt"].encode("utf-8")).hexdigest(),
        "plan_sha256": "b" * 64,
        "source_asset_ids": page["references"],
        "output": page["output"],
        "output_sha256": "a" * 64,
        "post_processing": [],
    }


class V90ArkCliSeedreamTests(unittest.TestCase):
    def test_current_template_uses_v9_contract(self):
        project = current_project()

        self.assertEqual(project["schema_version"], "9.0")
        self.assertEqual(project["skill_version"], "9.0.0")
        self.assertEqual(
            project["generation_channel"],
            "codex_image_with_arkcli_fallback",
        )
        self.assertEqual(validate_project(project), [])

    def test_v9_codex_channel_preserves_image2_size_contract(self):
        project = current_project()
        placement = project["target"]["placements"][1]
        placement["selected_size"] = "1080x1440"
        placement["aspect_ratio"] = "3:4"
        for page in project["pages"]:
            if page["placement_id"] == placement["id"]:
                page["size"] = "1080x1440"

        errors = validate_project(project)

        self.assertIn(
            "portrait-main:image2-size-edge-must-be-multiple-of-16:1080x1440",
            errors,
        )

    def test_v9_ark_channel_accepts_seedream_sizes_without_image2_rule(self):
        project = current_project()
        project["generation_channel"] = "arkcli_seedream_5_pro"
        placement = project["target"]["placements"][1]
        placement["selected_size"] = "1080x1440"
        placement["aspect_ratio"] = "3:4"
        for page in project["pages"]:
            if page["placement_id"] == placement["id"]:
                page["size"] = "1080x1440"

        errors = validate_project(project)

        self.assertFalse(
            any("image2-size-edge-must-be-multiple-of-16" in error for error in errors),
            errors,
        )
        self.assertFalse(
            any("seedream-pro-size" in error for error in errors),
            errors,
        )

    def test_v9_rejects_seedream_pro_size_below_minimum_pixels(self):
        project = current_project()
        placement = project["target"]["placements"][0]
        placement["selected_size"] = "800x800"
        for page in project["pages"]:
            if page["placement_id"] == placement["id"]:
                page["size"] = "800x800"

        errors = validate_project(project)

        self.assertIn(
            "square-main:seedream-pro-size-pixel-count-invalid:800x800",
            errors,
        )

    def test_default_policy_requires_size_supported_by_both_channels(self):
        project = current_project()
        placement = project["target"]["placements"][0]
        placement["selected_size"] = "1024x768"
        placement["aspect_ratio"] = "4:3"
        for page in project["pages"]:
            if page["placement_id"] == placement["id"]:
                page["size"] = "1024x768"

        self.assertIn(
            "square-main:seedream-pro-size-pixel-count-invalid:1024x768",
            validate_project(project),
        )

        project["generation_channel"] = "codex_image"
        self.assertNotIn(
            "square-main:seedream-pro-size-pixel-count-invalid:1024x768",
            validate_project(project),
        )

    def test_v9_codex_channel_accepts_original_generation_record(self):
        project = current_project()
        page = copy.deepcopy(project["pages"][0])
        page["output"] = "images/page-01.png"
        project["pages"][0] = page
        project["confirmation"]["plan_sha256"] = "b" * 64
        project["generation_log"] = [codex_generation_record(page)]

        self.assertEqual(validate_project(project), [])

        project["generation_log"][0] = ark_generation_record(page)
        errors = validate_project(project)
        self.assertIn("page-01:arkcli-fallback-requires-codex-failure", errors)

        project["generation_log"][0] = ark_generation_record(page, fallback=True)
        self.assertEqual(validate_project(project), [])

    def test_v82_project_rejects_ark_generation_record(self):
        project = current_project()
        project["schema_version"] = "8.2"
        project["skill_version"] = "8.2.0"
        project.pop("generation_channel")
        page = project["pages"][0]
        page["output"] = "images/page-01.png"
        project["confirmation"]["plan_sha256"] = "b" * 64
        project["generation_log"] = [ark_generation_record(page)]

        self.assertIn(
            "page-01:final-image-tool-must-be-codex-imagegen",
            validate_project(project),
        )

    def test_v9_ark_channel_requires_arkcli_and_exact_pro_model(self):
        project = current_project()
        project["generation_channel"] = "arkcli_seedream_5_pro"
        page = copy.deepcopy(project["pages"][0])
        page["output"] = "images/page-01.png"
        project["pages"][0] = page
        project["confirmation"]["plan_sha256"] = "b" * 64
        record = ark_generation_record(page)
        project["generation_log"] = [record]

        self.assertEqual(validate_project(project), [])

        project["generation_log"][0]["tool"] = "image_gen.imagegen"
        errors = validate_project(project)

        self.assertIn("page-01:final-image-tool-must-be-arkcli-gen", errors)

        project["generation_log"][0] = ark_generation_record(page)
        project["generation_log"][0]["model"] = "doubao-seedream-5-0-260128"
        errors = validate_project(project)
        self.assertIn("page-01:final-image-model-must-be-seedream-5-pro", errors)

    def test_v9_generation_record_rejects_watermark_and_unknown_resource(self):
        project = current_project()
        project["generation_channel"] = "arkcli_seedream_5_pro"
        page = copy.deepcopy(project["pages"][0])
        page["output"] = "images/page-01.png"
        project["pages"][0] = page
        project["confirmation"]["plan_sha256"] = "b" * 64
        record = ark_generation_record(page)
        record["watermark"] = True
        record["resource_id"] = "doubao-seedream-5-0-260128"
        project["generation_log"] = [record]

        errors = validate_project(project)

        self.assertIn("page-01:arkcli-watermark-must-be-false", errors)
        self.assertIn("page-01:invalid-arkcli-generation-resource", errors)

    def test_default_policy_rejects_quality_issue_as_fallback_trigger(self):
        project = current_project()
        page = copy.deepcopy(project["pages"][0])
        page["output"] = "images/page-01.png"
        project["pages"][0] = page
        project["confirmation"]["plan_sha256"] = "b" * 64
        record = ark_generation_record(page, fallback=True)
        record["fallback_from"]["error_type"] = "visual_quality_failed"
        project["generation_log"] = [record]

        self.assertIn(
            "page-01:invalid-fallback-trigger",
            validate_project(project),
        )

        record = ark_generation_record(page, fallback=True)
        record["fallback_from"]["attempted_at"] = "2026-08-21T16:05:00+08:00"
        project["generation_log"] = [record]
        self.assertIn(
            "page-01:fallback-generation-must-follow-codex-failure",
            validate_project(project),
        )

    def test_v9_rejects_unknown_channel_and_binds_channel_to_confirmation(self):
        project = current_project()
        project["generation_channel"] = "unknown"
        self.assertIn(
            "unsupported-generation-channel:unknown",
            validate_project(project),
        )

        project = current_project()
        codex_hash = _execution_manifest_sha256(project)
        project["status"] = "generating"
        project["confirmation"].update(
            {
                "status": "confirmed",
                "confirmed_at": "2026-08-21T15:00:00+08:00",
                "method": "user_message",
                "plan_sha256": "b" * 64,
                "execution_manifest_sha256": codex_hash,
            }
        )
        self.assertNotIn(
            "confirmation:execution-manifest-changed-after-confirmation",
            validate_project(project),
        )
        project["generation_channel"] = "arkcli_seedream_5_pro"
        self.assertNotEqual(codex_hash, _execution_manifest_sha256(project))
        self.assertIn(
            "confirmation:execution-manifest-changed-after-confirmation",
            validate_project(project),
        )

    def test_malformed_channel_and_fallback_return_errors(self):
        project = current_project()
        project["generation_channel"] = ["arkcli_seedream_5_pro"]
        self.assertIn(
            "unsupported-generation-channel:['arkcli_seedream_5_pro']",
            validate_project(project),
        )

        project = current_project()
        page = project["pages"][0]
        page["output"] = "images/page-01.png"
        project["confirmation"]["plan_sha256"] = "b" * 64
        record = ark_generation_record(page, fallback=True)
        record["fallback_from"]["error_summary"] = ["request failed"]
        project["generation_log"] = [record]
        self.assertIn(
            "page-01:incomplete-fallback-record:error_summary",
            validate_project(project),
        )

    def test_skill_documents_arkcli_three_step_workflow_and_single_image_limit(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        reference = (SKILL_DIR / "references" / "arkcli_seedream.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "arkcli auth status",
            "arkcli resources list --modality image",
            "arkcli resources resolve <ep-id>",
            "arkcli models get doubao-seedream-5-0-pro-260628",
            "arkcli +gen",
            "每页单独调用一次",
            "Platform profile 选中 Endpoint 后必须",
            "--watermark=false",
        ):
            self.assertIn(phrase, skill)
        self.assertIn("`codex_image_with_arkcli_fallback`：默认值", skill)
        self.assertIn("openai_image_capability.md", skill)
        self.assertIn("最多 10 张", reference)
        self.assertIn("不支持 `sequential_image_generation`", reference)
        self.assertIn("不能证明 `+gen`", reference)
        self.assertIn("服务端会使用 `watermark=true` 默认值", reference)


if __name__ == "__main__":
    unittest.main()
