# Varshitha Gundluru

AI Developer Candidate · Python · SQL · Data Analytics

## Featured case study: Travel Reimbursement Approval Agent

This repository contains a self-contained prototype for evaluating employee travel reimbursement claims against policy, receipt requirements, spending limits, and approval thresholds.

**Primary deliverable:** [VarshithaGundluru.ipynb](./VarshithaGundluru.ipynb)

### What the prototype demonstrates

- Policy-grounded claim evaluation with stable `POL-*` rule references
- Agent-style orchestration across policy, receipt, limit, threshold, and timeliness tools
- Structured decisions: `APPROVE`, `PARTIAL_APPROVE`, `REJECT`, and `MANUAL_REVIEW`
- Conservative handling of missing receipts, policy exceptions, and high-value claims
- Intermediate audit evidence and a results dashboard derived from actual outcomes
- Deterministic financial decisions with an optional LLM narration hook

### Sample outcomes

| Claim | Decision | Approved | Deducted |
|---|---|---:|---:|
| CLM-001 | APPROVE | $1,110.00 | $0.00 |
| CLM-002 | REJECT | $0.00 | $380.00 |
| CLM-003 | PARTIAL_APPROVE | $840.00 | $100.00 |
| CLM-004 | MANUAL_REVIEW | Pending | Pending |
| CLM-005 | MANUAL_REVIEW | Pending | Pending |

### Run the notebook

Open `VarshithaGundluru.ipynb` in Jupyter, JupyterLab, or VS Code and run all cells from top to bottom. The default workflow requires no API key or paid service. Matplotlib is optional; if unavailable, the notebook prints a numeric dashboard summary.

The final code cell emits one JSON object per claim with the required fields:

`claim_id`, `decision`, `approved_amount`, `deducted_amount`, `missing_docs`, `policy_refs`, `confidence`, `explanation`, and `tools_used`.

### Repository structure

```text
.
├── README.md
└── VarshithaGundluru.ipynb
```

### Design choices

The policy tools are authoritative for amounts and decisions. The optional LLM layer is limited to explanation writing, which keeps reimbursement calculations reproducible and makes the reasoning auditable. Manual review is preferred whenever evidence is incomplete or the claim exceeds the agent's authority.

### Connect

- [LinkedIn](https://www.linkedin.com/in/varshitha-g-89a9a1314/)
- [HackerRank](https://www.hackerrank.com/profile/varshitha_21bce6)