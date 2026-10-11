# ReconPilot — Autonomous Financial Reconciliation & Exception Investigation

> **Razorpay AI Buildathon 2026** — *Track 4: AI Finance Controller*  
> **Core Guarantee:** Purely deterministic financial matching, evidence-grounded AI root-cause investigation, and dual-control human governance. Zero automated ledger mutations.

---

## 1. Executive Summary & Problem

Modern digital businesses process millions of transactions across internal ledgers, payment gateways (e.g. Razorpay), and banking networks. When fees drift, refunds arrive out of order, or settlement batches lag, manual spreadsheet reconciliation breaks down.

Conversely, naive generative AI approaches present serious compliance risks: hallucinations in arithmetic, fabricated transaction balances, or un-audited automated ledger modifications.

**ReconPilot resolves this dilemma through a strict separation of concerns:**
1. **Deterministic Financial Truth:** All mathematical formulas, matching algorithms, and balance calculations are executed deterministically using fixed-point `Decimal` arithmetic in Python and PostgreSQL ACID storage.
2. **Correlated Evidence Provenance:** Prior to any diagnostic analysis, a structured evidence dossier is correlated from source records, classifying evidence strength (`Confirmed`, `Corroborated`, `Conflicting`) and highlighting missing information.
3. **Schema-Constrained AI Reasoning:** Generative LLMs analyze the evidence dossier strictly to evaluate root-cause hypotheses and recommend operational actions. The reasoner cites only verified evidence IDs, acknowledges operational limitations, and provides full transparency regarding its provider state (Live Gemini vs Deterministic Mock).
4. **Dual-Control Human Governance:** Operational actions (such as write-offs or gateway escalations) are submitted as structured proposals. An automated Separation of Duties (SoD) engine prevents self-approval, requiring authorized reviewer sign-off and maintaining an immutable audit history.

---

## 2. Complete Product Workflow

```
 SOURCE RECORDS (Internal Ledgers, Razorpay Gateway, Bank Statements)
                     │
                     ▼
 DETERMINISTIC MATCHING ENGINE (Exact 2-Way, Tolerance, SLA Windows)
                     │
                     ├── [Matched Records] ──► Expected Settlement Verified
                     │
                     └── [Discrepancies] ────► Categorized Financial Exceptions
                                                   │
                                                   ▼
                                     EVIDENCE CORRELATION ENGINE
                                     (Dossier Assembly & Provenance)
                                                   │
                                                   ▼
                                      AI ROOT CAUSE REASONER
                                     (Hypotheses Citing Evidence)
                                                   │
                                                   ▼
                                     DUAL-CONTROL HUMAN APPROVAL
                                     (Proposals, SoD, Decision Log)
                                                   │
                                                   ▼
                                     COMMAND CENTER TELEMETRY
```

---

## 3. Technology Stack & Architecture

ReconPilot is built as a **clean, modular monolith**:

| Layer | Technologies | Rationale |
|:---|:---|:---|
| **Frontend** | React 18, TypeScript (Strict), Vite, Tailwind CSS, Recharts, Lucide Icons | High-performance SPA with strict typing, responsive data visualizations, and professional fintech hierarchy. |
| **Backend API**| Python 3.11+ / FastAPI, Pydantic 2.x, Uvicorn ASGI | Native async I/O, strict schema contracts, high throughput, and automatic OpenAPI documentation. |
| **Database** | **PostgreSQL (Exclusively)** with SQLAlchemy 2.x & Alembic | ACID transactional guarantees, row-level locking, and `NUMERIC(20, 2)` monetary precision. No SQLite or MongoDB. |
| **Reconciliation**| Python `Decimal` fixed arithmetic (28-digit precision) | Zero floating-point rounding errors in financial matching or fee verification. |
| **AI Reasoner** | Google Gemini 1.5 Pro / Flash + Deterministic Mock Provider | Schema-constrained Pydantic output; seamless fallback to deterministic mock when offline. |

---

## 4. Key Capabilities by Phase

