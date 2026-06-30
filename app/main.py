from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import submit, reports, incidents, review

# Create tables on startup (replace with Alembic in production).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(submit.router)
app.include_router(reports.router)
app.include_router(incidents.router)
app.include_router(review.router)


@app.get("/health")
def health():
    return {"status": "ok"}
