# Crisis Radar VE — Technical Proposal (MVP)

## Vision

Build a lightweight AI-assisted crisis intelligence platform that transforms chaotic public information into structured, reviewable incidents for the tragedy in Venezuela.

The goal is **NOT** to replace existing missing-person platforms or official channels.

The goal is to reduce information overload by aggregating reports from public sources, extracting structured information, clustering duplicate reports, and presenting a clean dashboard for human review and coordination.

---

## Core Principle

The AI never publishes facts automatically.

It only generates **candidate reports**.

Every public incident is reviewable by humans before it reaches any dashboard.

---

## MVP Scope

### Input

- Public news articles
- RSS feeds
- Google Search results
- User-submitted links
- User-submitted screenshots
- User-submitted text

### Output

A dashboard of structured incidents:

- Help requested
- Help offered
- Hospital information
- Blocked roads
- Utility outages
- Missing person mentions
- Possible located person mentions
- Rumors (flagged)

---

## High-Level Architecture

```
               Public Sources
        RSS | News | Google Search | User Links | Screenshots | Raw Text
                 │
                 ▼
           Raw Item Storage (raw_items)
                 │
                 ▼
          AI Processing Layer
        OCR (if image) → Extract entities → Summarize → Categorize → Embedding
                 │
                 ▼
         Deduplication Engine
      Similarity + Embeddings + Human confirmation
                 │
                 ▼
        Incident Aggregator
                 │
                 ▼
          Human Review UI
                 │
                 ▼
        Public Dashboard (tiered visibility)
```

---

## Proposed Stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js |
| Backend | FastAPI |
| Database | PostgreSQL + pgvector |
| Worker | Celery (start with single queue, split later) |
| OCR | Tesseract (prototype) → PaddleOCR/EasyOCR (production) |
| Embedding model | OpenAI / open source (configurable) |
| LLM | GPT / Claude / Kimi / local fallback |

---

## Database Design

### raw_items

Stores everything exactly as received.

```text
id                      UUID PK
source_type             TEXT        -- link | screenshot | text | rss | search
source_url              TEXT
source_metadata         JSONB       -- domain, author, publish time, collector
raw_text                TEXT
image_path              TEXT
fingerprint             TEXT        -- hash of normalized content
created_at              TIMESTAMPTZ
collected_at            TIMESTAMPTZ
processing_status       TEXT        -- pending | processing | completed | failed
```

### reports

AI-generated structured report.

```text
id                      UUID PK
raw_item_id             UUID FK

category                TEXT        -- HELP_REQUESTED, MISSING_PERSON, etc.
summary                 TEXT
public_summary          TEXT        -- sanitized version for public dashboard
location_text           TEXT
location_country        TEXT
location_geometry       GEOMETRY(Point, 4326)
geocoding_confidence    FLOAT

people                  JSONB       -- [{name, role, context}]
organizations           JSONB

urgency                 TEXT        -- low | medium | high
confidence              FLOAT

language                TEXT
translation             TEXT

embedding               VECTOR(1536)

model_version           TEXT
prompt_version          TEXT
raw_extract             JSONB       -- original LLM output

sensitivity_level       TEXT        -- low | medium | high
public_visibility       TEXT        -- public | responders_only | reviewer_only
contact_info            JSONB       -- phone, email, etc.
contact_visibility      TEXT        -- public | responders_only | reviewer_only
source_url              TEXT        -- mandatory for public visibility
original_author_handle  TEXT
consent_basis           TEXT        -- public_post | family_request | official | unknown

contains_sensitive_information  BOOLEAN
requested_removal       BOOLEAN
removal_reason          TEXT

review_status           TEXT        -- pending | approved | rejected | duplicate | sensitive_withheld
reviewer_id             UUID
reviewed_at             TIMESTAMPTZ

created_at              TIMESTAMPTZ
```

### incidents

Cluster of multiple reports.

```text
id                      UUID PK
title                   TEXT
category                TEXT
location                TEXT
location_geometry       GEOMETRY
summary                 TEXT
public_summary          TEXT
status                  TEXT        -- active | resolved | closed
visibility              TEXT        -- public | responders_only | reviewer_only
confidence              FLOAT
report_count            INT
source_urls             TEXT[]
time_window_start       TIMESTAMPTZ
time_window_end         TIMESTAMPTZ
first_seen              TIMESTAMPTZ
last_seen               TIMESTAMPTZ
created_at              TIMESTAMPTZ
updated_at              TIMESTAMPTZ
```

