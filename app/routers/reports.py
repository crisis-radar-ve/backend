from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report
from app.schemas import ReportCreate, ReportOut

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportOut])
def list_reports(
    review_status: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Report)
    if review_status:
        query = query.filter(Report.review_status == review_status)
    if category:
        query = query.filter(Report.category == category)
    return query.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: UUID, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("", response_model=ReportOut)
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):
    report = Report(**payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
