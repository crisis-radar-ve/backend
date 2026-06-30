from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident, IncidentReport
from app.schemas import IncidentCreate, IncidentOut

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    visibility: str | None = Query(None),
    category: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Incident)
    if visibility:
        query = query.filter(Incident.visibility == visibility)
    if category:
        query = query.filter(Incident.category == category)
    if status:
        query = query.filter(Incident.status == status)
    return query.order_by(Incident.last_seen.desc()).offset(offset).limit(limit).all()


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("", response_model=IncidentOut)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    incident = Incident(**payload.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.post("/{incident_id}/merge/{target_incident_id}")
def merge_incidents(
    incident_id: str,
    target_incident_id: str,
    reviewer_id: str | None = None,
    db: Session = Depends(get_db),
):
    source = db.query(Incident).filter(Incident.id == incident_id).first()
    target = db.query(Incident).filter(Incident.id == target_incident_id).first()
    if not source or not target:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Re-link reports
    links = db.query(IncidentReport).filter(
        IncidentReport.incident_id == source.id
    ).all()
    for link in links:
        link.incident_id = target.id

    db.delete(source)
    db.commit()
    return {"ok": True, "merged_into": target_incident_id}
