>>>>>>> REPLACE
# Crisis Radar VE — Backend

AI-assisted crisis intelligence platform for aggregating and structuring public information during the Venezuela tragedy.

> **Warning:** This is a humanitarian tech effort. All AI-generated output is treated as a candidate report and requires human review before public display.

---

## One-command startup

```bash
./start.sh
```

This script will:
1. Start PostgreSQL + pgvector + Redis via Docker Compose
2. Create/activate a Python virtual environment
3. Install dependencies
4. Create database tables
5. Seed the admin user `frankponte95@gmail.com`
6. Start FastAPI with hot reload on `http://localhost:8000`

### Admin credentials (created by `seed_user.py`)

```text
email:    frankponte95@gmail.com
password: crisiscaracas26
```

---

## Manual commands

If you prefer to run steps manually:

```bash
# Start infrastructure
docker compose up -d postgres redis

# Setup venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Enable pgvector extension
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d crisisradar -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Create tables and seed user
python seed_user.py

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Makefile shortcuts

```bash
make start   # ./start.sh
make stop    # Stop Docker + uvicorn
make setup   # First-time venv setup
make dev     # Run uvicorn only
make seed    # Run seed_user.py
```

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login, returns JWT |
| POST | `/submit/link` | Submit a public URL |
| POST | `/submit/text` | Submit raw text |
| POST | `/submit/screenshot` | Submit image(s) |
| GET | `/reports` | List AI-generated reports |
| GET | `/reports/{id}` | Get a single report |
| GET | `/incidents` | List clustered incidents |
| POST | `/incidents` | Create an incident manually |
| POST | `/review/{report_id}` | Approve / reject / flag a report |

API docs at `http://localhost:8000/docs`.

---

## Project Structure

```
crisis-radar-ve-backend/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── start.sh
├── Makefile
├── seed_user.py
├── TECHNICAL_PROPOSAL.md
└── app/
    ├── main.py
    ├── config.py
    ├── database.py
    ├── models.py
    ├── schemas.py
    ├── worker.py
    ├── ai/
    │   └── extraction.py
    ├── routers/
    │   ├── auth.py
    │   ├── submit.py
    │   ├── reports.py
    │   ├── incidents.py
    │   └── review.py
    └── services/
        ├── auth.py
        ├── extraction.py
        ├── fetcher.py
        └── media.py
```

---

## Next Steps

1. Move AI processing to Celery for async handling.
2. Add OCR for screenshots.
3. Add pgvector nearest-neighbor deduplication.
4. Add responder-only visibility enforcement.

---

## Safety Notes

- All public incidents require human review.
- ID numbers and medical details are never stored.
- Phone numbers and exact addresses are responders-only by default.
- Every review action is audit-logged.
