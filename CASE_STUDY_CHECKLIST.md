# Case-study traceability checklist

This document records how the independent implementation covers the requested travel-reimbursement workflow.

| Requirement area | Evidence in this submission |
| --- | --- |
| Structured claim intake | `process_json` accepts one JSON object or an array of claim objects. |
| Policy knowledge | `Policy` is a visible, editable configuration with category eligibility, caps, receipt threshold, submission window, and auto-approval limit. |
| Validation | Required claim and expense fields, date order, submission timing, numeric amounts, and non-empty expenses are checked. |
| Policy tools | `policy_tools.py` exposes named tools for lookup, input validation, eligibility, receipts, airfare, timeliness, per-diem limits, and approval threshold. |
| Decision outcomes | The engine supports `APPROVE`, `PARTIAL_APPROVE`, `REJECT`, and `MANUAL_REVIEW`. |
| Explainability | Every result contains an explanation, policy references, tools used, and line-level audit data. |
| Safe escalation | Missing documents, invalid claims, and over-limit automatic approvals route to manual review with zero finalized amounts. |
| Required output | `public_result` returns the stable fields: claim ID, decision, approved amount, deducted amount, missing documents, explanation, policy references, tools used, and confidence. |
| Testing | `test_travel_agent_core.py` covers compliant, ineligible, capped, missing receipt, high-value, late, and output-contract cases. |
| Reproducibility | No API key, model call, database, or third-party runtime package is required. |

The implementation is deliberately deterministic. An LLM can be added later as an intake or explanation layer, but it cannot override the numeric policy checks.
