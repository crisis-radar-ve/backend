.PHONY: start stop setup test

start:
	./start.sh

stop:
	docker compose down
	pkill -f "uvicorn app.main:app" || true

setup:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	cp .env.example .env

dev:
	.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

seed:
	.venv/bin/python seed_user.py
