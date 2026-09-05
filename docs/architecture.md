# AssessIQ Architecture & Foundation (Phase 1)

## Overview
AssessIQ is a modern, enterprise-ready multi-tenant B2B SaaS platform for technical candidate assessments.

```
                     ┌───────────────────────────┐
                     │    Nginx Reverse Proxy    │
                     │  (SSL, Routing, Security) │
                     └─────────────┬─────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              │                                         │
              ▼                                         ▼
   ┌────────────────────┐                    ┌────────────────────┐
   │ React / Vite App   │                    │ FastAPI Backend    │
   │ (Single-Page App)  │                    │ (REST API & Auth)  │
   └────────────────────┘                    └─────────┬──────────┘
                                                       │
                                     ┌─────────────────┴─────────────────┐
                                     ▼                                   ▼
                          ┌────────────────────┐              ┌────────────────────┐
                          │ PostgreSQL DB      │              │ Redis (Caching,    │
                          │ (Multi-Tenant RLS) │              │ Queues, Sessions)  │
                          └────────────────────┘              └────────────────────┘
```

## Tenancy Model
- **Companies (`companies`)**: Organizations subscribing to AssessIQ.
- **Tenant Isolation**: Every tenant-owned table contains `company_id`. All queries are scoped through `core/tenant.py` and authorization dependencies in `dependencies.py`.
- **Global Candidates**: Candidates are not tied to a single company (`company_id = NULL`), allowing candidates to take assessments for multiple companies seamlessly.

## Role-Based Access Control (RBAC)
Hierarchy:
`CANDIDATE < QUESTION_MANAGER < RECRUITER < COMPANY_ADMIN < SUPER_ADMIN`

1. **SUPER_ADMIN**: Global system administrator (unscoped, manages all tenants and platform metrics).
2. **COMPANY_ADMIN**: Full tenant authority (creates assessments, invites team members, reviews billing).
3. **RECRUITER**: Manages candidate invitations, reviews test scores, views proctoring reports.
4. **QUESTION_MANAGER**: Manages coding/MCQ question banks.
5. **CANDIDATE**: Global end-user taking assessments.

## Authentication & Security
- **JWT Authentication**: Short-lived (15 min) access tokens + refresh tokens with rotation and DB revocation.
- **Passwords**: Hashed with bcrypt (cost factor 12).
- **Audit Logging**: All security actions (`company.created`, `auth.login`, `user.created`, etc.) are written to `audit_logs`.
- **Self-Serve Registration**: `POST /api/v1/auth/register-company` executes atomic tenant onboarding (Company + User + Role) in a single database transaction.
