#!/usr/bin/env python3
"""Validate the installable archive and run its own full release checks."""

import argparse
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


FORBIDDEN_PARTS = {"__pycache__", ".DS_Store", ".git", ".env"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()

    with zipfile.ZipFile(args.archive) as archive:
        names = archive.namelist()
        if not names or not all(name.startswith("dst-skills/") for name in names):
            raise SystemExit("archive must contain one dst-skills root")
        for name in names:
            path = PurePosixPath(name)
            if any(part in FORBIDDEN_PARTS for part in path.parts):
                raise SystemExit(f"forbidden archive entry: {name}")
            if path.suffix in FORBIDDEN_SUFFIXES:
                raise SystemExit(f"forbidden archive entry: {name}")

        with tempfile.TemporaryDirectory() as temp_dir:
            archive.extractall(temp_dir)
            root = Path(temp_dir) / "dst-skills"
            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "validate_skill_release.py"), "--full"],
                cwd=root,
                check=False,
            )
            if result.returncode:
                raise SystemExit(result.returncode)

    print(f"PACKAGE CHECK OK ({len(names)} files)")


if __name__ == "__main__":
    main()
