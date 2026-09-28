#!/usr/bin/env python3
"""CLI entrypoint for dst-skills v7.0 through v9.0 project validation."""

import argparse
import json
from pathlib import Path

from project_contract import validate_project


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("--project-dir", type=Path)
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="validate structure and contracts without checking placeholder files",
    )
    args = parser.parse_args()

    project = json.loads(args.project.read_text(encoding="utf-8"))
    project_dir = None if args.schema_only else (args.project_dir or args.project.parent)
    errors = validate_project(project, project_dir)
    if errors:
        print("PROJECT VALIDATION FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("PROJECT VALIDATION OK")


if __name__ == "__main__":
    main()
