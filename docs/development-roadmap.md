# AssessIQ Development Roadmap

This document outlines the high-level roadmap and future phases for the AssessIQ platform after reaching **Phase 7 (Production SaaS Readiness)**.

---

## ✅ Completed Phases

1. **Phase 1: Foundation** - Multi-tenant database schema, RBAC, JWT Auth, Company/User models.
2. **Phase 2: Question Banks** - Assessment models, Question modeling (MCQ, Coding, SQL).
3. **Phase 3: Test Runner & Exec Sandbox** - Secure remote code execution environments (Piston/JDoodle).
4. **Phase 4: Assessment Review & Feedback** - Proctoring listeners, Result/Scorecard calculation.
5. **Phase 5: Copilot, Resume & Skill Matrix** - AI-generated questions, resume parsing, competency matrices.
6. **Phase 6: AI-Assisted Integrity Monitoring** - Sensory proctoring (camera/mic), deterministic risk scoring, recruiter review studio, telemetry retention.
7. **Phase 7: Production SaaS Readiness** - Subscription billing tiers, multi-format export reports, pluggable notifications, rate-limiting, and SuperAdmin platform console.

---

## 🚀 Phase 8: External Integrations & API Offerings (Up Next)

**Goal:** Embed AssessIQ seamlessly into modern HR and recruitment pipelines.
- **ATS Integrations**: Seamless connections to Workable, Greenhouse, and Lever.
- **Public API Keys**: Allow enterprise tenants to generate API keys for custom integrations.
- **Webhooks**: Dispatch real-time JSON payloads when candidates finish assessments or when integrity alerts fire.

## 🛠 Phase 9: Advanced Analytics & Benchmarking

**Goal:** Provide industry insights and comparative performance.
- **Global Percentile Benchmarking**: Compare candidate scores against anonymized platform-wide datasets.
- **Time-to-Hire Analytics**: Dashboard measuring recruitment funnel velocity based on assessment completion times.
- **Diversity & Bias Monitoring**: Statistical tests ensuring question sets do not favor specific demographics disproportionately.

## 🔒 Phase 10: Enterprise Security & Compliance

**Goal:** Secure large-scale enterprise contracts (SOC2 & GDPR compliance).
- **Single Sign-On (SSO)**: SAML 2.0 / OIDC integrations for corporate identity providers (Okta, Azure AD).
- **Audit Logging Export**: Allow tenants to stream their `audit_logs` directly to external SIEM platforms (Splunk, Datadog).
- **Granular Data Residency**: Deploy separate database clusters in EU-West or US-East to comply with strict data localization laws.
