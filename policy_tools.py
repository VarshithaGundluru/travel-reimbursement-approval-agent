"""Named, reviewer-friendly policy tools for the independent agent."""

from typing import Any, Mapping

from travel_agent_core import (
    DEFAULT_POLICY,
    Policy,
    _expense_limit,
    _parse_date,
    validate_claim,
)


def lookup_policy(policy: Policy = DEFAULT_POLICY):
    return {
        "eligible_categories": list(policy.eligible_categories),
        "airfare_cap": policy.airfare_cap,
        "lodging_nightly_cap": policy.lodging_nightly_cap,
        "meal_daily_cap": policy.meal_daily_cap,
        "receipt_threshold": policy.receipt_threshold,
        "submission_window_days": policy.submission_window_days,
        "auto_approval_limit": policy.auto_approval_limit,
    }


def validate_claim_input(claim: Mapping[str, Any], policy: Policy = DEFAULT_POLICY):
    return validate_claim(claim, policy)


def check_category_eligibility(expense: Mapping[str, Any], policy: Policy = DEFAULT_POLICY):
    return str(expense.get("category", "")).strip().lower() in policy.eligible_categories


def check_receipt_completeness(expense: Mapping[str, Any], policy: Policy = DEFAULT_POLICY):
    amount = float(expense.get("amount", 0))
    return amount < policy.receipt_threshold or bool(expense.get("receipt"))


def check_airfare_compliance(expense: Mapping[str, Any], policy: Policy = DEFAULT_POLICY):
    if str(expense.get("category", "")).strip().lower() != "airfare":
        return True
    return float(expense.get("amount", 0)) <= policy.airfare_cap


def check_submission_timeliness(claim: Mapping[str, Any], policy: Policy = DEFAULT_POLICY):
    end = _parse_date(claim.get("trip_end"))
    submitted = _parse_date(claim.get("submitted_on"))
    return bool(end and submitted and 0 <= (submitted - end).days <= policy.submission_window_days)


def check_per_diem_limits(expense: Mapping[str, Any], claim_days: int, policy: Policy = DEFAULT_POLICY):
    limit = _expense_limit(str(expense.get("category", "")).strip().lower(), claim_days, policy)
    return limit is None or float(expense.get("amount", 0)) <= limit


def check_approval_threshold(amount: float, policy: Policy = DEFAULT_POLICY):
    return float(amount) <= policy.auto_approval_limit
