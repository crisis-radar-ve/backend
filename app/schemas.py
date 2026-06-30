from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Raw Items
# ---------------------------------------------------------------------------

class RawItemBase(BaseModel):
    source_type: str
    source_url: str | None = None
    source_metadata: dict[str, Any] = {}
    raw_text: str | None = None
    image_path: str | None = None


class RawItemCreate(RawItemBase):
    pass


class RawItemOut(RawItemBase):
    id: UUID
    fingerprint: str | None
    created_at: datetime
    collected_at: datetime
    processing_status: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class Person(BaseModel):
    name: str | None = None
    role: str | None = None  # missing | helper | contact | other
    context: str | None = None


class ContactInfo(BaseModel):
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    other: str | None = None


class MediaOut(BaseModel):
    id: UUID
    original_url: str | None
    compressed_url: str | None
    thumbnail_url: str | None
    mime_type: str | None
    width: int | None
    height: int | None
    processing_status: str

    class Config:
        from_attributes = True


class ReportBase(BaseModel):
    category: str
    summary: str | None = None
    public_summary: str | None = None
    location_text: str | None = None
    location_country: str = "VE"
    urgency: str = "medium"
    confidence: float = 0.0
    language: str | None = None
    translation: str | None = None
    sensitivity_level: str = "low"
    public_visibility: str = "reviewer_only"
    contact_visibility: str = "responders_only"
    source_url: str | None = None
    original_author_handle: str | None = None
    consent_basis: str = "unknown"
    contains_sensitive_information: bool = False


class ReportCreate(ReportBase):
    raw_item_id: UUID
    people: list[Person] = []
    organizations: list[str] = []
    contact_info: ContactInfo | None = None
    raw_extract: dict[str, Any] | None = None
    model_version: str | None = None
    prompt_version: str | None = None


class ReportOut(ReportBase):
    id: UUID
    raw_item_id: UUID
    people: list[Person]
    organizations: list[str]
    contact_info: dict[str, Any]
    media: list[MediaOut]
    review_status: str
    reviewer_id: UUID | None
    reviewed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------

class IncidentBase(BaseModel):
    title: str | None = None
    category: str
    location: str | None = None
    summary: str | None = None
    public_summary: str | None = None
    status: str = "active"
    visibility: str = "reviewer_only"
    confidence: float = 0.0


class IncidentCreate(IncidentBase):
    pass


class IncidentOut(IncidentBase):
    id: UUID
    report_count: int
    source_urls: list[str]
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime
    media: list[MediaOut]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

class ReviewActionPayload(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|duplicate|merge|sensitive|escalate|request_removal)$")
    comment: str | None = None
    target_incident_id: UUID | None = None
    new_visibility: str | None = None


class ReviewActionOut(BaseModel):
    id: UUID
    report_id: UUID | None
    incident_id: UUID | None
    action: str
    previous_status: str | None
    new_status: str | None
    comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------

class SubmitLinkPayload(BaseModel):
    url: str
    raw_text: str | None = None
    source_metadata: dict[str, Any] = {}


class SubmitTextPayload(BaseModel):
    text: str
    source_metadata: dict[str, Any] = {}


class SubmitOut(BaseModel):
    raw_item_id: UUID
    status: str
