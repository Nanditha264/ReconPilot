# ReconPilot — Architecture Documentation

## 1. System Vision & Paradigm

ReconPilot is an **AI Finance Controller** engineered for high-volume fintech and payment operations. It eliminates manual mismatch investigation through an evidence-backed, policy-controlled workflow featuring deterministic matching, automated exception classification, human review, and immutable auditability.

```
+-----------------------------------------------------------------------------------+
|                        RECONPILOT OPERATIONAL PIPELINE                            |
+-----------------------------------------------------------------------------------+
|  [ Ingestion ]   Internal Ledger + Payment Gateway + Bank Settlement Records      |
|         │                                                                         |
|         ▼                                                                         |
|  [ Normalize ]   Standardized schema, ISO currency, decimal-safe amounts          |
|         │                                                                         |
|         ▼                                                                         |
|  [ Reconcile ]   Deterministic 2-way and 3-way matching rules                     |
|         │                                                                         |
|         ▼                                                                         |
|  [ Exceptions]   Detect fee discrepancy, timing lag, missing payout, status drift  |
|         │                                                                         |
|         ▼                                                                         |
|  [ Evidence ]    Assemble structured JSON packet: tx metadata, rule logs, deltas  |
|         │                                                                         |
|         ▼                                                                         |
|  [ AI Reason ]   Hypothesize root causes & suggest classifications within schema  |
|         │                                                                         |
|         ▼                                                                         |
|  [ Policy Gate]  Confidence >= 0.90 ──► Auto-classify & resolve                   |
|         │        Confidence <  0.90 ──► Route to Controller Review Queue          |
|         ▼                                                                         |
|  [ Audit Trail]  Immutable PostgreSQL log: inputs, decisions, timestamps, roles   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Decisions

### 2.1. Why a Modular Monolith?
- **Domain Cohesion:** Financial reconciliation requires strong transactional boundaries (e.g., matching a payment requires atomically locking both internal ledger records and gateway statement lines). Distributed microservices introduce eventual consistency anomalies that are disastrous for ledger accounting.
- **Developer Velocity & Reliability:** A single repository with clean boundaries between `reconciliation`, `exceptions`, `evidence`, `investigation`, `policy`, `review`, and `audit` avoids network latency, distributed serialization overhead, and RPC failure modes.

### 2.2. Why PostgreSQL is the Sole Application Database
- **ACID Financial Guarantees:** Multi-table ACID transactions, strict schema constraints, foreign keys, and row-level locking are non-negotiable in financial accounting.
- **Relational Integrity:** Reconciliation is fundamentally a relational problem (matching `N` ledger lines to `M` bank statement entries).
- **No SQLite/NoSQL:** SQLite lacks production concurrency and granular user/permission controls. MongoDB and Firebase lack cross-entity multi-document transaction guarantees and strict relational integrity required for financial controllership.

### 2.3. Why Python / FastAPI on the Backend?
- **Python Data Ecosystem:** Python provides superior numeric tooling and native bindings to high-performance analytics libraries.
- **FastAPI Performance:** Async I/O handles concurrent gateway webhooks and data ingestion, while strict Pydantic schemas enforce type safety at all system boundaries.
- **Self-Documenting Contracts:** OpenAPI specification generation ensures synchronized frontend TypeScript clients.

### 2.4. Why Deterministic Logic Owns Financial Truth
- **Zero Hallucination Tolerance:** An AI model must never calculate ledger balances, compute settlement amounts, or determine whether two numbers match.
- **Fixed Arithmetic:** All arithmetic is performed using Python's `Decimal` type with fixed rounding precision. Floating-point arithmetic (`float`) is strictly prohibited in financial paths.
- **Reconciliation Engine:** Deterministic rule engines match transactions based on exact or tolerance-governed rules (order ID, reference ID, amount, timestamp windows).

### 2.5. Why AI Only Investigates Structured Evidence
- **Bounded Role:** LLMs act as investigative reasoning assistants, not balance calculators.
- **Structured Dossiers:** The deterministic engine packages all mismatch metadata, fee schedules, and historical patterns into a validated JSON evidence packet.
- **Strict Output Schema:** The LLM responds only via constrained Pydantic schemas (e.g., classification category, root-cause hypothesis, confidence score). Unstructured free-form answers are rejected.

### 2.6. Why Policy & Audit Boundaries are Strictly Isolated
- **Policy Engine:** Acts as a deterministic gatekeeper between AI suggestions and ledger changes. No AI output takes effect unless it satisfies system policy rules (e.g., amount < ₹5,000 and confidence score ≥ 0.90).
- **Human in the Loop:** Ambiguous, high-value, or low-confidence discrepancies are routed directly to human finance controllers with complete evidence summaries.
- **Immutable Audit Trail:** Every event, calculation input, AI reasoning attempt, and human override is logged in dedicated PostgreSQL audit tables with immutable timestamps.

### 2.7. Why No Chatbot, RAG, or Vector Database
- **Operational Reality:** Finance controllers do not query ledgers through open conversational dialogues. Financial operations require deterministic queues, case files, status transitions, and actionable triage grids.
- **Deterministic Truth:** Relational PostgreSQL queries with indexed B-Trees provide exact, reproducible financial lookups, rendering probabilistic vector embeddings and vector databases unsuitable for transactional reconciliation.
