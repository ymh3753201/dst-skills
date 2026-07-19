#!/usr/bin/env python3
"""Build a clean, installable dst-skills archive."""

import argparse
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "plugins" / "dst-skills" / "skills" / "dst-skills"
EXCLUDED_PARTS = {"__pycache__", ".DS_Store", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def included_files():
    for path in sorted(SKILL_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        yield path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    files = list(included_files())
    if not files:
        raise SystemExit("no skill files found")

    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, Path("dst-skills") / path.relative_to(SKILL_ROOT))

    print(f"PACKAGED {len(files)} files -> {args.output}")


if __name__ == "__main__":
    main()
