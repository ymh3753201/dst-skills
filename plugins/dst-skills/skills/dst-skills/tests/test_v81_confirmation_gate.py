import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
sys.path.insert(0, str(SKILL_DIR / "tests"))

from project_contract import validate_project
from test_v8_strategy_contract import v80_project


def v81_project():
    project = copy.deepcopy(v80_project())
    project["schema_version"] = "8.1"
    project["skill_version"] = "8.1.0"
    project["plan_document"] = "plan.md"
    project["target"]["platform_validation"] = "design_recommendation"

    dimensions = {
        "decision-identity": ("identity", "product_fact"),
        "decision-use": ("usage_fit", "creative_simulation"),
        "decision-detail": ("proof", "product_fact"),
        "decision-fit": ("selection", "product_fact"),
        "decision-trust": ("trust", "product_fact"),
    }
    for decision in project["decision_map"]:
        dimension, claim_type = dimensions[decision["id"]]
        decision["dimension"] = dimension
        decision["claim_type"] = claim_type

    for fact in project["facts"]:
        fact["evidence_status"] = "verified"
        fact["claim_scope"] = "只限该条文本明确表达的商品事实"
        fact["approved_for_copy"] = True

    for index, page in enumerate(project["pages"], start=1):
        page["primary_decision_id"] = page["decision_ids"][0]
        page["unique_evidence"] = f"第 {index} 页提供独立且不重复的可见证据"
        page["has_factual_claims"] = False
        page["claim_fact_ids"] = []
    return project


class V81ConfirmationGateTests(unittest.TestCase):
    def test_complete_v81_project_is_valid(self):
        self.assertEqual(validate_project(v81_project()), [])

    def test_planned_project_rejects_any_blocking_decision(self):
        project = v81_project()
        project["decision_map"][3].update(
            {
                "status": "blocking",
                "basis": "missing",
                "claim_type": "missing_fact",
                "fact_ids": [],
                "page_ids": [],
            }
        )

        errors = validate_project(project)

        self.assertIn(
            "decision-fit:planned-project-has-blocking-decision",
            errors,
        )

    def test_missing_information_cannot_be_disguised_as_out_of_scope(self):
        project = v81_project()
        project["decision_map"][3].update(
            {
                "status": "out_of_scope",
                "basis": "missing",
                "claim_type": "scope_exclusion",
                "page_ids": [],
            }
        )

        errors = validate_project(project)

        self.assertIn(
            "decision-fit:out-of-scope-requires-out-of-scope-basis",
            errors,
        )
        self.assertIn(
            "decision-fit:out-of-scope-requires-explicit-scope-basis",
            errors,
        )
        self.assertIn(
            "decision-fit:out-of-scope-requires-scope-ref",
            errors,
        )

    def test_product_fact_cannot_be_based_on_model_inference(self):
        project = v81_project()
        project["decision_map"][1]["claim_type"] = "product_fact"

        errors = validate_project(project)

        self.assertIn(
            "decision-use:product-fact-cannot-use-model-inference",
            errors,
        )

    def test_full_set_requires_core_commercial_decision_dimensions(self):
        project = v81_project()
        project["decision_map"][4]["dimension"] = "benefit"

        errors = validate_project(project)

        self.assertIn("full-set-missing-decision-dimension:trust", errors)

    def test_factual_copy_cannot_use_unapproved_or_ambiguous_fact(self):
        project = v81_project()
        fact = project["facts"][1]
        fact["evidence_status"] = "ambiguous"
        fact["claim_scope"] = "无法确认该数字属于整机还是充电盒"
        fact["approved_for_copy"] = False
        page = project["pages"][5]
        page["has_factual_claims"] = True
        page["claim_fact_ids"] = ["fact-02"]

        errors = validate_project(project)

        self.assertIn("page-06:claim-fact-not-approved:fact-02", errors)

    def test_ambiguous_fact_can_never_be_marked_approved_for_copy(self):
        project = v81_project()
        fact = project["facts"][1]
        fact["evidence_status"] = "ambiguous"
        fact["approved_for_copy"] = True

        errors = validate_project(project)

        self.assertIn("fact-02:ambiguous-fact-cannot-be-approved", errors)

    def test_factual_copy_requires_explicit_claim_fact_links(self):
        project = v81_project()
        project["pages"][5]["has_factual_claims"] = True

        errors = validate_project(project)

        self.assertIn("page-06:factual-copy-requires-claim-facts", errors)

    def test_planned_project_requires_human_readable_plan_document(self):
        project = v81_project()
        project.pop("plan_document")

        errors = validate_project(project)

        self.assertIn("planned-project-requires-plan-document", errors)

    def test_declared_plan_document_must_exist_in_project_directory(self):
        project = v81_project()

        with tempfile.TemporaryDirectory() as project_dir:
            errors = validate_project(project, project_dir)

        self.assertIn("missing-plan-document-file", errors)

    def test_each_page_requires_unique_evidence_and_primary_decision(self):
        project = v81_project()
        project["pages"][2]["unique_evidence"] = ""
        project["pages"][3]["primary_decision_id"] = "decision-use"

        errors = validate_project(project)

        self.assertIn("page-03:missing-unique-evidence", errors)
        self.assertIn("page-04:primary-decision-not-linked:decision-use", errors)

    def test_planned_full_set_rejects_more_than_two_pages_with_same_primary_decision(self):
        project = v81_project()
        project["pages"][2]["decision_ids"].append("decision-identity")
        project["pages"][2]["primary_decision_id"] = "decision-identity"

        errors = validate_project(project)

        self.assertIn(
            "planned-full-set-repeats-primary-decision:decision-identity:3",
            errors,
        )

    def test_platform_preflight_requires_backend_verified_specs(self):
        project = v81_project()
        project["target"]["mode"] = "platform_preflight"

        errors = validate_project(project)

        self.assertIn(
            "platform-preflight-requires-backend-verified-specs",
            errors,
        )

    def test_jd_earbud_regression_is_not_confirmation_ready_under_v81(self):
        project = v81_project()
        project["status"] = "draft"
        for index, decision_id in ((1, "decision-wearing"), (3, "decision-battery"), (4, "decision-sound-spec")):
            decision = project["decision_map"][index]
            old_decision_id = decision["id"]
            decision.update(
                {
                    "id": decision_id,
                    "status": "blocking",
                    "basis": "missing",
                    "claim_type": "missing_fact",
                    "fact_ids": [],
                    "page_ids": [],
                    "reason": "商品资料不足，不得写入事实文案。",
                }
            )
            for page in project["pages"]:
                page["decision_ids"] = [
                    decision_id if item == old_decision_id else item
                    for item in page["decision_ids"]
                ]
                if page["primary_decision_id"] == old_decision_id:
                    page["primary_decision_id"] = decision_id
        blocking = {
            item["id"]
            for item in project["decision_map"]
            if item["status"] == "blocking"
        }

        self.assertEqual(project["status"], "draft")
        self.assertIn("decision-wearing", blocking)
        self.assertIn("decision-battery", blocking)
        self.assertIn("decision-sound-spec", blocking)
        self.assertEqual(validate_project(project), [])


if __name__ == "__main__":
    unittest.main()
