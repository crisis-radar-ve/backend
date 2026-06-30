#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "🚀 Crisis Radar VE - Backend startup"

# 1. Ensure environment file exists
if [ ! -f .env ]; then
  echo "⚠️  .env not found, copying .env.example"
  cp .env.example .env
fi

# 2. Start Postgres + Redis via Docker Compose
echo "🐳 Starting Postgres + Redis..."
docker compose up -d postgres redis

# 3. Wait for Postgres to be ready
echo "⏳ Waiting for Postgres..."
until PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d crisisradar -c "SELECT 1" > /dev/null 2>&1; do
  sleep 1
done

# 4. Enable pgvector extension
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d crisisradar -c "CREATE EXTENSION IF NOT EXISTS vector;" > /dev/null

# 5. Create virtual environment if missing
if [ ! -d .venv ]; then
  echo "🐍 Creating virtual environment..."
  python -m venv .venv
fi

# 6. Install/update dependencies
echo "📦 Installing dependencies..."
source .venv/bin/activate
pip install -q -r requirements.txt

# 7. Create tables (replace with Alembic migrations in production)
echo "🗄️  Creating database tables..."
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"

# 8. Seed admin user if not exists
echo "🌱 Seeding admin user..."
python seed_user.py

# 9. Start backend with auto-reload
echo "✅ Starting FastAPI on http://localhost:8000"
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