### incident_reports

```text
incident_id             UUID FK
report_id               UUID FK
relationship_confidence FLOAT       -- embedding similarity or reviewer score
reviewer_confirmed      BOOLEAN
```

### review_actions

Audit log for every human decision.

```text
id                      UUID PK
report_id               UUID FK
incident_id             UUID FK
reviewer_id             UUID
action                  TEXT        -- approve | reject | duplicate | merge | sensitive | escalate
previous_status         TEXT
new_status              TEXT
comment                 TEXT
created_at              TIMESTAMPTZ
```

### incident_merge_history

```text
id                      UUID PK
from_incident_id        UUID FK
to_incident_id          UUID FK
reviewer_id             UUID
reason                  TEXT
created_at              TIMESTAMPTZ
```

### media

Stores images and screenshots attached to raw items or reports. Designed for cost optimization.

```text
id                      UUID PK
raw_item_id             UUID FK
report_id               UUID FK

file_path               TEXT        -- storage key / local path
original_url            TEXT        -- original upload (reviewer-only / temporary)
compressed_url          TEXT        -- web-optimized public image
thumbnail_url           TEXT        -- small preview

mime_type               TEXT
size_bytes              INT
width                   INT
height                  INT

processing_status       TEXT        -- pending | compressed | failed
created_at              TIMESTAMPTZ
```

---

## Categories

```text
HELP_REQUESTED
HELP_OFFERED
MISSING_PERSON
POSSIBLE_LOCATED
HOSPITAL
SHELTER
ROAD_BLOCKED
UTILITY_OUTAGE
SEARCH_AND_RESCUE
RUMOR
IRRELEVANT
```

---

## AI Output Schema

```json
{
  "category": "MISSING_PERSON",
  "summary": "...",
  "public_summary": "...",
  "location_text": "Macuto, Vargas",
  "location_country": "VE",
  "people": [
    {"name": "María López", "role": "missing", "context": "last seen in Macuto"}
  ],
  "organizations": [],
  "urgency": "high",
  "confidence": 0.82,
  "language": "es",
  "translation": "...",
  "contains_sensitive_information": true,
  "sensitive_details": ["phone number"],
  "is_rumor_or_unverified": false,
  "needs_human_review_reason": "mentions a minor"
}
```

---

## Tiered Visibility Model

Because the information is already public and livesaving, we do not blanket-suppress it. We publish it with guardrails.

| Tier | Visibility | Examples |
|------|-----------|----------|
| **1 — Public** | Anyone | Road closures, outages, hospital/shelter status, generic help requests, aggregated maps |
| **2 — Public with source link** | Anyone | Names of missing/located persons, general zone/municipality, link to original post |
| **3 — Responders only** | Log-in, role-declared, audit-logged users | Phone numbers, WhatsApp, exact addresses, organizer contacts |
| **4 — Reviewer only** | Trusted reviewers | ID numbers, medical details, photos of minors, flagged content |

### Rules

- Source URL is mandatory for any public or responders-only visibility.
- Phone numbers are responders-only by default; public only when source-linked and reviewer-approved.
- Exact addresses are responders-only; public dashboard shows zone/municipality only.
- ID numbers and medical details are **never collected or stored**; if extracted accidentally, delete immediately.
- Missing-person reports require two independent sources or one official/family confirmation before full public visibility.

---

## Deduplication Strategy

### Phase 1 — Heuristic pre-filter

Same category + similar location + 72-hour window.

### Phase 2 — Exact/near-duplicate detection

MinHash / LSH on normalized text before embedding lookup.

### Phase 3 — Embeddings

Store embedding for every report. Find nearest neighbors above threshold (~0.85–0.90).

### Phase 4 — Human confirmation

For sensitive categories (`MISSING_PERSON`, `POSSIBLE_LOCATED`), never auto-merge. Surface candidates to a reviewer via a `dedup_candidates` queue.

