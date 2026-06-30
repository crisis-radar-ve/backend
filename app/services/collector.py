import hashlib
import html
import re
from datetime import datetime
from typing import Any
from uuid import uuid4

import feedparser
import httpx
from sqlalchemy.orm import Session

from app.ai.extraction import extract_report
from app.models import RawItem, Report


def _strip_html(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


DEFAULT_FEEDS = [
    # Google News RSS for Venezuela crisis-related queries
    "https://news.google.com/rss/search?q=desastre+Venezuela",
    "https://news.google.com/rss/search?q=terremoto+Venezuela",
    "https://news.google.com/rss/search?q=emergencia+Vargas",
    "https://news.google.com/rss/search?q=desaparecido+Caracas",
]


def _compute_fingerprint(text: str | None, url: str | None) -> str:
    content = f"{url or ''}|{text or ''}".strip()
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _create_report_from_raw(db: Session, raw_item: RawItem) -> Report:
    extracted = extract_report(raw_item.raw_text or "")

    report = Report(
        id=uuid4(),
        raw_item_id=raw_item.id,
        category=extracted["category"],
        summary=extracted["summary"],
        public_summary=extracted["public_summary"],
        location_text=extracted.get("location_text"),
        location_country=extracted.get("location_country", "VE"),
        people=extracted.get("people", []),
        organizations=extracted.get("organizations", []),
        urgency=extracted["urgency"],
        confidence=extracted["confidence"],
        language=extracted.get("language", "es"),
        raw_extract=extracted.get("raw_extract"),
        model_version=extracted.get("model_version"),
        prompt_version=extracted.get("prompt_version"),
        contains_sensitive_information=extracted.get("contains_sensitive_information", False),
        sensitivity_level="high" if extracted.get("contains_sensitive_information") else "low",
        source_url=raw_item.source_url,
        review_status="pending",
    )
    db.add(report)
    db.flush()

    for media in raw_item.media:
        media.report_id = report.id

    db.commit()
    db.refresh(report)
    return report


def collect_rss_feeds(db: Session, feeds: list[str] | None = None) -> dict[str, Any]:
    """Collect entries from RSS feeds and create raw items + reports."""
    feeds = feeds or DEFAULT_FEEDS
    created = 0
    skipped = 0

    for feed_url in feeds:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception:
            continue

        for entry in parsed.entries[:10]:  # Limit per feed
            title = _strip_html(entry.get("title", ""))
            link = entry.get("link", "")
            summary = _strip_html(entry.get("summary", "") or entry.get("description", ""))
            published = entry.get("published", "")
            text = f"{title}\n\n{summary}".strip()

            fingerprint = _compute_fingerprint(text, link)
            existing = db.query(RawItem).filter(RawItem.fingerprint == fingerprint).first()
            if existing:
                skipped += 1
                continue

            raw_item = RawItem(
                id=uuid4(),
                source_type="rss",
                source_url=link,
                source_metadata={
                    "feed_url": feed_url,
                    "title": title,
                    "published": published,
                },
                raw_text=text,
                fingerprint=fingerprint,
                processing_status="completed",
                collected_at=datetime.utcnow(),
            )
            db.add(raw_item)
            db.flush()

            _create_report_from_raw(db, raw_item)
            created += 1

    return {"created": created, "skipped": skipped}


def collect_google_news(db: Session, query: str) -> dict[str, Any]:
    """Collect from a Google News RSS query."""
    feed_url = f"https://news.google.com/rss/search?q={httpx.QueryParams({'q': query})}"
    return collect_rss_feeds(db, [feed_url])
