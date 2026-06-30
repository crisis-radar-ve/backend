from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RawItem
from app.schemas import SubmitLinkPayload, SubmitTextPayload, SubmitOut

router = APIRouter(prefix="/submit", tags=["submit"])


def _compute_fingerprint(text: str | None, url: str | None) -> str:
    """Naive fingerprint; replace with a real hash in production."""
    content = f"{url or ''}|{text or ''}".strip()
    return str(hash(content))


@router.post("/link", response_model=SubmitOut)
def submit_link(payload: SubmitLinkPayload, db: Session = Depends(get_db)):
    raw_item = RawItem(
        id=uuid4(),
        source_type="link",
        source_url=payload.url,
        source_metadata=payload.source_metadata,
        raw_text=payload.raw_text,
        fingerprint=_compute_fingerprint(payload.raw_text, payload.url),
        processing_status="pending",
    )
    db.add(raw_item)
    db.commit()
    return SubmitOut(raw_item_id=raw_item.id, status=raw_item.processing_status)


@router.post("/text", response_model=SubmitOut)
def submit_text(payload: SubmitTextPayload, db: Session = Depends(get_db)):
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
    return SubmitOut(raw_item_id=raw_item.id, status=raw_item.processing_status)


# Screenshot upload would go here, using FileUpload.
