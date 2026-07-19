#!/usr/bin/env python3
"""QA-only Contact Sheet builder."""

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def build_contact_sheet(project, project_dir, output_path, columns=4):
    project_dir = Path(project_dir).resolve()
    output_path = Path(output_path).resolve()
    images_dir = (project_dir / "images").resolve()
    if output_path == images_dir or images_dir in output_path.parents:
        raise ValueError("QA-only Contact Sheet cannot be written under images/")

    cards = []
    for page in project.get("pages", []):
        if not page.get("output"):
            continue
        source_path = project_dir / page["output"]
        with Image.open(source_path) as image:
            thumb = ImageOps.contain(image.convert("RGB"), (480, 480))
        card = Image.new("RGB", (520, 550), "white")
        card.paste(thumb, ((520 - thumb.width) // 2, 18))
        surface = page.get("surface")
        page_type = f"{surface} | {page.get('role', '')}" if surface else page.get("role", "")
        ImageDraw.Draw(card).text(
            (20, 515),
            f"{page.get('id', '')} | {page_type}",
            fill="#111111",
        )
        cards.append(card)

    if not cards:
        raise ValueError("No generated page outputs found")
    columns = max(1, min(columns, len(cards)))
    rows = math.ceil(len(cards) / columns)
    sheet = Image.new("RGB", (columns * 520, rows * 550), "#D8D8D8")
    for index, card in enumerate(cards):
        sheet.paste(card, ((index % columns) * 520, (index // columns) * 550))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, quality=92)
    return output_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("--project-dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--columns", type=int, default=4)
    args = parser.parse_args()
    project = json.loads(args.project.read_text(encoding="utf-8"))
    result = build_contact_sheet(
        project,
        args.project_dir or args.project.parent,
        args.out,
        args.columns,
    )
    print(result)


if __name__ == "__main__":
    main()
