import hashlib
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session

from app.ai.extraction import extract_report
from app.database import get_db
from app.models import RawItem, Report, Media
from app.schemas import SubmitLinkPayload, SubmitTextPayload, SubmitOut
from app.services.fetcher import fetch_url
from app.services.media import save_upload

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
    db.flush()

    # Link any media attached to the raw item to the report.
    for media in raw_item.media:
        media.report_id = report.id

    db.commit()
    db.refresh(report)
    return report


@router.post("/link", response_model=SubmitOut)
async def submit_link(
    payload: SubmitLinkPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    fetched = await fetch_url(payload.url)
    raw_text = payload.raw_text or fetched["text"] or payload.url

    raw_item = RawItem(
        id=uuid4(),
        source_type="link",
        source_url=payload.url,
        source_metadata={
            **payload.source_metadata,
            "fetched_title": fetched.get("title"),
            "fetch_error": fetched.get("error"),
        },
        raw_text=raw_text,
        fingerprint=_compute_fingerprint(raw_text, payload.url),
        processing_status="pending",
    )
    db.add(raw_item)
    db.commit()
    db.refresh(raw_item)

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


@router.post("/screenshot", response_model=SubmitOut)
async def submit_screenshot(
    files: list[UploadFile] = File(...),
    caption: str | None = None,
    db: Session = Depends(get_db),
):
    raw_item = RawItem(
        id=uuid4(),
        source_type="screenshot",
        source_metadata={"caption": caption, "filename": files[0].filename if files else None},
        raw_text=caption or "",
        image_path="",
        fingerprint=_compute_fingerprint(caption or "", ""),
        processing_status="pending",
    )
    db.add(raw_item)
    db.flush()

    for file in files:
        saved = await save_upload(file)
        media = Media(
            id=uuid4(),
            raw_item_id=raw_item.id,
            **saved,
            processing_status="compressed",
        )
        db.add(media)

    db.commit()
    db.refresh(raw_item)

    _create_report(db, raw_item)

    return SubmitOut(raw_item_id=raw_item.id, status="completed")
