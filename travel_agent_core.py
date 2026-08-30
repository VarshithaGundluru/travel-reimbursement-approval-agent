"""Independent, deterministic travel-reimbursement decision engine.

The module is intentionally dependency-free so it can be reviewed and run in
any Python environment. It separates policy configuration, validation,
calculation, and decision-making so each part is easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
import json


class Decision(str, Enum):
    APPROVE = "APPROVE"
    PARTIAL_APPROVE = "PARTIAL_APPROVE"
    REJECT = "REJECT"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass(frozen=True)
class Policy:
    """Business rules in one auditable configuration object."""

    eligible_categories: Tuple[str, ...] = (
        "airfare",
        "lodging",
        "meals",
        "ground_transport",
        "registration",
    )
    airfare_cap: float = 1500.0
    lodging_nightly_cap: float = 250.0
    meal_daily_cap: float = 75.0
    receipt_threshold: float = 25.0
    submission_window_days: int = 30
    auto_approval_limit: float = 1500.0


DEFAULT_POLICY = Policy()
REQUIRED_CLAIM_FIELDS = ("claim_id", "employee_id", "trip_start", "trip_end", "submitted_on", "expenses")
REQUIRED_EXPENSE_FIELDS = ("category", "amount")


def _money(value: float) -> float:
    return round(max(0.0, float(value)), 2)


def _parse_date(value: Any) -> Optional[date]:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _days(start: date, end: date) -> int:
    return max(1, (end - start).days + 1)


def validate_claim(claim: Mapping[str, Any], policy: Policy = DEFAULT_POLICY) -> List[str]:
    """Return validation errors without changing the input claim."""

    errors: List[str] = []
    for field in REQUIRED_CLAIM_FIELDS:
        if field not in claim or claim[field] in (None, ""):
            errors.append(f"missing claim field: {field}")

    if errors:
        return errors

    trip_start = _parse_date(claim["trip_start"])
    trip_end = _parse_date(claim["trip_end"])
    submitted = _parse_date(claim["submitted_on"])
    if not trip_start or not trip_end or not submitted:
        errors.append("dates must use YYYY-MM-DD format")
    elif trip_end < trip_start:
        errors.append("trip_end cannot be before trip_start")
    elif (submitted - trip_end).days < 0:
        errors.append("submitted_on cannot be before trip_end")
    elif (submitted - trip_end).days > policy.submission_window_days:
        errors.append(f"claim submitted outside the {policy.submission_window_days}-day window")

    if not isinstance(claim["expenses"], list) or not claim["expenses"]:
        errors.append("expenses must be a non-empty list")
    else:
        for index, expense in enumerate(claim["expenses"]):
            if not isinstance(expense, Mapping):
                errors.append(f"expense {index + 1} must be an object")
                continue
            for field in REQUIRED_EXPENSE_FIELDS:
                if field not in expense:
                    errors.append(f"expense {index + 1} missing field: {field}")
            if "amount" in expense:
                try:
                    if float(expense["amount"]) < 0:
                        errors.append(f"expense {index + 1} amount cannot be negative")
                except (TypeError, ValueError):
                    errors.append(f"expense {index + 1} amount must be numeric")
    return errors


def _expense_limit(category: str, claim_days: int, policy: Policy) -> Optional[float]:
    if category == "airfare":
        return policy.airfare_cap
    if category == "lodging":
        return policy.lodging_nightly_cap * claim_days
    if category == "meals":
        return policy.meal_daily_cap * claim_days
    return None


def evaluate_expenses(
    expenses: Iterable[Mapping[str, Any]], claim_days: int, policy: Policy = DEFAULT_POLICY
) -> Dict[str, Any]:
    """Apply category eligibility, caps, and receipt requirements line by line."""

    approved = 0.0
    claimed = 0.0
    deductions = 0.0
    missing_docs: List[str] = []
    line_audit: List[Dict[str, Any]] = []

    for number, expense in enumerate(expenses, start=1):
        category = str(expense.get("category", "")).strip().lower()
        amount = _money(float(expense.get("amount", 0)))
        claimed += amount
        reasons: List[str] = []
        eligible = category in policy.eligible_categories
        allowed = amount if eligible else 0.0

        if not eligible:
            reasons.append("category is outside the reimbursement policy")
        else:
            limit = _expense_limit(category, claim_days, policy)
            if limit is not None and allowed > limit:
                reasons.append(f"policy cap applied: {category} limit is ${limit:,.2f}")
                allowed = limit
            if amount >= policy.receipt_threshold and not bool(expense.get("receipt")):
                missing_docs.append(f"expense {number}: receipt for {category}")
                reasons.append("receipt required for this amount")

        allowed = _money(allowed)
        line_deduction = _money(amount - allowed)
        approved += allowed
        deductions += line_deduction
        line_audit.append({
            "line": number,
            "category": category,
            "claimed": amount,
            "allowed": allowed,
            "deducted": line_deduction,
            "reasons": reasons,
        })

    return {
        "claimed_amount": _money(claimed),
        "approved_amount": _money(approved),
        "deducted_amount": _money(deductions),
        "missing_docs": missing_docs,
        "line_audit": line_audit,
    }


def decide(
    claim: Mapping[str, Any], expense_result: Mapping[str, Any], errors: List[str], policy: Policy
) -> Tuple[Decision, str, float, float]:
    """Return a conservative decision and final amounts."""

    if errors or expense_result["missing_docs"]:
        detail = "; ".join(errors + ["required receipt(s) are missing"] if expense_result["missing_docs"] else errors)
        return Decision.MANUAL_REVIEW, detail, 0.0, 0.0

    approved = float(expense_result["approved_amount"])
    deducted = float(expense_result["deducted_amount"])
    claimed = float(expense_result["claimed_amount"])
    if approved <= 0:
        return Decision.REJECT, "No eligible expense amount remains after policy checks.", 0.0, _money(claimed)
    if approved > policy.auto_approval_limit:
        return Decision.MANUAL_REVIEW, "Eligible amount exceeds the automatic approval limit.", 0.0, 0.0
    if deducted > 0:
        return Decision.PARTIAL_APPROVE, "Eligible expenses approved; policy deductions were applied.", approved, deducted
    return Decision.APPROVE, "All submitted expenses satisfy the configured reimbursement policy.", approved, 0.0


def process_claim(claim: Mapping[str, Any], policy: Policy = DEFAULT_POLICY) -> Dict[str, Any]:
    """Process one claim and return reviewer-facing JSON-compatible data."""

    errors = validate_claim(claim, policy)
    start = _parse_date(claim.get("trip_start"))
    end = _parse_date(claim.get("trip_end"))
    claim_days = _days(start, end) if start and end and end >= start else 1
    expenses = claim.get("expenses") if isinstance(claim.get("expenses"), list) else []
    expense_result = evaluate_expenses(expenses, claim_days, policy) if not errors else {
        "claimed_amount": 0.0, "approved_amount": 0.0, "deducted_amount": 0.0,
        "missing_docs": [], "line_audit": [],
    }
    decision, explanation, approved, deducted = decide(claim, expense_result, errors, policy)
    tools_used = ["validate_claim", "evaluate_expenses", "decide"]
    if expense_result["missing_docs"]:
        tools_used.append("request_missing_documents")
    if decision == Decision.MANUAL_REVIEW:
        tools_used.append("route_to_human_reviewer")

    result = {
        "claim_id": str(claim.get("claim_id", "UNKNOWN")),
        "decision": decision.value,
        "approved_amount": _money(approved),
        "deducted_amount": _money(deducted),
        "missing_docs": expense_result["missing_docs"],
        "explanation": explanation,
        "policy_refs": [
            "eligible_categories",
            "category_caps",
            "receipt_threshold",
            "submission_window",
            "auto_approval_limit",
        ],
        "tools_used": tools_used,
        "confidence": 0.96 if not errors and not expense_result["missing_docs"] else 0.88,
        "audit": {
            "validation_errors": errors,
            "claimed_amount": expense_result["claimed_amount"],
            "trip_days": claim_days,
            "line_items": expense_result["line_audit"],
        },
    }
    return result


def process_json(payload: str, policy: Policy = DEFAULT_POLICY) -> List[Dict[str, Any]]:
    """Process either one claim object or a JSON array of claims."""

    parsed = json.loads(payload)
    claims = parsed if isinstance(parsed, list) else [parsed]
    if not all(isinstance(claim, Mapping) for claim in claims):
        raise ValueError("JSON payload must contain claim objects")
    return [process_claim(claim, policy) for claim in claims]


def public_result(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Return the exact compact contract suitable for an API or evaluator."""

    keys = (
        "claim_id", "decision", "approved_amount", "deducted_amount",
        "missing_docs", "explanation", "policy_refs", "tools_used", "confidence",
    )
    return {key: result[key] for key in keys}
