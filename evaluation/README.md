# ReconPilot — AI Evaluation Framework

This module contains ground-truth reconciliation benchmark datasets and automated scoring scripts for evaluating AI classification accuracy, hallucination resistance, and policy compliance.

## Planned Evaluation Datasets (Subsequent Phases)
- `evaluation/data/gold_standard_reconciliation.json`: 500+ curated synthetic financial transactions containing known discrepancy types (fee mismatches, international card surcharges, timing lags, duplicate gateway debits).
- `evaluation/data/edge_cases.json`: Boundary conditions including micro-cent rounding errors, daylight savings time boundary shifts, and multi-currency foreign exchange deltas.

## Planned Evaluation Metrics
1. **Reconciliation Match Rate (RMR):** Proportion of matching ledger records identified deterministically.
2. **AI Classification Accuracy (ACA):** Precision and recall of exception root causes compared against ground truth.
3. **Policy Gate False-Accept Rate (FAR):** Rate of AI suggestions erroneously allowed through the auto-classification gate below confidence criteria.
4. **Audit Trail Completeness (ATC):** Verification that 100% of pipeline state transitions generate valid immutable audit records.
