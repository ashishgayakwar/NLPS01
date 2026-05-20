"""Conservative patient query normalization before retrieval/routing."""

import re


EXACT_REPLACEMENTS = {
    "bodypain": "body pain",
    "chestpain": "chest pain",
    "kidneystone": "kidney stone",
    "gallbladderstone": "gallbladder stone",
    "kharate": "kharrate",
}


def normalize_query(raw_query: str) -> str:
    """Normalize only small, high-confidence query variants."""
    normalized = re.sub(r"\s+", " ", (raw_query or "").strip().lower())
    return EXACT_REPLACEMENTS.get(normalized, normalized)
