import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Boolean,
    JSON,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database import Base


def now_utc():
    return datetime.utcnow()


class RawItem(Base):
    __tablename__ = "raw_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String, nullable=False)  # link | screenshot | text | rss | search
    source_url = Column(Text)
    source_metadata = Column(JSONB, default=dict)
    raw_text = Column(Text)
    image_path = Column(Text)
    fingerprint = Column(Text)
    created_at = Column(DateTime, default=now_utc)
    collected_at = Column(DateTime, default=now_utc)
    processing_status = Column(String, default="pending")  # pending | processing | completed | failed

    reports = relationship("Report", back_populates="raw_item")


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_item_id = Column(UUID(as_uuid=True), ForeignKey("raw_items.id"), nullable=False)

    category = Column(String, nullable=False)
    summary = Column(Text)
    public_summary = Column(Text)
    location_text = Column(Text)
    location_country = Column(String, default="VE")
    location_geometry = Column(String)  # WKT placeholder; swap for GeoAlchemy2 if needed
    geocoding_confidence = Column(Float)

    people = Column(JSONB, default=list)
    organizations = Column(JSONB, default=list)

    urgency = Column(String, default="medium")  # low | medium | high
    confidence = Column(Float, default=0.0)

    language = Column(String)
    translation = Column(Text)

    embedding = Column(Vector(1536))

    model_version = Column(String)
    prompt_version = Column(String)
    raw_extract = Column(JSONB)

    sensitivity_level = Column(String, default="low")  # low | medium | high
    public_visibility = Column(String, default="reviewer_only")  # public | responders_only | reviewer_only
    contact_info = Column(JSONB, default=dict)
    contact_visibility = Column(String, default="responders_only")
    source_url = Column(Text)
    original_author_handle = Column(Text)
    consent_basis = Column(String, default="unknown")  # public_post | family_request | official | unknown

    contains_sensitive_information = Column(Boolean, default=False)
    requested_removal = Column(Boolean, default=False)
    removal_reason = Column(Text)

    review_status = Column(String, default="pending")  # pending | approved | rejected | duplicate | sensitive_withheld
    reviewer_id = Column(UUID(as_uuid=True))
    reviewed_at = Column(DateTime)

    created_at = Column(DateTime, default=now_utc)

    raw_item = relationship("RawItem", back_populates="reports")
    incident_links = relationship("IncidentReport", back_populates="report")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text)
    category = Column(String, nullable=False)
    location = Column(Text)
    location_geometry = Column(String)
    summary = Column(Text)
    public_summary = Column(Text)
    status = Column(String, default="active")  # active | resolved | closed
    visibility = Column(String, default="reviewer_only")
    confidence = Column(Float, default=0.0)
    report_count = Column(Integer, default=0)
    source_urls = Column(ARRAY(Text), default=list)
    time_window_start = Column(DateTime)
    time_window_end = Column(DateTime)
    first_seen = Column(DateTime, default=now_utc)
    last_seen = Column(DateTime, default=now_utc)
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)

    report_links = relationship("IncidentReport", back_populates="incident")


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    incident_id = Column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), primary_key=True
    )
    report_id = Column(
        UUID(as_uuid=True), ForeignKey("reports.id"), primary_key=True
    )
    relationship_confidence = Column(Float)
    reviewer_confirmed = Column(Boolean, default=False)

    report = relationship("Report", back_populates="incident_links")
    incident = relationship("Incident", back_populates="report_links")


class ReviewAction(Base):
    __tablename__ = "review_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"))
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"))
    reviewer_id = Column(UUID(as_uuid=True))
    action = Column(String, nullable=False)
    previous_status = Column(String)
    new_status = Column(String)
    comment = Column(Text)
    created_at = Column(DateTime, default=now_utc)


class IncidentMergeHistory(Base):
    __tablename__ = "incident_merge_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"))
    to_incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"))
    reviewer_id = Column(UUID(as_uuid=True))
    reason = Column(Text)
    created_at = Column(DateTime, default=now_utc)
