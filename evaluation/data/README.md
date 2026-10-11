# ReconPilot Evaluation Benchmark Dataset (v1.0)

This directory stores ground-truth datasets used to evaluate the accuracy of the deterministic reconciliation engine and AI investigative reasoner.

## Ground Truth vs System Predictions
Ground-truth benchmarks are strictly isolated from model predictions:
- Benchmark records are stored in the `benchmark_cases` table.
- Expected match statuses, exception types, and policy outcomes are human-curated and deterministic.
- The evaluation harness scores runtime predictions against these benchmarks without allowing the AI reasoner to self-label or inspect benchmark labels.

## Benchmark Scenarios (50 Cases in Dataset v1.0)

| Scenario Range | Category | Description | Ground Truth Status |
| :--- | :--- | :--- | :--- |
| `SCEN_01` – `SCEN_04` | Standard Matched | Exact 2-way match, partial refund, multiple refunds, agreed fee schedule. | `MATCHED` |
| `SCEN_05` | Fee Discrepancy | Gateway charged ₹95 fee instead of agreed ₹60 MDR slab. | `EXCEPTION` (`FEE_MISMATCH`) |
| `SCEN_06` | Missing Settlement | Captured payment in ledger with no corresponding settlement batch item. | `EXCEPTION` (`MISSING_SETTLEMENT`) |
| `SCEN_07` | Missing Payment | Gateway settled funds for external payment ID absent from internal ledger. | `EXCEPTION` (`MISSING_PAYMENT`) |
| `SCEN_08` – `SCEN_09` | Duplicates | Duplicate internal ledger transaction; duplicate settlement line. | `EXCEPTION` (`DUPLICATE_*`) |
| `SCEN_10` | Timing Drift | Transaction settlement delayed beyond agreed T+2 SLA. | `EXCEPTION` (`DELAYED_SETTLEMENT`) |
| `SCEN_11` | Amount Discrepancy | Gross amount mismatch between internal order and settlement credit. | `EXCEPTION` (`AMOUNT_MISMATCH`) |
| `SCEN_12` – `SCEN_14` | Signed Adjustments | Dispute win ($+\Delta$), chargeback debit ($-\Delta$), settlement-level rebate. | `MATCHED` |
| `SCEN_15` | Refund Lag | Refund issued but not deducted from payout batch net amount. | `EXCEPTION` (`REFUND_MISMATCH`) |
| `SCEN_16` | Missing External ID | Unidentified external reference. | `EXCEPTION` (`UNKNOWN_EXCEPTION`) |
| `SCEN_17` – `SCEN_18` | Batch Aggregation | Multiple payments aggregated into a single settlement batch. | `MATCHED` |
| `SCEN_19`, `SCEN_25` | Ambiguous / Sparse | Ambiguous evidence requiring human review; insufficient evidence. | `EXCEPTION` (`REVIEW_REQUIRED`) |
| `SCEN_20` | Multi-Currency | Cross-currency transaction flag (`USD`). | `EXCEPTION` (`UNKNOWN_EXCEPTION`) |
| `SCEN_21` | Failed Payment | Failed payment attempt must not be counted as expected revenue. | `MATCHED` (Expected net = 0) |
| `SCEN_22` | Failed Refund | Failed refund must not decrease settlement amount. | `MATCHED` (Refund excluded) |
| `SCEN_23` | Within Tolerance | Discrepancy of ₹0.60 falling within ₹1.00 tolerance. | `MATCHED_WITH_VARIANCE` |
| `SCEN_24` | Outside Tolerance | Discrepancy of ₹2.50 exceeding ₹1.00 tolerance. | `EXCEPTION` (`AMOUNT_MISMATCH`) |
| `SCEN_26` – `SCEN_50` | Scale Variations | 25 additional parameterized benchmark variations across fee, adjustment, and match patterns. | Mixed Ground Truth |