---

## Human Review

Every report is reviewable.

Reviewer actions:

- Approve
- Reject
- Merge into another incident
- Mark as duplicate
- Mark sensitive / change visibility tier
- Escalate urgency
- Request removal

Every action is logged in `review_actions`.

---

## Public Dashboard

Show only approved incidents.

Fields:

- Category
- Summary / public summary
- Zone / municipality
- Confidence
- Last updated
- Source links
- Report harmful content / request removal button

Dashboard disclaimers:

> “This is crowdsourced, unverified public information. Always verify with official channels. Do not rely on this for emergency dispatch.”

---

## Shareability / Social Cards

Every approved public incident can be shared easily to Instagram, X, and WhatsApp.

- **Generate a share card** (PNG) with the incident summary, category, location, urgency, and confidence.
- **Download image** for Instagram / WhatsApp Status.
- **Share to X** via Twitter Web Intent with pre-filled text and link.
- The card always includes the disclaimer and source link.
- For sensitive incidents (`MISSING_PERSON`, `POSSIBLE_LOCATED`), allow sharing only the public summary and source link, never contact details or exact addresses.

---

## Data Sources

### Phase 1 — Manual input
- Paste links
- Paste text
- Upload screenshots

### Phase 2 — RSS + Google News

### Phase 3 — Google Search
- SerpAPI
- Google Programmable Search

Example queries:

```text
site:instagram.com terremoto Venezuela
site:instagram.com desaparecido Caracas
site:instagram.com hospital La Guaira
site:facebook.com terremoto Vargas
```

### Phase 4 — Additional collectors
- Bluesky
- Public Telegram channels

---

## Explicit Non-Goals

- No scraping private Instagram accounts.
- No WhatsApp scraping.
- No automatic publication of missing-person information.
- No facial recognition.
- No automatic “person found” decisions.
- No emergency dispatch.
- No storage of ID numbers or medical details, even if public.

---

## Initial API

```text
POST /submit
GET  /reports
GET  /incidents
POST /review/{report_id}
POST /incidents/{incident_id}/merge
POST /reports/{report_id}/request-removal
```

---

## MVP Roadmap

| Day | Focus |
|-----|-------|
| 1 | FastAPI + PostgreSQL/pgvector + Next.js + submission form + `raw_items` |
| 2 | AI pipeline: OCR → categorization → summarization → structured extraction → embeddings |
| 3 | Reviewer UI + audit log + tiered visibility |
| 4 | Deduplication candidate generation + human-confirmed incident merging |
| 5 | Public dashboard + CSV export + first RSS collector |

---

## Future Ideas

- Interactive map
- Timeline reconstruction
- Confidence evolution
- Hospital capacity monitoring
- Volunteer assignment
- Needs heatmap
- AI-generated situation reports every hour
- Automatic multilingual translation
- Notification subscriptions by region

---

## Cost Optimization Strategy

Because infrastructure costs come from personal funds, every expensive component is optimized from day one.

### Images / multimedia

- **Client-side compression** before upload (canvas or browser-image-compression).
- **Limit upload size** to 10 MB per file and max 4 images per submission initially.
- **Generate three versions:** original (reviewer-only), compressed (public), thumbnail (lists).
- **Preferred object storage:** Cloudflare R2 or Backblaze B2 (lower egress than AWS S3).
- **Delete originals** after successful OCR + thumbnail generation if they are not legally required.
- **Serve via CDN** with long cache headers.
- **Lazy load** images on the dashboard.

### AI / LLM

- Use smaller models (GPT-4o-mini, Claude Haiku, or local models) for extraction and categorization.
- Cache embeddings to avoid recomputing.
- Batch OCR and extraction jobs with Celery during low-traffic windows.
- Skip AI processing for exact duplicates detected by hash.

### Database

- Index `reports(raw_item_id, review_status, category)`.
- Index `incidents(category, status, last_seen)`.
- Use `pgvector` HNSW index for embedding search.
- Archive old `raw_items` and rejected reports after 90 days.

---

## Success Metric

The system is successful if it can convert hundreds of noisy public posts into a small set of structured, deduplicated, reviewable incidents that help volunteers and responders understand the evolving situation faster.
