# ReconPilot — API Specifications (v1)

## Base URL
`/api/v1`

## Response Conventions

All API v1 endpoints return a standardized JSON envelope:

### Success
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

### Error
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human readable explanation.",
    "details": null
  }
}
```

---

## Implemented Endpoints (Phase 01)

### `GET /api/v1/health`
Liveness probe checking that the application server is running and reporting environment configuration.

**Response `200 OK`:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "service": "reconpilot-backend",
    "version": "0.1.0",
    "environment": "development",
    "integrations": {
      "razorpay_configured": false,
      "ai_provider": "mock",
      "llm_configured": false
    }
  },
  "error": null
}
```

---

### `GET /api/v1/health/ready`
Readiness probe verifying actual live connectivity to the PostgreSQL database.

**Success Response `200 OK` (Database connected):**
```json
{
  "success": true,
  "data": {
    "status": "ready",
    "service": "reconpilot-backend",
    "database": {
      "type": "PostgreSQL",
      "connected": true,
      "message": "PostgreSQL database connection verified."
    },
    "config": {
      "environment": "development",
      "amount_tolerance": 1.0,
      "ai_auto_classify_threshold": 0.9,
      "ai_review_threshold": 0.75
    }
  },
  "error": null
}
```

**Unavailable Response `503 Service Unavailable` (Database unreachable):**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "DATABASE_UNAVAILABLE",
    "message": "PostgreSQL database dependency is not reachable.",
    "details": {
      "status": "not_ready",
      "service": "reconpilot-backend",
      "database": {
        "type": "PostgreSQL",
        "connected": false,
        "message": "PostgreSQL database unavailable (OperationalError): connection timeout expired"
      },
      "config": {
        "environment": "development",
        "amount_tolerance": 1.0,
        "ai_auto_classify_threshold": 0.9,
        "ai_review_threshold": 0.75
      }
    }
  }
}
```

---

---

## Implemented Endpoints (Phase 03 & Phase 04)

### Authentication & RBAC (Phase 03)
- `POST /api/v1/auth/login` — Authenticate user and receive JWT access token.
- `GET /api/v1/auth/me` — Retrieve current authenticated user profile and roles.
- `POST /api/v1/auth/logout` — Invalidate user session.
- `GET /api/v1/users` — Admin-only paginated, searchable user management endpoint.

### Reconciliation Runs & Results (Phase 04)
- `POST /api/v1/reconciliation/runs` — Trigger a deterministic reconciliation execution for the merchant.
- `GET /api/v1/reconciliation/runs` — Paginated list of historical reconciliation runs with status, duration, and record counters.
- `GET /api/v1/reconciliation/runs/{id}` — Get single reconciliation run detail.
- `GET /api/v1/reconciliation/runs/{id}/results` — Paginated line-by-line reconciliation outcomes (match status, expected settlement, actual settlement, variance, confidence).

### Financial Ingestion (Phase 04)
- `POST /api/v1/ingestion/demo` — Idempotently seed or reload the canonical demo financial dataset into PostgreSQL.

### Transactions & Ledger (Phase 04)
- `GET /api/v1/transactions` — Query paginated captured payments with status, amounts, and metadata.
- `GET /api/v1/transactions/{id}` — Fetch single payment record with refund and fee details.

### Exceptions Queue (Phase 04)
- `GET /api/v1/exceptions` — Query detected exceptions filtered by type, severity, status, and search terms.
- `GET /api/v1/exceptions/{id}` — Fetch detailed exception record with financial impact and reconciliation result linkage.

---

## Planned Endpoints (Phase 05)

### Investigation, Policy & Review
- `POST /api/v1/exceptions/{id}/investigate` — Trigger AI investigation on evidence dossier.
- `GET /api/v1/exceptions/{id}/evidence` — Query structured evidence dossier for an exception.
- `POST /api/v1/exceptions/{id}/reviews` — Submit human controller approval, override, or adjustment.

### Analytics & Audit
- `GET /api/v1/audit/events` — Query immutable audit trail logs.
- `GET /api/v1/analytics/summary` — Aggregate financial match rate, fee leakage metrics, and evaluation scores.
