#!/usr/bin/env python3
"""Validate the public repository, marketplace, and plugin wiring."""

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "dst-skills"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "dst-skills"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    errors = []
    required = [
        ROOT / "README.md",
        ROOT / "LICENSE",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
        ROOT / ".agents" / "plugins" / "marketplace.json",
        PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
        SKILL_ROOT / "SKILL.md",
        SKILL_ROOT / "VERSION",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing:{path.relative_to(ROOT)}")

    if errors:
        raise SystemExit("\n".join(errors))

    marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")
    plugin = load_json(PLUGIN_ROOT / ".codex-plugin" / "plugin.json")
    version = (SKILL_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    entries = marketplace.get("plugins", [])
    if marketplace.get("name") != "dst-skills" or len(entries) != 1:
        errors.append("marketplace-shape")
    elif entries[0].get("name") != "dst-skills":
        errors.append("marketplace-plugin-name")
    elif entries[0].get("source", {}).get("path") != "./plugins/dst-skills":
        errors.append("marketplace-plugin-path")

    if plugin.get("name") != "dst-skills":
        errors.append("plugin-name")
    if plugin.get("version") != version:
        errors.append("plugin-version-mismatch")
    if not re.search(r"(?m)^name:\s*dst-skills\s*$", skill_text[:1000]):
        errors.append("skill-name")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append("invalid-version")

    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8").split("\0")
    for relative in filter(None, tracked):
        path = Path(relative)
        if path.name == ".DS_Store" or path.suffix in {".pyc", ".pyo"} or "__pycache__" in path.parts:
            errors.append(f"forbidden-file:{relative}")

    if errors:
        print("REPOSITORY CHECK FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("REPOSITORY CHECK OK")


if __name__ == "__main__":
    main()
