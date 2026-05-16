"""Patient intent routing for the Pristyn semantic search prototype."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pprint import pprint


@dataclass
class JourneyDecision:
    state: str
    title: str
    message: str
    primary_result: dict | None
    alternatives: list[dict]
    clarifier_question: str
    clarifier_chips: list[str]
    safety_note: str


RISKY_TERMS = (
    "bahut bleeding",
    "severe bleeding",
    "chest pain",
    "emergency",
)

CLEAR_TREATMENT_TERMS = (
    "bawasir",
    "bavasir",
    "bawaseer",
    "piles",
    "kidney stone",
    "gallstone",
    "gall bladder stone",
    "gallbladder stone",
    "hernia",
    "kharrate",
    "snoring",
    "bachha nahi",
    "bachcha nahi",
    "bacha nahi",
    "infertility",
)

BROAD_STONE_TERMS = (
    "pathri",
    "patthri",
    "pattari",
    "stone",
)

SPECIFIC_STONE_TERMS = (
    "kidney",
    "gurda",
    "gurde",
    "urine",
    "urinary",
    "peshab",
    "gallbladder",
    "gall bladder",
    "gallstone",
    "pit ki thaili",
    "pitt ki thaili",
)

BROAD_BODY_PART_CHIPS = {
    "kaan": ["kaan dard", "kaan se paani", "sunai kam dena", "kaan ka parda"],
    "ear": ["ear pain", "ear discharge", "hearing loss", "eardrum issue"],
    "pet": ["pet me jalan", "pet dard", "pet ki pathri", "hernia"],
    "stomach": ["stomach pain", "acidity", "gallstone", "hernia"],
    "urine": ["urine me jalan", "urine me blood", "kidney stone", "urine rukna"],
    "peshab": ["peshab me jalan", "peshab me khoon", "pathri", "peshab rukna"],
    "ghutna": ["ghutne mein dard", "ghutne ki chot", "knee replacement", "ligament tear"],
    "knee": ["knee pain", "knee injury", "knee replacement", "ligament tear"],
}


def _normalized(query: str) -> str:
    return " ".join(query.lower().strip().split())


def _contains_any(query: str, terms: tuple[str, ...]) -> bool:
    return any(term in query for term in terms)


def _has_ambiguous_stone_intent(query: str) -> bool:
    has_broad_stone = _contains_any(query, BROAD_STONE_TERMS)
    has_specific_stone = _contains_any(query, SPECIFIC_STONE_TERMS)
    return has_broad_stone and not has_specific_stone


def _top_score(results: list[dict]) -> float:
    if not results:
        return 0.0
    return float(results[0].get("score", 0.0) or 0.0)


def _doctor_fallback(query: str, results: list[dict], reason: str) -> JourneyDecision:
    return JourneyDecision(
        state="doctor_fallback",
        title="Talk to a doctor",
        message="This may need clinical context before choosing a treatment path.",
        primary_result=results[0] if results else None,
        alternatives=results[1:4] if len(results) > 1 else [],
        clarifier_question="Would you like to describe your symptoms in a bit more detail?",
        clarifier_chips=["book consultation", "talk to doctor", "share symptoms"],
        safety_note=f"{reason} If symptoms feel urgent, seek emergency medical care immediately.",
    )


def _clarifier_chips_for(query: str) -> list[str]:
    chips: list[str] = []
    for term, term_chips in BROAD_BODY_PART_CHIPS.items():
        if term in query:
            for chip in term_chips:
                if chip not in chips:
                    chips.append(chip)
    return chips[:6] or ["pain", "bleeding", "swelling", "infection", "operation", "doctor consult"]


def route_patient_intent(query: str, results: list[dict]) -> JourneyDecision:
    normalized_query = _normalized(query)
    top_score = _top_score(results)
    top_result = results[0] if results else None
    alternatives = results[1:4] if len(results) > 1 else []

    if _contains_any(normalized_query, RISKY_TERMS):
        return _doctor_fallback(query, results, "Your query includes a possible warning symptom.")

    if not results or top_score < 0.45:
        return _doctor_fallback(query, results, "We could not confidently match this to a treatment.")

    if _has_ambiguous_stone_intent(normalized_query):
        return JourneyDecision(
            state="needs_clarification",
            title="A little more detail would help",
            message="Pathri can refer to different stone-related conditions, so we should narrow this before choosing a treatment.",
            primary_result=top_result,
            alternatives=alternatives,
            clarifier_question="Pathri can mean different types of stones. Which one is closest?",
            clarifier_chips=["Kidney / urine stone", "Gallbladder stone", "Not sure"],
            safety_note="This is only a search guide, not a diagnosis.",
        )

    has_specific_stone_intent = (
        _contains_any(normalized_query, BROAD_STONE_TERMS)
        and _contains_any(normalized_query, SPECIFIC_STONE_TERMS)
    )
    has_clear_treatment = _contains_any(normalized_query, CLEAR_TREATMENT_TERMS) or has_specific_stone_intent
    has_broad_body_part = any(term in normalized_query for term in BROAD_BODY_PART_CHIPS)

    if has_broad_body_part and not has_clear_treatment:
        return JourneyDecision(
            state="needs_clarification",
            title="A little more detail would help",
            message="This sounds broad, so a symptom or problem type will help narrow the right treatment.",
            primary_result=top_result,
            alternatives=alternatives,
            clarifier_question="Which of these is closest to what you mean?",
            clarifier_chips=_clarifier_chips_for(normalized_query),
            safety_note="This is only a search guide, not a diagnosis.",
        )

    if top_score >= 0.85:
        return JourneyDecision(
            state="direct_match",
            title="Best match found",
            message="This looks like a strong treatment match for your query.",
            primary_result=top_result,
            alternatives=alternatives,
            clarifier_question="",
            clarifier_chips=[],
            safety_note="Confirm symptoms with a qualified doctor before making care decisions.",
        )

    if top_score >= 0.65:
        return JourneyDecision(
            state="needs_confirmation",
            title="Likely match",
            message="This may be what you are looking for, but a quick confirmation would help.",
            primary_result=top_result,
            alternatives=alternatives,
            clarifier_question="Is this the treatment or symptom area you meant?",
            clarifier_chips=["yes, show this", "show alternatives", "talk to doctor"],
            safety_note="Search results are informational and do not replace medical advice.",
        )

    return JourneyDecision(
        state="needs_clarification",
        title="Help us narrow it down",
        message="There are a few possible treatment areas for this query.",
        primary_result=top_result,
        alternatives=alternatives,
        clarifier_question="Which symptom or concern is closest?",
        clarifier_chips=_clarifier_chips_for(normalized_query),
        safety_note="This is only a search guide, not a diagnosis.",
    )


if __name__ == "__main__":
    fake_results = [
        {"slug": "piles", "name": "Laser Treatment for Piles", "score": 0.92},
        {"slug": "fissure", "name": "Anal Fissure Treatment", "score": 0.71},
        {"slug": "fistula", "name": "Anal Fistula Treatment", "score": 0.67},
    ]

    samples = [
        ("bawasir ka ilaj", fake_results),
        ("kaan mei dikkat", [{"slug": "ear-infection", "name": "Ear Infection Treatment", "score": 0.72}]),
        ("bahut bleeding ho rahi hai", fake_results),
    ]

    for sample_query, sample_results in samples:
        print(f"\nQuery: {sample_query}")
        pprint(asdict(route_patient_intent(sample_query, sample_results)))
