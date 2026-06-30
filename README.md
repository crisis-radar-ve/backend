# Crisis Radar VE — Backend

AI-assisted crisis intelligence platform for aggregating and structuring public information during the Venezuela tragedy.

> **Warning:** This is a humanitarian tech effort. All AI-generated output is treated as a candidate report and requires human review before public display.

---

## Quick Start

### 1. Start PostgreSQL + pgvector and Redis

```bash
docker compose up -d postgres redis
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add OPENAI_API_KEY if using OpenAI
```

### 3. Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the backend

```bash
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`.
Docs at `http://localhost:8000/docs`.

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/submit/link` | Submit a public URL |
| POST | `/submit/text` | Submit raw text |
| GET | `/reports` | List AI-generated reports |
| GET | `/reports/{id}` | Get a single report |
| GET | `/incidents` | List clustered incidents |
| POST | `/incidents` | Create an incident manually |
| POST | `/review/{report_id}` | Approve / reject / flag a report |

---

## Project Structure

```
crisis-radar-ve-backend/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
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
    └── routers/
        ├── submit.py
        ├── reports.py
        ├── incidents.py
        └── review.py
```

---

## Next Steps

1. Add Celery worker tasks for async AI processing (OCR, extraction, embedding).
2. Implement OpenAI / local LLM extraction pipeline.
3. Add pgvector nearest-neighbor deduplication.
4. Add authentication and role-based access for responder-only data.

---

## Safety Notes

- All public incidents require human review.
- ID numbers and medical details are never stored.
- Phone numbers and exact addresses are responders-only by default.
- Every review action is audit-logged.
