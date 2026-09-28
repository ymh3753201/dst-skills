#!/usr/bin/env python3
"""Static and full release checker for dst-skills v9.0."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from project_contract import validate_project


def _declared_skill_name(skill_md):
    try:
        lines = skill_md.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines[:20]:
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


def validate_release(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    errors = []
    for relative in (
        "SKILL.md",
        "VERSION",
        "CHANGELOG.md",
        "templates/project_template.json",
        "scripts/project_contract.py",
    ):
        if not (root / relative).is_file():
            errors.append(f"missing:{relative}")

    version_path = root / "VERSION"
    if version_path.is_file() and version_path.read_text(encoding="utf-8").strip() != "9.0.0":
        errors.append("version-must-be-9.0.0")

    skill_path = root / "SKILL.md"
    if skill_path.is_file():
        line_count = len(skill_path.read_text(encoding="utf-8").splitlines())
        if line_count > 220:
            errors.append(f"skill-too-long:{line_count}")

    expected_scripts = {
        "project_contract.py",
        "validate_project.py",
        "build_contact_sheet.py",
        "compile_prompts.py",
        "validate_skill_release.py",
    }
    scripts_dir = root / "scripts"
    if scripts_dir.is_dir():
        scripts = {path.name for path in scripts_dir.glob("*.py")}
        if scripts != expected_scripts:
            errors.append("unexpected-script-set")
        if "render_text_overlay.py" in scripts:
            errors.append("forbidden-production-entry:render_text_overlay.py")

    if (root / "docs").exists():
        errors.append("legacy-docs-directory-present")

    references_dir = root / "references"
    reference_count = len(list(references_dir.glob("*.md"))) if references_dir.is_dir() else 0
    # v9 keeps one focused capability reference per selectable image channel.
    if not 4 <= reference_count <= 7:
        errors.append(f"reference-count:{reference_count}")

    template_path = root / "templates" / "project_template.json"
    if template_path.is_file():
        try:
            template = json.loads(template_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("invalid-project-template")
        else:
            if len(template) > 16 or len(template.get("pages", [{}])[0]) > 18:
                errors.append("project-template-too-complex")
            errors.extend(f"template:{error}" for error in validate_project(template))

    example_path = root / "examples" / "example_project.json"
    if example_path.is_file():
        try:
            example = json.loads(example_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("invalid-example-project")
        else:
            if example.get("schema_version") != "9.0":
                errors.append("example:schema-version-must-be-9.0")
            errors.extend(f"example:{error}" for error in validate_project(example))

    evals_path = root / "evals" / "evals.json"
    if evals_path.is_file():
        try:
            eval_count = len(json.loads(evals_path.read_text(encoding="utf-8"))["evals"])
        except (json.JSONDecodeError, KeyError, TypeError):
            errors.append("invalid-evals-json")
        else:
            if eval_count < 37:
                errors.append(f"not-enough-cross-industry-evals:{eval_count}")

    for relative in (
        "evals/fixtures/jd-earbuds-poor-project-v81.json",
        "evals/fixtures/jd-earbuds-poor-contact-sheet-v81.jpg",
    ):
        if not (root / relative).is_file():
            errors.append(f"missing-immutable-regression:{relative}")

    main_skill = (root / "SKILL.md").resolve()
    for candidate in sorted(root.parent.rglob("SKILL.md")):
        if candidate.resolve() == main_skill:
            continue
        if _declared_skill_name(candidate) == "dst-skills":
            errors.append(
                "duplicate-discoverable-skill:"
                + candidate.relative_to(root.parent).as_posix()
            )
    return errors


def run_full_tests(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(root / "tests"),
            "-p",
            "test_v*.py",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    skipped = re.search(r"skipped=(\d+)", output)
    errors = []
    if result.returncode != 0:
        errors.append("unit-tests-failed")
    if skipped and int(skipped.group(1)) > 0:
        errors.append(f"unit-tests-skipped:{skipped.group(1)}")
    return errors, output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full",
        action="store_true",
        help="run static checks plus the complete unit and real-regression suite",
    )
    args = parser.parse_args()
    errors = validate_release()
    if errors:
        print("SKILL STATIC CHECK FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    if not args.full:
        print("SKILL STATIC CHECK OK")
        return

    full_errors, output = run_full_tests()
    print(output, end="" if output.endswith("\n") else "\n")
    if full_errors:
        print("SKILL FULL RELEASE CHECK FAIL")
        for error in full_errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("SKILL FULL RELEASE CHECK OK")


if __name__ == "__main__":
    main()
