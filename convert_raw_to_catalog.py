"""Convert scraped Pristyn records into catalog.py format."""

from __future__ import annotations

import json
import pprint
from collections import defaultdict
from pathlib import Path


RAW_FILE = Path("pristyn_treatments_raw.json")
CATALOG_FILE = Path("catalog.py")


def compact_join(*parts: str | None) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def category_from_breadcrumb(record: dict) -> str:
    breadcrumb = [part for part in record.get("breadcrumb", []) if part]
    if len(breadcrumb) >= 3:
        return breadcrumb[-2]
    return ""


def build_catalog(records: list[dict]) -> list[dict]:
    by_slug: dict[str, dict[str, dict]] = defaultdict(dict)
    for record in records:
        slug = record.get("slug")
        lang = record.get("lang")
        if slug and lang in {"en", "hi"}:
            by_slug[slug][lang] = record

    catalog = []
    for index, slug in enumerate(sorted(slug for slug, langs in by_slug.items() if "en" in langs), 1):
        english = by_slug[slug]["en"]
        hindi = by_slug[slug].get("hi")

        english_intro = (english.get("intro_paragraphs") or [""])[0]
        hindi_intro = (hindi.get("intro_paragraphs") or [""])[0] if hindi else ""

        catalog.append(
            {
                "id": index,
                "name": english.get("h1") or "",
                "hindi_name": (hindi.get("h1") or "") if hindi else "",
                "slug": slug,
                "url": english.get("url") or "",
                "description": compact_join(english.get("meta_description"), english_intro),
                "hindi_description": compact_join(hindi.get("meta_description"), hindi_intro) if hindi else "",
                "category": category_from_breadcrumb(english),
            }
        )
    return catalog


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
        item.get("description", ""),
        item.get("hindi_description", ""),
        item.get("category", ""),
    ]
    return " | ".join(part for part in parts if part)
''',
        encoding="utf-8",
    )


def main() -> None:
    records = json.loads(RAW_FILE.read_text(encoding="utf-8"))
    catalog = build_catalog(records)
    write_catalog(catalog)
    print(f"Wrote {len(catalog)} catalog entries to {CATALOG_FILE}")


if __name__ == "__main__":
    main()
