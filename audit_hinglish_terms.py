"""Remove clinically contradictory Hinglish terms from catalog.py."""

from __future__ import annotations

import json
import os
import pprint
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from catalog import CATALOG


MODEL = "gpt-4o-mini"
CATALOG_FILE = Path("catalog.py")


SYSTEM_PROMPT = """You are a clinical search relevance auditor.
Your job is to remove Hinglish search terms that are clinically opposite or contradictory to the treatment.
Be conservative: remove only terms that clearly describe the opposite intent, wrong clinical direction, or a condition this treatment is not for.
Do not remove broad but related symptoms unless they are clearly contradictory.
Return only valid JSON."""


def normalize_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    terms = []
    for item in value:
        if not isinstance(item, str):
            continue
        item = " ".join(item.strip().lower().split())
        if item and item not in terms:
            terms.append(item)
    return terms


def audit_item(client: OpenAI, item: dict) -> tuple[list[str], list[str]]:
    terms = normalize_list(item.get("hinglish_terms", []))
    prompt = f"""Treatment: {item.get("name", "")}
Description: {item.get("description", "")}
Hinglish search terms: {json.dumps(terms, ensure_ascii=False)}

Check if any of the Hinglish terms describe symptoms or conditions that are CLINICALLY OPPOSITE to what this treatment does.

Example: A "Tubectomy" (female sterilization) should NOT have terms like "bacha nahi ho raha" because tubectomy is for people who don't want babies, not for infertility.

Return JSON: {{"keep": [terms to keep], "remove": [terms that contradict the treatment]}}.
If all terms are appropriate, return {{"keep": [all terms], "remove": []}}."""

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            payload = json.loads(response.choices[0].message.content)
            keep = normalize_list(payload.get("keep"))
            remove = normalize_list(payload.get("remove"))

            original_set = set(terms)
            keep = [term for term in keep if term in original_set]
            remove = [term for term in remove if term in original_set]
            remove_set = set(remove)
            if not keep:
                keep = [term for term in terms if term not in remove_set]
            return keep, remove
        except Exception as exc:
            if attempt == 2:
                raise
            wait = 2**attempt
            print(f"Audit failed for {item.get('slug')} ({exc}); retrying in {wait}s...", flush=True)
            time.sleep(wait)
    return terms, []


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


def main() -> None:
    load_dotenv(override=True)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    catalog = [dict(item) for item in CATALOG]
    removals: list[tuple[str, str, list[str]]] = []

    for index, item in enumerate(catalog, 1):
        keep, remove = audit_item(client, item)
        if remove:
            item["hinglish_terms"] = keep
            removals.append((item.get("slug", ""), item.get("name", ""), remove))
            print(f"Removed from {item.get('slug')}: {remove}", flush=True)
        if index % 50 == 0 or index == len(catalog):
            print(f"Audited {index}/{len(catalog)} entries...", flush=True)

    write_catalog(catalog)
    print(f"Saved audited catalog to {CATALOG_FILE}")
    print(f"Treatments with terms removed: {len(removals)}")
    if removals:
        print("REMOVALS_SUMMARY")
        for slug, name, removed in removals:
            print(f"{slug}\t{name}\t{', '.join(removed)}")


if __name__ == "__main__":
    main()