- **Phase 01–03:** PostgreSQL financial schema, Argon2id authentication, RFC-compliant JWT tokens, Role-Based Access Control (`ADMIN`, `FINANCE_CONTROLLER`, `REVIEWER`, `FINANCE_OPERATOR`), and strict multi-tenant isolation.
- **Phase 04:** Multi-stage deterministic reconciliation engine, expected payout calculation, variance detection, and benchmark accuracy evaluation.
- **Phase 05:** Correlated financial evidence dossiers with fact corroboration, conflict detection, and evidence strength categorization.
- **Phase 06:** AI-assisted investigation engine generating evidence-grounded hypotheses, citing audit IDs, and adhering to policy gates.
- **Phase 07:** Dual-control human resolution workflow with proposals, separation of duties enforcement, and immutable decision logging.
- **Phase 08:** Finance Operations Command Center featuring executive KPIs, multi-currency exposure segregation, 14-day trends, and an actionable operations queue.
- **Phase 09:** Presenter Demo Mode, floating guided walkthrough, real-record scenario selector, and presenter readiness checklist.
- **Phase 10:** Production deployment architecture and verified 5–7 minute judge demonstration script.

---

## 5. Local Setup & Startup Guide

### Prerequisites
- **Python:** 3.11 or newer (Python 3.14 verified)
- **Node.js:** v20 or newer and npm (Node 20+ verified)
- **PostgreSQL:** 15, 16, 17, or 18 running locally on port 5432

### Step 1: Clone and Configure Environment
```bash
# Copy configuration template
cp .env.example .env
```
*(Review `.env` to confirm `DATABASE_URL` matches your local PostgreSQL instance).*

### Step 2: Backend Setup
```bash
# 1. Create and activate Python virtual environment
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 2. Install backend dependencies
pip install -e ".[dev]"

# 3. Apply database migrations
alembic -c server/alembic.ini upgrade head

# 4. Start the FastAPI backend server
python -m uvicorn app.main:app --app-dir server --reload --host 127.0.0.1 --port 8000
```
- API Server: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Interactive API Docs (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Readiness Probe: [http://127.0.0.1:8000/api/v1/health/ready](http://127.0.0.1:8000/api/v1/health/ready)

### Step 3: Frontend Setup
```bash
# In a new terminal window:
cd client
npm install
npm run dev
```
- Frontend Application: [http://localhost:5173](http://localhost:5173)

---

## 6. Seeded Demo Accounts

The local development database includes pre-seeded demonstration accounts for evaluating role-based governance:

| Role | Email | Password | Permissions |
|:---|:---|:---|:---|
| **Finance Operator** | `operator@reconpilot.local` | `OperatorSecret2026!` | Can triage exceptions, run investigations, and submit resolution proposals. |
| **Finance Reviewer** | `reviewer@reconpilot.local` | `ReviewerSecret2026!` | Can review evidence and approve or reject proposals submitted by others (SoD enforced). |
| **System Admin** | `admin@reconpilot.local` | `AdminSecret2026!` | Full administrative access, tenant settings, and user management. |

---

## 7. Documentation & Guides

- [**docs/JUDGE_DEMO.md**](docs/JUDGE_DEMO.md): A timed 5–7 minute script guiding evaluators through the complete end-to-end reconciliation lifecycle.
- [**docs/DEPLOYMENT.md**](docs/DEPLOYMENT.md): Production cloud deployment specifications, hosting requirements, container setups, and zero-downtime migration guidelines.

---

## 8. Verification & Test Suite

ReconPilot maintains 100% test coverage across all domain modules:

```bash
# Run complete backend pytest suite (97 passing tests):
python -m pytest server/tests/ -v

# Run Python linter & code formatter:
python -m ruff check server
python -m ruff format server --check

# Run frontend linting & production build:
cd client
npm run lint
npm run build
```

---

## 9. Security, Compliance & Governance Principles

1. **Non-Negotiable Determinism:** All arithmetic (fees, refunds, net payouts, variances) is calculated via Python `Decimal` and PostgreSQL `NUMERIC(20, 2)`. No LLM is ever used for mathematical calculations.
2. **Separation of Duties (SoD):** A user who submits a resolution proposal is prohibited from approving it. Approval requires a distinct reviewer account.
3. **Strict Multi-Currency Protection:** Exposures are segregated by currency (INR vs USD). Cross-currency addition is mathematically forbidden.
4. **AI Transparency:** When live Gemini credentials are not supplied, the system operates via a deterministic mock provider, clearly labeled in the user interface.
5. **Zero Automated Ledger Mutations:** Approval records a reviewed decision and audit trail entry; it never automatically mutates financial source records without authorized external ledger integration.
