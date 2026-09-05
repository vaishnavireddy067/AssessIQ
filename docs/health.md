# AssessIQ Health & Probes Specification

AssessIQ provides Kubernetes/Docker compatible health check endpoints on the root API router:

### 1. Simple Health Probe
- **Endpoint**: `GET /health`
- **Purpose**: General status check.
- **Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### 2. Liveness Probe
- **Endpoint**: `GET /healthz`
- **Purpose**: Fast container liveness check. Determines if the FastAPI process is running.
- **Status Code**: `200 OK`
- **Response**:
```json
{
  "status": "alive"
}
```

### 3. Readiness Probe
- **Endpoint**: `GET /readyz`
- **Purpose**: Validates upstream connectivity (e.g. PostgreSQL database ping) before routing traffic to the container.
- **Status Code**: `200 OK` (or 503 if unavailable)
- **Response**:
```json
{
  "status": "ready"
}
```
