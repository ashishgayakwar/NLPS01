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
    clarifier_chips: list[str | dict]
    safety_note: str


RISKY_TERMS = (
    "bahut bleeding",
    "severe bleeding",
    "chest pain",
    "breathing problem",
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
    "cataract",
    "fissure",
    "fistula",
)

BROAD_SYMPTOM_TERMS = (
    "body pain",
    "pain",
    "dard",
    "badan dard",
    "sharir dard",
    "weakness",
    "kamzori",
    "thakan",
    "tired",
    "fatigue",
    "fever",
    "bukhar",
    "not feeling well",
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

def _target_chip(label: str, target_query: str) -> dict:
    return {"label": label, "target_query": target_query}


def _consultation_chip(label: str = "Not sure") -> dict:
    return {"label": label, "action": "consultation"}


BROAD_BODY_PART_CHIPS = {
    "kaan": [
        _target_chip("kaan dard", "ear pain"),
        _target_chip("kaan se paani", "ear discharge"),
        _target_chip("sunai kam dena", "hearing loss"),
        _target_chip("kaan ka parda", "eardrum issue"),
        _consultation_chip(),
    ],
    "ear": [
        _target_chip("ear pain", "ear pain"),
        _target_chip("ear discharge", "ear discharge"),
        _target_chip("hearing loss", "hearing loss"),
        _target_chip("eardrum issue", "eardrum issue"),
        _consultation_chip(),
    ],
    "pet": [
        _target_chip("pet me jalan", "acidity"),
        _target_chip("pet dard", "stomach pain"),
        _target_chip("pet ki pathri", "kidney stone"),
        _target_chip("hernia", "hernia"),
        _consultation_chip(),
    ],
    "stomach": [
        _target_chip("stomach pain", "stomach pain"),
        _target_chip("acidity", "acidity"),
        _target_chip("gallstone", "gallstone"),
        _target_chip("hernia", "hernia"),
        _consultation_chip(),
    ],
    "urine": [
        _target_chip("urine me jalan", "urine burning"),
        _target_chip("urine me blood", "blood in urine"),
        _target_chip("kidney stone", "kidney stone"),
        _target_chip("urine rukna", "urine retention"),
        _consultation_chip(),
    ],
    "peshab": [
        _target_chip("peshab me jalan", "urine burning"),
        _target_chip("peshab me khoon", "blood in urine"),
        _target_chip("pathri", "kidney stone"),
        _target_chip("peshab rukna", "urine retention"),
        _consultation_chip(),
    ],
    "ghutna": [
        _target_chip("ghutne mein dard", "knee pain"),
        _target_chip("ghutne ki chot", "knee injury"),
        _target_chip("knee replacement", "knee replacement"),
        _target_chip("ligament tear", "ligament tear"),
        _consultation_chip(),
    ],
    "knee": [
        _target_chip("knee pain", "knee pain"),
        _target_chip("knee injury", "knee injury"),
        _target_chip("knee replacement", "knee replacement"),
        _target_chip("ligament tear", "ligament tear"),
        _consultation_chip(),
    ],
}


def _normalized(query: str) -> str:
    return " ".join(query.lower().strip().split())


def _contains_any(query: str, terms: tuple[str, ...]) -> bool:
    return any(term in query for term in terms)


def _has_ambiguous_stone_intent(query: str) -> bool:
    has_broad_stone = _contains_any(query, BROAD_STONE_TERMS)
    has_specific_stone = _contains_any(query, SPECIFIC_STONE_TERMS)
    return has_broad_stone and not has_specific_stone


def _is_broad_symptom_query(query: str) -> bool:
    tokens = set(query.split())
    if query in BROAD_SYMPTOM_TERMS:
        return True
    if "not feeling well" in query:
        return len(tokens) <= 4

    broad_tokens = {
        "body",
        "pain",
        "dard",
        "badan",
        "sharir",
        "weakness",
        "kamzori",
        "thakan",
        "tired",
        "fatigue",
        "fever",
        "bukhar",
    }
    filler_tokens = {"me", "mein", "mai", "hai", "ho", "raha", "rahi", "lag", "lagti", "lagta"}
    return bool(tokens) and tokens <= broad_tokens | filler_tokens and bool(tokens & broad_tokens)


def _broad_symptom_clarification(results: list[dict]) -> JourneyDecision:
    return JourneyDecision(
        state="needs_clarification",
        title="We need one more detail",
        message="This can happen for many reasons. Choose the closest symptom area so we can guide you better.",
        primary_result=results[0] if results else None,
        alternatives=results[1:4] if len(results) > 1 else [],
        clarifier_question="Where are you feeling the problem most?",
        clarifier_chips=[
            _target_chip("Stomach / abdomen", "stomach pain"),
            _target_chip("Urine / kidney area", "kidney stone pain"),
            _target_chip("Back or spine", "back pain"),
            _target_chip("Knee / joints", "knee pain"),
            _target_chip("Chest", "chest pain"),
            _consultation_chip(),
        ],
        safety_note="This is only a search guide, not a diagnosis.",
    )


def _top_score(results: list[dict]) -> float:
    if not results:
        return 0.0
    return float(results[0].get("score", 0.0) or 0.0)


def _top_bm25_score(results: list[dict]) -> float:
    if not results:
        return 0.0
    return float(results[0].get("bm25_score", 0.0) or 0.0)


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


def _clarifier_chips_for(query: str) -> list[str | dict]:
    chips: list[str | dict] = []
    seen_labels: set[str] = set()
    for term, term_chips in BROAD_BODY_PART_CHIPS.items():
        if term in query:
            for chip in term_chips:
                label = chip.get("label", "") if isinstance(chip, dict) else chip
                if label and label not in seen_labels:
                    chips.append(chip)
                    seen_labels.add(label)
    return chips[:6] or [
        _target_chip("pain", "pain"),
        _target_chip("bleeding", "bleeding"),
        _target_chip("swelling", "swelling"),
        _target_chip("infection", "infection"),
        _target_chip("operation", "operation"),
        _consultation_chip("doctor consult"),
    ]


def route_patient_intent(query: str, results: list[dict]) -> JourneyDecision:
    normalized_query = _normalized(query)
    top_score = _top_score(results)
    top_bm25_score = _top_bm25_score(results)
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
            clarifier_chips=[
                _target_chip("Kidney / urine stone", "kidney stone"),
                _target_chip("Gallbladder stone", "gallstone"),
                _consultation_chip(),
            ],
            safety_note="This is only a search guide, not a diagnosis.",
        )

    has_specific_stone_intent = (
        _contains_any(normalized_query, BROAD_STONE_TERMS)
        and _contains_any(normalized_query, SPECIFIC_STONE_TERMS)
    )
    has_clear_treatment = _contains_any(normalized_query, CLEAR_TREATMENT_TERMS) or has_specific_stone_intent
    has_broad_body_part = any(term in normalized_query for term in BROAD_BODY_PART_CHIPS)

    if _is_broad_symptom_query(normalized_query) and not has_clear_treatment:
        return _broad_symptom_clarification(results)

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

    if not has_clear_treatment and top_bm25_score < 0.5:
        return _doctor_fallback(query, results, "Your search does not clearly match an available treatment.")

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
