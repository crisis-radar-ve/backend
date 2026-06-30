"""
Celery worker stub.

Real tasks to implement:
- fetch_url(raw_item_id)
- process_screenshot(raw_item_id)
- extract_report(raw_item_id)
- generate_embedding(report_id)
- find_duplicate_candidates(report_id)
"""

from celery import Celery
from app.config import settings

worker = Celery("crisisradar", broker=settings.redis_url, backend=settings.redis_url)


@worker.task
def ping():
    return "pong"
