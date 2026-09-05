# AssessIQ Public API Integration Guide (Phase 8)

AssessIQ provides a secure public REST API intended for B2B ATS integrations (e.g., Workable, Greenhouse, Lever). Programmatic endpoints are protected by an `ApiKey`.

## Authentication

Create an API Key from the SuperAdmin Dashboard. The raw key is provided once (e.g., `aiq_pr_abc123...`). Provide this key in the HTTP `Authorization` header.

```http
Authorization: Bearer aiq_pr_abc123...
```

## Public API Endpoints

### 1. Invite a Candidate (ATS Integration)
**Endpoint:** `POST /public/v1/assessments/{assessment_id}/invite`

**Payload:**
```json
{
  "candidate_email": "engineer@example.com",
  "candidate_name": "Jane Doe",
  "ats_candidate_id": "ats_uuid_98765"
}
```

**Response:**
```json
{
  "attempt_id": "uuid-1234",
  "magic_link": "https://assessiq.example.com/exam/magic-token-xyz",
  "status": "INVITED"
}
```

### 2. Retrieve Candidate Results
**Endpoint:** `GET /public/v1/results/{attempt_id}`

**Response:**
```json
{
  "attempt_id": "uuid-1234",
  "candidate_email": "engineer@example.com",
  "status": "COMPLETED",
  "total_score": 92,
  "percentage": 92.0,
  "integrity_score": 100.0,
  "is_flagged": false
}
```

## Webhooks

AssessIQ supports real-time webhooks (HMAC-SHA256 signed). Configure your Webhook URL in the Admin dashboard.

**Supported Events:**
- `candidate.submitted`
- `assessment.published`
- `proctoring.flagged`

**Webhook Payload Format:**
```json
{
  "event_id": "evt_abc123",
  "event_type": "candidate.submitted",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "attempt_id": "uuid-1234",
    "score": 92
  }
}
```

**Verifying Signatures:**
AssessIQ signs all payloads. Compute the HMAC-SHA256 of the raw payload using your `secret_key` and compare it against the `AssessIQ-Signature` header (`sha256=...`).
