import json
from typing import Any

from openai import OpenAI

from app.config import settings


EXTRACTION_PROMPT = """You are an assistant for a crisis intelligence platform. Extract structured information from the following public post or news item about a tragedy in Venezuela.

Rules:
- Only use information present in the text. Do not invent details.
- Categorize the report using exactly one of these categories: HELP_REQUESTED, HELP_OFFERED, MISSING_PERSON, POSSIBLE_LOCATED, HOSPITAL, SHELTER, ROAD_BLOCKED, UTILITY_OUTAGE, SEARCH_AND_RESCUE, RUMOR, IRRELEVANT.
- urgency must be "low", "medium", or "high".
- confidence is your estimate (0.0 to 1.0) that the extracted facts are accurate.
- contains_sensitive_information: true if the text contains phone numbers, exact addresses, ID numbers, medical details, or names of minors.
- sensitive_details: list the types of sensitive info found, if any.
- people: list of people mentioned with role (missing, helper, contact, other).
- organizations: list of organizations mentioned.
- location_text: the most specific location mentioned, or null.
- location_country: "VE" for Venezuela unless clearly another country.
- language: ISO-639-1 code of the original text (e.g. "es").
- is_rumor_or_unverified: true if the post looks like a rumor or lacks evidence.
- needs_human_review_reason: short reason if this clearly needs human review (e.g. "mentions a minor", "possible false report"), otherwise null.

Input text:
"""


def _fallback_extract(raw_text: str) -> dict[str, Any]:
    """Cheap rule-based extraction when OpenAI is not available."""
    text_lower = raw_text.lower()

    category = "IRRELEVANT"
    if any(w in text_lower for w in ["desaparecido", "desaparecida", "busco a", "perdido"]):
        category = "MISSING_PERSON"
    elif any(w in text_lower for w in ["encontrado", "ubicado", "visto en"]):
        category = "POSSIBLE_LOCATED"
    elif any(w in text_lower for w in ["vía bloqueada", "carretera cerrada", "derrumbe", "no hay paso"]):
        category = "ROAD_BLOCKED"
    elif any(w in text_lower for w in ["hospital", "insumos", "donaciones médicas"]):
        category = "HOSPITAL"
    elif any(w in text_lower for w in ["refugio", "albergue"]):
        category = "SHELTER"
    elif any(w in text_lower for w in ["ayuda", "necesito", "urgente"]):
        category = "HELP_REQUESTED"

    urgency = "high" if any(w in text_lower for w in ["urgente", "emergencia", "peligro"]) else "medium"

    return {
        "category": category,
        "summary": raw_text[:200],
        "public_summary": raw_text[:120],
        "location_text": None,
        "location_country": "VE",
        "people": [],
        "organizations": [],
        "urgency": urgency,
        "confidence": 0.5,
        "language": "es",
        "contains_sensitive_information": False,
        "sensitive_details": [],
        "is_rumor_or_unverified": False,
        "needs_human_review_reason": None,
        "raw_extract": {},
        "model_version": "fallback",
        "prompt_version": "1.0",
    }


def extract_report(raw_text: str, image_text: str | None = None) -> dict[str, Any]:
    """Extract structured report from raw text using OpenAI, with rule-based fallback."""
    if not settings.openai_api_key or settings.openai_api_key == "sk-...":
        return _fallback_extract(raw_text)

    client = OpenAI(api_key=settings.openai_api_key)

    combined = raw_text
    if image_text:
        combined += f"\n\n[OCR text from image]:\n{image_text}"

    schema = {
        "type": "object",
        "properties": {
            "category": {"type": "string"},
            "summary": {"type": "string"},
            "public_summary": {"type": "string"},
            "location_text": {"type": ["string", "null"]},
            "location_country": {"type": "string"},
            "people": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": ["string", "null"]},
                        "role": {"type": ["string", "null"]},
                        "context": {"type": ["string", "null"]},
                    },
                },
            },
            "organizations": {"type": "array", "items": {"type": "string"}},
            "urgency": {"type": "string"},
            "confidence": {"type": "number"},
            "language": {"type": "string"},
            "contains_sensitive_information": {"type": "boolean"},
            "sensitive_details": {"type": "array", "items": {"type": "string"}},
            "is_rumor_or_unverified": {"type": "boolean"},
            "needs_human_review_reason": {"type": ["string", "null"]},
        },
        "required": ["category", "summary", "urgency", "confidence"],
    }

    try:
        response = client.chat.completions.create(
            model=settings.default_llm_model,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": combined},
            ],
            functions=[
                {
                    "name": "extract_report",
                    "description": "Extract structured report from crisis-related text",
                    "parameters": schema,
                }
            ],
            function_call={"name": "extract_report"},
            temperature=0.1,
        )

        message = response.choices[0].message
        args = json.loads(message.function_call.arguments)

        return {
            "category": args.get("category", "IRRELEVANT"),
            "summary": args.get("summary", ""),
            "public_summary": args.get("public_summary") or args.get("summary", ""),
            "location_text": args.get("location_text"),
            "location_country": args.get("location_country", "VE"),
            "people": args.get("people", []),
            "organizations": args.get("organizations", []),
            "urgency": args.get("urgency", "medium"),
            "confidence": float(args.get("confidence", 0.5)),
            "language": args.get("language", "es"),
            "contains_sensitive_information": args.get("contains_sensitive_information", False),
            "sensitive_details": args.get("sensitive_details", []),
            "is_rumor_or_unverified": args.get("is_rumor_or_unverified", False),
            "needs_human_review_reason": args.get("needs_human_review_reason"),
            "raw_extract": args,
            "model_version": settings.default_llm_model,
            "prompt_version": "1.0",
        }
    except Exception:
        # Graceful fallback to avoid blocking submissions when OpenAI fails.
        return _fallback_extract(raw_text)


def generate_embedding(text: str) -> list[float] | None:
    """Generate text embedding using OpenAI. Returns None if no API key."""
    if not settings.openai_api_key:
        return None

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(
        model=settings.default_embedding_model,
        input=text,
    )
    return response.data[0].embedding
