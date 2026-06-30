from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report, Incident, IncidentReport, ReviewAction
from app.schemas import ReviewActionPayload, ReviewActionOut

router = APIRouter(prefix="/review", tags=["review"])


@router.post("/{report_id}", response_model=ReviewActionOut)
def review_report(
    report_id: UUID,
    payload: ReviewActionPayload,
    reviewer_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    previous_status = report.review_status

    if payload.action == "approve":
        report.review_status = "approved"
        # Auto-create incident if none linked (simplified).
        if not report.incident_links:
            incident = Incident(
                title=report.summary[:120] if report.summary else "Untitled",
                category=report.category,
                location=report.location_text,
                summary=report.summary,
                public_summary=report.public_summary,
                visibility=report.public_visibility,
                confidence=report.confidence,
                source_urls=[report.source_url] if report.source_url else [],
            )
            db.add(incident)
            db.flush()
            db.add(
                IncidentReport(
                    incident_id=incident.id,
                    report_id=report.id,
                    reviewer_confirmed=True,
                )
            )

    elif payload.action == "reject":
        report.review_status = "rejected"
    elif payload.action == "duplicate":
        report.review_status = "duplicate"
    elif payload.action == "sensitive":
        report.review_status = "sensitive_withheld"
        if payload.new_visibility:
            report.public_visibility = payload.new_visibility
    elif payload.action == "escalate":
        if report.urgency == "low":
            report.urgency = "medium"
        elif report.urgency == "medium":
            report.urgency = "high"
    elif payload.action == "request_removal":
        report.requested_removal = True
        report.removal_reason = payload.comment or "Requested by reviewer"
    else:
        raise HTTPException(status_code=400, detail="Unknown action")

    report.reviewer_id = reviewer_id
    from datetime import datetime
    report.reviewed_at = datetime.utcnow()

    action = ReviewAction(
        report_id=report.id,
        reviewer_id=reviewer_id,
        action=payload.action,
        previous_status=previous_status,
        new_status=report.review_status,
        comment=payload.comment,
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action
