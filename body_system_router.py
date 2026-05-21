"""Small body-system disambiguation layer for generic symptom queries."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class BodySystemDecision:
    state: str
    title: str
    message: str
    clarifier_question: str
    clarifier_chips: list[dict]
    safety_note: str


def _target_chip(label: str, target_query: str) -> dict:
    return {"label": label, "target_query": target_query}


def _consultation_chip(label: str = "Not sure") -> dict:
    return {"label": label, "action": "consultation"}


PROCTOLOGY_BODY_TERMS = (
    "stool",
    "motion",
    "potty",
    "tatti",
    "latrine",
    "mal",
    "bowel",
    "rectal",
    "rectum",
    "anus",
    "anal",
    "gudha",
    "guda",
    "gudhe",
    "pichwada",
    "pichwade",
    "bawasir",
    "piles",
    "fissure",
    "fistula",
    "bhagandar",
)

PROCTOLOGY_SYMPTOM_TERMS = (
    "blood",
    "bleeding",
    "bleed",
    "khoon",
    "khun",
    "lahu",
    "pain",
    "dard",
    "swelling",
    "sujan",
    "pus",
    "discharge",
    "paani",
    "pani",
    "jalan",
    "burning",
    "itching",
    "khujli",
)

PROCTOLOGY_CLEAR_INTENT_TERMS = (
    "bawasir",
    "piles",
    "fissure",
    "anal fissure",
    "fistula",
    "anal fistula",
    "bhagandar",
    "anal abscess",
    "rectal prolapse",
    "pilonidal sinus",
)

UROLOGY_BODY_TERMS = (
    "urine",
    "urinary",
    "peshab",
    "pesab",
    "pishaab",
    "bladder",
    "kidney",
    "gurda",
    "gurde",
    "urethra",
    "prostate",
)

UROLOGY_SYMPTOM_TERMS = (
    "blood",
    "khoon",
    "burning",
    "jalan",
    "pain",
    "dard",
    "blockage",
    "rukna",
    "flow kam",
    "leakage",
    "leak",
)

UROLOGY_CLEAR_INTENT_TERMS = (
    "kidney stone",
    "urinary tract stone",
    "bladder stone",
    "prostate",
    "urethral stricture",
    "phimosis",
    "circumcision",
    "balanitis",
)

GYNECOLOGY_BODY_TERMS = (
    "vaginal",
    "vagina",
    "yoni",
    "uterus",
    "bachhedani",
    "period",
    "periods",
    "maasik",
    "mahavari",
    "menstrual",
)

GYNECOLOGY_SYMPTOM_TERMS = (
    "bleeding",
    "blood",
    "khoon",
    "discharge",
    "paani",
    "white discharge",
    "itching",
    "khujli",
    "burning",
    "jalan",
    "pain",
    "dard",
    "swelling",
    "sujan",
)

GYNECOLOGY_CLEAR_INTENT_TERMS = (
    "irregular periods",
    "vaginal bleeding",
    "vaginal infection",
    "vaginal itching",
    "fibroid",
    "ovarian cyst",
    "pcos",
    "pcod",
)

PREGNANCY_TERMS = (
    "pregnancy",
    "pregnant",
    "garbh",
    "garbhwati",
)

PREGNANCY_SAFETY_SYMPTOMS = (
    "bleeding",
    "blood",
    "khoon",
    "pain",
    "dard",
)


def _normalize(query: str) -> str:
    return " ".join((query or "").lower().strip().split())


def _tokens(query: str) -> set[str]:
    return set(re.findall(r"[\w]+", query, flags=re.UNICODE))


def _contains_term(query: str, tokens: set[str], term: str) -> bool:
    if " " in term:
        return term in query
    return term in tokens


def _contains_any(query: str, tokens: set[str], terms: tuple[str, ...]) -> bool:
    return any(_contains_term(query, tokens, term) for term in terms)


def _proctology_decision() -> BodySystemDecision:
    return BodySystemDecision(
        state="needs_clarification",
        title="We need one more detail",
        message=(
            "This sounds like an anorectal concern. Symptoms like bleeding, pain, swelling, "
            "or discharge during stool can happen due to piles, fissure, fistula, or other conditions."
        ),
        clarifier_question="Which of these is closest?",
        clarifier_chips=[
            _target_chip("Piles / bawasir", "bawasir bleeding"),
            _target_chip("Pain while passing stool", "anal fissure bleeding"),
            _target_chip("Swelling or pus near anus", "anal fistula"),
            _consultation_chip(),
        ],
        safety_note="This is only a search guide, not a diagnosis.",
    )


def _urology_decision() -> BodySystemDecision:
    return BodySystemDecision(
        state="needs_clarification",
        title="We need one more detail",
        message="This sounds like a urinary or kidney-related concern. Choose the closest option so we can guide you better.",
        clarifier_question="Which of these is closest?",
        clarifier_chips=[
            _target_chip("Burning while urinating", "urine burning"),
            _target_chip("Blood in urine", "blood in urine"),
            _target_chip("Stone-like pain", "kidney stone pain"),
            _target_chip("Urine flow problem", "urinary obstruction"),
            _consultation_chip(),
        ],
        safety_note="This is only a search guide, not a diagnosis.",
    )


def _gynecology_decision() -> BodySystemDecision:
    return BodySystemDecision(
        state="needs_clarification",
        title="We need one more detail",
        message="This sounds like a gynecology-related concern. Choose the closest option so we can guide you better.",
        clarifier_question="Which of these is closest?",
        clarifier_chips=[
            _target_chip("Irregular or heavy periods", "irregular periods"),
            _target_chip("Vaginal bleeding", "vaginal bleeding"),
            _target_chip("White discharge / itching", "vaginal infection"),
            _consultation_chip(),
        ],
        safety_note="This is only a search guide, not a diagnosis.",
    )


def _pregnancy_fallback_decision() -> BodySystemDecision:
    return BodySystemDecision(
        state="doctor_fallback",
        title="Talk to a doctor",
        message="This may need clinical context before choosing a treatment path.",
        clarifier_question="Would you like to describe your symptoms in a bit more detail?",
        clarifier_chips=[
            _consultation_chip("book consultation"),
            _consultation_chip("talk to doctor"),
            _consultation_chip("share symptoms"),
        ],
        safety_note="Pregnancy with bleeding or pain should be checked by a qualified doctor. If symptoms feel urgent, seek emergency medical care immediately.",
    )


def classify_body_system_intent(query: str) -> BodySystemDecision | None:
    """Detect high-confidence body-system context before generic retrieval routing."""
    normalized_query = _normalize(query)
    query_tokens = _tokens(normalized_query)

    if (
        _contains_any(normalized_query, query_tokens, PREGNANCY_TERMS)
        and _contains_any(normalized_query, query_tokens, PREGNANCY_SAFETY_SYMPTOMS)
    ):
        return _pregnancy_fallback_decision()

    if (
        _contains_any(normalized_query, query_tokens, PROCTOLOGY_BODY_TERMS)
        and _contains_any(normalized_query, query_tokens, PROCTOLOGY_SYMPTOM_TERMS)
    ):
        if _contains_any(normalized_query, query_tokens, PROCTOLOGY_CLEAR_INTENT_TERMS):
            return None
        return _proctology_decision()

    if (
        _contains_any(normalized_query, query_tokens, UROLOGY_BODY_TERMS)
        and _contains_any(normalized_query, query_tokens, UROLOGY_SYMPTOM_TERMS)
    ):
        if _contains_any(normalized_query, query_tokens, UROLOGY_CLEAR_INTENT_TERMS):
            return None
        return _urology_decision()

    if (
        _contains_any(normalized_query, query_tokens, GYNECOLOGY_BODY_TERMS)
        and _contains_any(normalized_query, query_tokens, GYNECOLOGY_SYMPTOM_TERMS)
    ):
        if _contains_any(normalized_query, query_tokens, GYNECOLOGY_CLEAR_INTENT_TERMS):
            return None
        return _gynecology_decision()

    return None
