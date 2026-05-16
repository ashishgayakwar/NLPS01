"""Add Hinglish search terms to catalog.py entries using OpenAI."""

from __future__ import annotations

import json
import os
import pprint
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from catalog import CATALOG


MODEL = "gpt-4o"
BATCH_SIZE = 20
CATALOG_FILE = Path("catalog.py")


SYSTEM_PROMPT = """You are generating Roman-script Hindi (Hinglish) search terms that real Indian patients type into Google when looking for treatment.

Rules:
- Output ONLY Roman-script Hindi phrases, not English-only medical terms and not Devanagari.
- Include common misspellings, e.g. bavasir, bawaseer, ghutney.
- Include symptom phrases, not just treatment names, e.g. "pet me jalan" not "acidity treatment".
- Include body part + problem combinations, e.g. "naak band", "ghutne mein dard", "kamar dard".
- Include vague or colloquial phrasings, e.g. "bacha nahi ho raha", "saans phulna".
- Generate 8-12 terms per treatment.
- Return only valid JSON in the shape requested by the user."""


def build_user_prompt(batch: list[dict]) -> str:
    compact = [
        {
            "slug": item["slug"],
            "name": item.get("name", ""),
            "hindi_name": item.get("hindi_name", ""),
            "description": item.get("description", "")[:500],
            "hindi_description": item.get("hindi_description", "")[:500],
        }
        for item in batch
    ]
    return (
        "Generate Hinglish terms for these entries. Return JSON in this exact shape: "
        '{"items":[{"slug":"...","terms":["term1","term2"]}]}.\n\n'
        'Examples:\n'
        '"Piles Treatment" -> ["bawasir", "bavasir", "bawaseer", "mulvyadh", "gudhe me dard", '
        '"khoon aana motion se", "piles ka ilaj", "bawasir ka operation", "anus me sujan"]\n'
        '"Septoplasty" -> ["naak band rehti hai", "naak ki haddi tedhi", "saans lene mein dikkat", '
        '"naak ka operation", "ek nathuna band", "nose surgery", "naak ke andar haddi"]\n'
        '"Snoring Treatment" -> ["kharrate", "kharrate ka ilaj", "raat ko kharrate", '
        '"neend mein saans rukna", "sote samay awaaz"]\n'
        '"IVF" -> ["bacha nahi ho raha", "bachcha nahi ho raha", "garbhdharan nahi ho raha", '
        '"santan sukh", "test tube baby", "infertility ka ilaj", "bachhe ke liye ilaj"]\n\n'
        "Entries:\n"
        + json.dumps(compact, ensure_ascii=False)
    )


def normalize_terms(terms: object) -> list[str]:
    if not isinstance(terms, list):
        return []
    cleaned = []
    for term in terms:
        if not isinstance(term, str):
            continue
        term = " ".join(term.strip().lower().split())
        if not term:
            continue
        if any("\u0900" <= char <= "\u097f" for char in term):
            continue
        if term not in cleaned:
            cleaned.append(term)
    return cleaned[:12]


def request_batch(client: OpenAI, batch: list[dict]) -> dict[str, list[str]]:
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(batch)},
                ],
            )
            payload = json.loads(response.choices[0].message.content)
            items = payload.get("items", [])
            return {
                item.get("slug"): normalize_terms(item.get("terms"))
                for item in items
                if isinstance(item, dict) and item.get("slug")
            }
        except Exception as exc:
            if attempt == 2:
                raise
            wait = 2**attempt
            print(f"Batch failed ({exc}); retrying in {wait}s...", flush=True)
            time.sleep(wait)
    return {}


def write_catalog(catalog: list[dict]) -> None:
    rendered_catalog = pprint.pformat(catalog, width=120, sort_dicts=False)
    CATALOG_FILE.write_text(
        f'''"""
Pristyn Care treatment catalog generated from pristyn_treatments_raw.json.
"""

CATALOG = {rendered_catalog}


def get_searchable_text(item):
    """Combine all fields into one rich text for embedding."""
    parts = [
        item.get("name", ""),
        item.get("hindi_name", ""),
        item.get("slug", ""),
        " ".join(item.get("hinglish_terms", [])),
        item.get("description", ""),
        item.get("hindi_description", ""),
        item.get("category", ""),
    ]
    return " | ".join(part for part in parts if part)
''',
        encoding="utf-8",
    )


def fallback_terms(item: dict) -> list[str]:
    slug = item.get("slug", "")
    base = slug.replace("-", " ")
    terms = [base, f"{base} ka ilaj", f"{base} treatment", f"{base} operation", f"{base} surgery"]
    return normalize_terms(terms)


def main() -> None:
    load_dotenv(override=True)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    catalog = [dict(item) for item in CATALOG]

    processed = 0
    next_progress = 50
    for start in range(0, len(catalog), BATCH_SIZE):
        batch = catalog[start:start + BATCH_SIZE]
        generated = request_batch(client, batch)
        for item in batch:
            terms = generated.get(item["slug"]) or fallback_terms(item)
            item["hinglish_terms"] = terms
        processed += len(batch)
        if processed >= next_progress or processed == len(catalog):
            print(f"Enriched {processed}/{len(catalog)} entries...", flush=True)
            while next_progress <= processed:
                next_progress += 50

    write_catalog(catalog)
    print(f"Saved enriched catalog with {len(catalog)} entries to {CATALOG_FILE}")


if __name__ == "__main__":
    main()
