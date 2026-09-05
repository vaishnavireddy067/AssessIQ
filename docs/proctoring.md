# AssessIQ Proctoring & Sensory Governance (Phase 6)

## 1. Ethical Governance & Mandatory Consent Principles

AssessIQ implements AI-assisted proctoring under strict ethical, transparent, and privacy-preserving constraints:

1. **Explicit Candidate Consent**:
   - Before high-security assessments begin, candidates are presented with transparent disclosures.
   - Camera, microphone, and browser monitoring permissions are explicitly acknowledged and stored in `candidate_consent_records`.
2. **Guaranteed Zero Automated Rejections**:
   - The AI sensory engine **only flags anomalies and calculates risk tiers** (`NORMAL`, `LOW_RISK`, `REVIEW_REQUIRED`, `HIGH_RISK`).
   - The AI **never** labels a candidate as "cheated" or issues automatic test invalidation.
   - All high-risk sessions require human recruiter adjudication in the Integrity Review Studio.
3. **Transparent, Explainable Scoring**:
   - Deductions are derived from deterministic weights rather than opaque neural network embeddings.
   - Every point deduction is itemized on the scorecard.

---

## 2. Sensory Signals & Deduction Rules

| Signal Event | Severity | Deduction | Description |
|---|---|:---:|---|
| **`MULTIPLE_FACES`** | **CRITICAL** | **-25 pts** | Secondary person(s) identified in camera frame. Forces human review. |
| **`FACE_ABSENT`** | **HIGH** | **-15 pts** | Face obscured or candidate leaves frame for >10 seconds. |
| **`CAMERA_DISCONNECTED`**| **HIGH** | **-10 pts** | Webcam stream was abruptly disconnected or denied. |
| **`FULLSCREEN_EXIT`** | **MEDIUM** | **-15 pts** | Candidate departed fullscreen exam runner. |
| **`TAB_SWITCH`** | **MEDIUM** | **-10 pts** | Browser tab switched or window focus left exam application. |
| **`AUDIO_SPIKE`** | **LOW** | **-5 pts** | Acoustic anomaly or background vocal speech detected. |
| **`PASTE_DETECTED`** | **LOW** | **-5 pts** | External clipboard insertion into question fields. |
| **`WINDOW_BLUR`** | **LOW** | **-3 pts** | Exam window lost foreground focus. |

---

## 3. Risk Tiers & Recruiter Adjudication

- **`NORMAL` (Score: 90 – 100)**: Clean session. No intervention required.
- **`LOW_RISK` (Score: 75 – 89)**: Minor irregularities (e.g. single clipboard paste or brief blur).
- **`REVIEW_REQUIRED` (Score: 55 – 74)**: Multiple window departures or sensory warnings. Recruiter review advised.
- **`HIGH_RISK` (Score: 0 – 54)**: Repeated departures, multiple faces, or extended face absence. Marked for recruiter resolution.

### Recruiter Resolution Workflow:
Recruiters inspect the incident timeline in the candidate scorecard, review the itemized deduction evidence, and set one of two final resolution states:
- `RESOLVED_CLEAN`: Recruiter accepted candidate explanation or confirmed false positive.
- `RESOLVED_FLAGGED`: Recruiter confirmed violation.

---

## 4. Configurable Data Retention & Purge

- **Retention Window**: Proctoring telemetry and sensory signals default to a **90-day retention horizon**.
- **Automated / API Purge**: Expired event payloads can be purged via `POST /api/v1/proctoring/retention/purge`.
- **Compliance Guarantee**: Heavy video/audio metadata is cleared upon expiration while retaining top-level scores and recruiter notes for compliance records.
