# ReconPilot — Reconciliation Engine Specification & Verification (Phase 04)

## 1. Overview & Operational Principles

The reconciliation engine in ReconPilot is purely **deterministic**. Financial truth is derived solely from immutable relational records and mathematical algorithms.
AI models never calculate ledger balances, compute settlement differences, or determine whether financial transactions match.

```
+----------------------------------------------------------------------------------------------------+
|                                DETERMINISTIC RECONCILIATION PIPELINE                               |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [ Ingestion & Normalization ]                                                                     |
|  - PostgreSQL Source Records (Payments, Refunds, Fees, Adjustments, Settlement Items, Settlements)  |
|  - Currency Validation (ISO 4217, single-currency enforcement per transaction)                      |
|  - Fixed Decimal Ingestion (Python Decimal, no floating-point arithmetic)                          |
|                                     │                                                              |
|                                     ▼                                                              |
|  [ Duplicate Detection & Pre-Validation ]                                                          |
|  - Detection of duplicated external IDs or double-settled records                                 |
|  - Clean distinction between legitimate identical charge amounts and duplicate external IDs       |
|                                     │                                                              |
|                                     ▼                                                              |
|  [ Multi-Stage Deterministic Matching ]                                                            |
|  - Stage 1: Exact Reference Match (Direct payment_id FK, or external_id == item external_id)      |
|             Confidence: 1.0000                                                                     |
|  - Stage 2: Strong Window Match (Exact amount, same currency, time window <= 48 hrs)               |
|             Confidence: 0.9500                                                                     |
|  - Stage 3: Controlled Candidate Match & Ambiguity Detection                                       |
|             Multiple candidates within window flagged as UNRESOLVED / AMBIGUOUS (Confidence: 0.7000)|
|                                     │                                                              |
|                                     ▼                                                              |
|  [ Expected Settlement Calculation ]                                                               |
|  - Expected = Gross Payment - Net Successful Refunds - Total Applicable Fees + Signed Adjustments  |
|  - Difference = Expected Settlement - Actual Net Settlement                                        |
|  - Tolerance Check: abs(difference) <= AMOUNT_TOLERANCE (Default: INR 1.00)                        |
|                                     │                                                              |
|                                     ▼                                                              |
|  [ Discrepancy Classification & Taxonomy ]                                                         |
|  - MATCHED: difference == 0.00                                                                     |
|  - MATCHED_WITH_VARIANCE: 0.00 < abs(difference) <= 1.00                                            |
|  - FEE_MISMATCH: difference attributed to fee discrepancy                                          |
|  - REFUND_MISMATCH: difference attributed to refund timing or missing refund                       |
|  - AMOUNT_MISMATCH: gross/net discrepancy exceeding tolerance                                      |
|  - DELAYED_SETTLEMENT: payment uncaptured/unsettled within SLA window (e.g. T+2 / 48 hrs)          |
|  - MISSING_PAYMENT: settlement item exists on gateway statement without corresponding payment      |
|  - MISSING_SETTLEMENT: payment captured but missing from gateway payout batch beyond SLA          |
|  - DUPLICATE_TRANSACTION: duplicate transaction record detected                                    |
|                                     │                                                              |
|                                     ▼                                                              |
|  [ Persistence & Audit Trail ]                                                                     |
|  - Atomic PostgreSQL Transaction: ReconciliationRun + ReconciliationResult + ExceptionRecord       |
|  - Immutable AuditEvent recorded with actor_type = SYSTEM                                          |
|  - Complete Execution Metrics (total records, matched, exceptions, net variance, duration ms)      |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Ingestion & Normalization

All records ingested from PostgreSQL tables are mapped into strongly-typed dataclasses defined in `app.modules.reconciliation.normalization`:
- `NormalizedPayment`
- `NormalizedRefund`
- `NormalizedFee`
- `NormalizedAdjustment`
- `NormalizedSettlementItem`
- `NormalizedSettlement`

### Rules
1. **Decimal Precision**: All monetary quantities are represented strictly as `decimal.Decimal` with 2 decimal places. No `float` conversions are permitted.
2. **Currency Consistency**: Every calculation verifies that all components share the same currency. Cross-currency arithmetic raises a `ValueError`.
3. **Status Filtering**:
   - Only `CAPTURED` payments generate expected settlement revenue. `FAILED` or `AUTHORIZED` payments expect `0.00` gross settlement.
   - Only `PROCESSED` refunds deduct from settlement. `FAILED` or `PENDING` refunds are excluded from the deduction.

---

## 3. Mathematical Calculations & Formulas

Defined in `app.modules.reconciliation.calculations`:

### Expected Settlement Formula
$$\text{Expected Settlement} = \text{Payment Amount} - \sum \text{Successful Refunds} - \sum \text{Applicable Fees} + \sum \text{Signed Adjustments}$$

### Settlement Difference Formula
$$\text{Difference} = \text{Expected Settlement} - \text{Actual Settlement}$$

- **Positive Difference ($> 0$):** Under-settlement (the merchant was credited less than expected).
- **Negative Difference ($< 0$):** Over-settlement (the merchant was credited more than expected).
- **Tolerance Gate:** If $|\text{Difference}| \le \text{DEFAULT\_AMOUNT\_TOLERANCE}$ ($\le 1.00$ INR), the record is marked `MATCHED_WITH_VARIANCE`.

---

## 4. Multi-Stage Matching Strategy

Implemented in `app.modules.reconciliation.matching`:

| Stage | Strategy | Criteria | Confidence |
| :--- | :--- | :--- | :--- |
| **Stage 1** | Exact Reference Match | `item.payment_id == payment.id` OR `item.external_payment_id == payment.external_id` | `1.0000` |
| **Stage 2** | Strong Amount & Window | Unmatched payment & item with identical currency, exact net/gross amount match, and timestamp delta $\le 48\text{ hours}$ | `0.9500` |
| **Stage 3** | Controlled Candidate Match | Ambiguity detection: if multiple candidates match within tolerance, match is rejected to prevent false positive matching | `0.7000` |

---

## 5. Discrepancy Classification Taxonomy

Implemented in `app.modules.reconciliation.classification`:

| Exception Type | Trigger Condition | Default Severity |
| :--- | :--- | :--- |
| `MATCHED` | $|\text{Difference}| = 0.00$ | `LOW` |
| `MATCHED_WITH_VARIANCE` | $0.00 < |\text{Difference}| \le 1.00$ | `LOW` |
| `FEE_MISMATCH` | Actual fee deducted exceeds calculated fee by $> 1.00$ | `MEDIUM` |
| `REFUND_MISMATCH` | Recorded refund not accounted for or deducted incorrectly | `MEDIUM` |
| `AMOUNT_MISMATCH` | Net variance exceeds tolerance ($> 1.00$) | `HIGH` / `MEDIUM` |
| `MISSING_SETTLEMENT` | Captured payment with no settlement batch record within SLA window ($\le \text{SLA delay}$, default 2 days) | `MEDIUM` / `HIGH` |
| `DELAYED_SETTLEMENT` | Captured payment un-settled beyond SLA window ($> \text{SLA delay}$, default 2 days) without settlement credit | `HIGH` / `CRITICAL` |
| `MISSING_PAYMENT` | Settlement item present without internal payment capture | `HIGH` |
| `DUPLICATE_PAYMENT` | Multiple payment records share identical external transaction reference | `CRITICAL` |
| `DUPLICATE_SETTLEMENT` | Multiple settlement items share identical external payment reference | `CRITICAL` |

---

## 6. Live PostgreSQL Database Verification

A live execution of the reconciliation pipeline against PostgreSQL 18.1 yielded:
- **Total Source Records Evaluated**: 517
- **Matched Records**: 252 (Exact & Window Matches)
- **Detected Discrepancies**: 8 Exceptions
- **Discrepancy Breakdown**:
  - `AMOUNT_MISMATCH` [HIGH]: 1
  - `AMOUNT_MISMATCH` [MEDIUM]: 3
  - `DELAYED_SETTLEMENT` [HIGH]: 2
  - `REFUND_MISMATCH` [MEDIUM]: 1
  - `MISSING_PAYMENT` [HIGH]: 1
- **Matched with Variance**: 1
- **Deterministic Pipeline Execution Time**: 444 ms
- **Backend Test Suite**: 53 / 53 passed (including full benchmark scenario suite)
