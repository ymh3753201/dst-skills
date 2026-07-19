import importlib.util
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SKILL_DIR = Path(__file__).resolve().parents[1]


def load_script(name):
    path = SKILL_DIR / "scripts" / name
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(f"dst_v7_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.path.pop(0)
    return module


class V7ToolTests(unittest.TestCase):
    def copy_skill(self):
        temp_root = Path(tempfile.mkdtemp(prefix="dst-v7-release-"))
        self.addCleanup(shutil.rmtree, temp_root, True)
        skill_copy = temp_root / "dst-skills"
        shutil.copytree(SKILL_DIR, skill_copy)
        return skill_copy

    def test_contact_sheet_script_exposes_builder(self):
        module = load_script("build_contact_sheet.py")

        self.assertTrue(callable(getattr(module, "build_contact_sheet", None)))

    def test_project_validation_script_exposes_main(self):
        module = load_script("validate_project.py")

        self.assertTrue(callable(getattr(module, "main", None)))

    def test_release_script_exposes_validator(self):
        module = load_script("validate_skill_release.py")

        self.assertTrue(callable(getattr(module, "validate_release", None)))

    def test_contact_sheet_is_qa_only_and_never_changes_source_images(self):
        module = load_script("build_contact_sheet.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            images_dir = project_dir / "images"
            images_dir.mkdir()
            paths = []
            for index, color in enumerate(("red", "blue"), start=1):
                path = images_dir / f"page-{index:02d}.png"
                Image.new("RGB", (320, 240), color).save(path)
                paths.append(path)
            before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
            project = {
                "pages": [
                    {"id": "page-01", "role": "hero", "output": "images/page-01.png"},
                    {"id": "page-02", "role": "detail", "output": "images/page-02.png"},
                ]
            }
            output = project_dir / "review" / "contact-sheet.jpg"

            result = module.build_contact_sheet(project, project_dir, output, columns=2)

            after = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
            self.assertEqual(result, output.resolve())
            self.assertTrue(output.is_file())
            self.assertEqual(before, after)

    def test_contact_sheet_cannot_be_written_into_consumer_images(self):
        module = load_script("build_contact_sheet.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            (project_dir / "images").mkdir()

            with self.assertRaisesRegex(ValueError, "QA-only"):
                module.build_contact_sheet(
                    {"pages": []},
                    project_dir,
                    project_dir / "images" / "contact-sheet.jpg",
                )

    def test_contact_sheet_cli_builds_review_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            (project_dir / "images").mkdir()
            Image.new("RGB", (320, 240), "green").save(
                project_dir / "images" / "page-01.png"
            )
            project_path = project_dir / "project.json"
            project_path.write_text(
                json.dumps(
                    {
                        "pages": [
                            {
                                "id": "page-01",
                                "role": "hero",
                                "output": "images/page-01.png",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            output = project_dir / "review" / "contact-sheet.jpg"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_DIR / "scripts" / "build_contact_sheet.py"),
                    str(project_path),
                    "--project-dir",
                    str(project_dir),
                    "--out",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("contact-sheet.jpg", result.stdout)

    def test_project_cli_reports_invalid_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "project.json"
            project_path.write_text(
                json.dumps({"schema_version": "6.0"}), encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(SKILL_DIR / "scripts" / "validate_project.py"), str(project_path)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported-schema-version", result.stdout)

    def test_project_cli_can_validate_template_structure_without_placeholder_files(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SKILL_DIR / "scripts" / "validate_project.py"),
                str(SKILL_DIR / "templates" / "project_template.json"),
                "--schema-only",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PROJECT VALIDATION OK", result.stdout)

    def test_release_validator_rejects_incomplete_skill_root(self):
        module = load_script("validate_skill_release.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            errors = module.validate_release(Path(temp_dir))

        self.assertIn("missing:SKILL.md", errors)

    def test_release_validator_rejects_retired_overlay_entrypoint(self):
        module = load_script("validate_skill_release.py")
        skill_copy = self.copy_skill()
        (skill_copy / "scripts" / "render_text_overlay.py").write_text(
            "# retired bypass\n", encoding="utf-8"
        )

        errors = module.validate_release(skill_copy)

        self.assertIn("forbidden-production-entry:render_text_overlay.py", errors)

    def test_release_validator_rejects_duplicate_discoverable_skill_name(self):
        module = load_script("validate_skill_release.py")
        skill_copy = self.copy_skill()
        duplicate = skill_copy.parent / "old-workspace" / "skill-snapshot"
        duplicate.mkdir(parents=True)
        (duplicate / "SKILL.md").write_text(
            "---\nname: dst-skills\ndescription: stale duplicate\n---\n",
            encoding="utf-8",
        )

        errors = module.validate_release(skill_copy)

        self.assertTrue(
            any(error.startswith("duplicate-discoverable-skill:") for error in errors),
            errors,
        )

    def test_release_validator_checks_version_and_thin_skill_budget(self):
        module = load_script("validate_skill_release.py")
        skill_copy = self.copy_skill()
        (skill_copy / "VERSION").write_text("6.1.0\n", encoding="utf-8")
        (skill_copy / "SKILL.md").write_text("\n".join(["line"] * 221), encoding="utf-8")

        errors = module.validate_release(skill_copy)

        self.assertIn("version-must-be-8.2.0", errors)
        self.assertIn("skill-too-long:221", errors)

    def test_release_validator_runs_the_project_template_contract(self):
        module = load_script("validate_skill_release.py")
        skill_copy = self.copy_skill()
        template_path = skill_copy / "templates" / "project_template.json"
        template = json.loads(template_path.read_text(encoding="utf-8"))
        template["pages"][1]["copy"]["supporting_points"].append(
            {
                "text": "没有进入提示词的文案",
                "kind": "safe_commercial",
                "fact_ids": [],
            }
        )
        template_path.write_text(json.dumps(template, ensure_ascii=False), encoding="utf-8")

        errors = module.validate_release(skill_copy)

        self.assertIn("template:page-02:copy-not-in-prompt:没有进入提示词的文案", errors)

    def test_release_validator_runs_the_full_set_example_contract(self):
        module = load_script("validate_skill_release.py")
        skill_copy = self.copy_skill()
        example_path = skill_copy / "examples" / "example_project.json"
        example = json.loads(example_path.read_text(encoding="utf-8"))
        example["skill_version"] = "7.2.0"
        example_path.write_text(json.dumps(example, ensure_ascii=False), encoding="utf-8")

        errors = module.validate_release(skill_copy)

        self.assertIn("example:skill-version-must-be-8.2.0", errors)

    def test_release_cli_reports_current_skill_ok(self):
        result = subprocess.run(
            [sys.executable, str(SKILL_DIR / "scripts" / "validate_skill_release.py")],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SKILL STATIC CHECK OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
