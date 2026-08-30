import unittest

from travel_agent_core import Decision, public_result, process_claim


def claim(claim_id, expenses, **overrides):
    value = {
        "claim_id": claim_id,
        "employee_id": "EMP-100",
        "trip_start": "2026-08-01",
        "trip_end": "2026-08-03",
        "submitted_on": "2026-08-10",
        "expenses": expenses,
    }
    value.update(overrides)
    return value


class TravelAgentTests(unittest.TestCase):
    def test_fully_compliant_claim_is_approved(self):
        result = process_claim(claim("T-1", [{"category": "airfare", "amount": 450, "receipt": True}]))
        self.assertEqual(result["decision"], Decision.APPROVE.value)
        self.assertEqual(result["approved_amount"], 450.0)

    def test_unknown_category_is_rejected(self):
        result = process_claim(claim("T-2", [{"category": "gift", "amount": 100, "receipt": True}]))
        self.assertEqual(result["decision"], Decision.REJECT.value)
        self.assertEqual(result["approved_amount"], 0.0)

    def test_cap_creates_partial_approval(self):
        result = process_claim(claim("T-3", [{"category": "airfare", "amount": 1800, "receipt": True}]))
        self.assertEqual(result["decision"], Decision.PARTIAL_APPROVE.value)
        self.assertEqual(result["approved_amount"], 1500.0)
        self.assertEqual(result["deducted_amount"], 300.0)

    def test_missing_receipt_is_manual_review_with_no_final_amount(self):
        result = process_claim(claim("T-4", [{"category": "meals", "amount": 60, "receipt": False}]))
        self.assertEqual(result["decision"], Decision.MANUAL_REVIEW.value)
        self.assertEqual(result["approved_amount"], 0.0)
        self.assertEqual(result["deducted_amount"], 0.0)

    def test_large_claim_is_manual_review(self):
        result = process_claim(claim("T-5", [{"category": "airfare", "amount": 1501, "receipt": True}]))
        self.assertEqual(result["decision"], Decision.MANUAL_REVIEW.value)
        self.assertEqual(result["approved_amount"], 0.0)

    def test_late_claim_is_manual_review(self):
        result = process_claim(claim("T-6", [{"category": "airfare", "amount": 200, "receipt": True}], submitted_on="2026-09-15"))
        self.assertEqual(result["decision"], Decision.MANUAL_REVIEW.value)
        self.assertTrue(result["audit"]["validation_errors"])

    def test_public_contract_is_exact_and_audit_remains_available(self):
        result = process_claim(claim("T-7", [{"category": "registration", "amount": 300, "receipt": True}]))
        compact = public_result(result)
        self.assertEqual(set(compact), {
            "claim_id", "decision", "approved_amount", "deducted_amount",
            "missing_docs", "explanation", "policy_refs", "tools_used", "confidence",
        })
        self.assertIn("line_items", result["audit"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
