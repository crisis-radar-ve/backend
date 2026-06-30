import hashlib
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.ai.extraction import extract_report
from app.database import get_db
from app.models import RawItem, Report
from app.schemas import SubmitLinkPayload, SubmitTextPayload, SubmitOut

router = APIRouter(prefix="/submit", tags=["submit"])


def _compute_fingerprint(text: str | None, url: str | None) -> str:
    content = f"{url or ''}|{text or ''}".strip()
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _create_report(db: Session, raw_item: RawItem) -> Report:
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
    db.commit()
    db.refresh(report)
    return report


@router.post("/link", response_model=SubmitOut)
def submit_link(
    payload: SubmitLinkPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    raw_item = RawItem(
        id=uuid4(),
        source_type="link",
        source_url=payload.url,
        source_metadata=payload.source_metadata,
        raw_text=payload.raw_text or payload.url,
        fingerprint=_compute_fingerprint(payload.raw_text, payload.url),
        processing_status="pending",
    )
    db.add(raw_item)
    db.commit()
    db.refresh(raw_item)

    # For MVP, process synchronously. Move to Celery for production.
    _create_report(db, raw_item)

    return SubmitOut(raw_item_id=raw_item.id, status="completed")


@router.post("/text", response_model=SubmitOut)
def submit_text(
    payload: SubmitTextPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    raw_item = RawItem(
        id=uuid4(),
        source_type="text",
        raw_text=payload.text,
        source_metadata=payload.source_metadata,
        fingerprint=_compute_fingerprint(payload.text, None),
        processing_status="pending",
    )
    db.add(raw_item)
    db.commit()
    db.refresh(raw_item)

    _create_report(db, raw_item)

    return SubmitOut(raw_item_id=raw_item.id, status="completed")


# Screenshot upload will go here using FileUpload.
