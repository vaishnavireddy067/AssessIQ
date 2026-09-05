# AssessIQ: Production Deployment & Backups Guide

## 1. System Requirements & Architecture
AssessIQ is built using a modern Python FastAPI backend and a React Vite frontend. 

**Production Topology:**
- **API Server**: Gunicorn + Uvicorn workers (Python 3.11+)
- **Frontend**: NGINX serving static Vite build assets (`dist/`)
- **Database**: PostgreSQL 15+ (AWS RDS, Google Cloud SQL, or Supabase recommended)
- **Background Workers** (Future): Redis + Celery / RQ

---

## 2. Environment Configuration
The application requires the following environment variables in production:
```env
# Security
APP_SECRET_KEY="your-highly-secure-32-char-random-string"

# Database
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/assessiq"
DATABASE_URL_SYNC="postgresql://user:pass@host:5432/assessiq"

# Feature Flags & External APIs
AI_PROVIDER="OPENAI" # or "GEMINI"
OPENAI_API_KEY="sk-..."
```

---

## 3. Deployment Steps

### A. Backend (FastAPI)
1. Clone the repository and install dependencies using Poetry or `pip`.
2. Run database migrations: `alembic upgrade head`
3. Start the production server:
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

### B. Frontend (React / Vite)
1. Install dependencies: `npm install`
2. Build the production bundle: `npm run build`
3. Configure NGINX to serve the `dist/` directory and reverse-proxy `/api` requests to the FastAPI backend.

---

## 4. PostgreSQL Backup Strategy

To ensure data integrity, implement the following backup strategy:
1. **Continuous Archiving**: Use tools like WAL-G or pgBackRest for continuous WAL archiving to Amazon S3.
2. **Daily Logical Backups**: Run `pg_dump` daily to create a snapshot of the database schema and data.
   ```bash
   # scripts/backup.sh
   pg_dump -U $DB_USER -h $DB_HOST $DB_NAME > /backups/assessiq_$(date +%F).sql
   ```
3. **Retention Policy**: Retain daily backups for 30 days, and weekly backups for 1 year.
4. **Disaster Recovery Testing**: Automate a monthly test restore of the production backup to a staging database to verify backup integrity.

---

## 5. Security & Rate Limiting
- AssessIQ includes built-in rate-limiting middleware (`core/middleware/rate_limit.py`) which defaults to 120 requests per minute per IP.
- Ensure the FastAPI server is placed behind a WAF (Web Application Firewall) or Cloudflare for DDoS protection.
- Force HTTPS on the load balancer level.
