import json
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIR = SKILL_DIR / "evals" / "fixtures"


class ImmutableRealGenerationRegressionTests(unittest.TestCase):
    def test_real_generation_failure_artifacts_are_installed(self):
        for name in (
            "jd-earbuds-poor-project-v81.json",
            "jd-earbuds-poor-contact-sheet-v81.jpg",
            "taobao-sofa-uniform-square-contact-sheet.jpg",
            "template-heavy-boya-contact-sheet.png",
            "text-risk-ysl-contact-sheet.png",
        ):
            with self.subTest(name=name):
                self.assertTrue((FIXTURE_DIR / name).is_file())

    def test_frozen_jd_outputs_use_only_model_native_generation(self):
        project = json.loads(
            (FIXTURE_DIR / "jd-earbuds-poor-project-v81.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertTrue(project["generation_log"])
        self.assertTrue(
            all(record["tool"] == "image_gen.imagegen" for record in project["generation_log"])
        )
        self.assertTrue(
            all(record["post_processing"] == [] for record in project["generation_log"])
        )

    def test_frozen_jd_outputs_reproduce_sparse_copy_failure(self):
        project = json.loads(
            (FIXTURE_DIR / "jd-earbuds-poor-project-v81.json").read_text(
                encoding="utf-8"
            )
        )
        copy_counts = [len(page["copy"]) for page in project["pages"]]

        self.assertEqual(copy_counts[0], 0)
        self.assertEqual(copy_counts[1:], [2] * 7)
        self.assertEqual(
            [page["role"] for page in project["pages"][-3:]],
            ["commute_still_life", "travel_still_life", "home_lifestyle_closing"],
        )

    def test_visual_fixtures_are_real_image_files(self):
        jpeg = (FIXTURE_DIR / "jd-earbuds-poor-contact-sheet-v81.jpg").read_bytes()
        png = (FIXTURE_DIR / "template-heavy-boya-contact-sheet.png").read_bytes()

        self.assertTrue(jpeg.startswith(b"\xff\xd8\xff"))
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))


if __name__ == "__main__":
    unittest.main()
