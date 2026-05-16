"""
Scrape Pristyn Care treatment pages into a reviewable raw JSON file.

Inputs:
- english_slugs.txt

Outputs:
- pristyn_treatments_raw.json
- scrape_errors.log
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag


BASE_URL = "https://www.pristyncare.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
SLUGS_FILE = Path("english_slugs.txt")
OUTPUT_FILE = Path("pristyn_treatments_raw.json")
ERRORS_FILE = Path("scrape_errors.log")
USER_AGENT = "Pristyn-Internal-Catalog-Scraper/1.0"
TIMEOUT_SECONDS = 15
REQUEST_DELAY_SECONDS = 1


session = requests.Session()
session.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
    }
)


def load_slugs() -> list[str]:
    if not SLUGS_FILE.exists():
        raise FileNotFoundError(f"Missing {SLUGS_FILE}")
    return [line.strip() for line in SLUGS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


def sitemap_locs(xml_text: str) -> list[str]:
    import xml.etree.ElementTree as ET

    root = ET.fromstring(xml_text)
    locs = []
    for elem in root.iter():
        if elem.tag.split("}", 1)[-1] == "loc" and elem.text:
            locs.append(elem.text.strip())
    return locs


def is_sitemap_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return "sitemap" in path and path.endswith((".xml", ".xml.gz"))


def discover_hindi_treatment_slugs() -> set[str]:
    """Use sitemap XML to avoid probing hundreds of missing Hindi pages."""
    slugs: set[str] = set()
    seen: set[str] = set()
    queue = [SITEMAP_URL]
    while queue:
        sitemap_url = queue.pop(0)
        if sitemap_url in seen:
            continue
        seen.add(sitemap_url)
        try:
            response = session.get(sitemap_url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.RequestException:
            continue
        for loc in sitemap_locs(response.text):
            if is_sitemap_url(loc):
                if loc not in seen and loc not in queue:
                    queue.append(loc)
                continue
            parts = [part for part in urlparse(loc).path.split("/") if part]
            lower = [part.lower() for part in parts]
            if len(parts) == 3 and lower[0] == "hi" and lower[1] == "treatment":
                slugs.add(parts[2])
    return slugs


def polite_sleep() -> None:
    time.sleep(REQUEST_DELAY_SECONDS)


def fetch(url: str) -> tuple[int | None, str | None, str | None]:
    """Return (status_code, html, error). Retry once on 5xx."""
    last_error = None
    for attempt in range(2):
        if attempt:
            polite_sleep()
        try:
            response = session.get(url, timeout=TIMEOUT_SECONDS)
            if response.status_code >= 500 and attempt == 0:
                last_error = f"HTTP {response.status_code}; retrying once"
                continue
            if response.status_code != 200:
                return response.status_code, None, f"HTTP {response.status_code}"
            response.encoding = "utf-8"
            return response.status_code, response.text, None
        except requests.RequestException as exc:
            last_error = str(exc)
            if attempt == 0:
                continue
            return None, None, last_error
    return None, None, last_error


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def meta_content(soup: BeautifulSoup, **attrs: str) -> str | None:
    tag = soup.find("meta", attrs=attrs)
    if not tag:
        return None
    content = tag.get("content")
    return clean_text(content) if content else None


def looks_like_noise(text: str) -> bool:
    lowered = text.lower()
    noise_bits = (
        "book appointment",
        "call us",
        "select city",
        "choose city",
        "view all",
        "read more",
        "pristyn care",
        "consult doctor",
    )
    return any(bit in lowered for bit in noise_bits) and len(text.split()) < 18


def visible_paragraphs(container: Tag) -> Iterable[str]:
    for paragraph in container.find_all("p"):
        text = clean_text(paragraph.get_text(" ", strip=True))
        if len(text.split()) < 8:
            continue
        if looks_like_noise(text):
            continue
        yield text


def main_content_area(soup: BeautifulSoup) -> Tag:
    for selector in ("main", "article", '[role="main"]'):
        match = soup.select_one(selector)
        if match:
            return match

    candidates: list[tuple[int, Tag]] = []
    for tag in soup.find_all(["section", "div"]):
        class_id = " ".join(tag.get("class", [])) + " " + (tag.get("id") or "")
        class_id = class_id.lower()
        if any(skip in class_id for skip in ("nav", "footer", "header", "sidebar", "modal", "popup")):
            continue
        paragraph_count = sum(1 for _ in visible_paragraphs(tag))
        if paragraph_count:
            candidates.append((paragraph_count, tag))

    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    return soup.body or soup


def extract_breadcrumb(soup: BeautifulSoup) -> list[str]:
    selectors = [
        'nav[aria-label*="breadcrumb" i]',
        '[class*="breadcrumb" i]',
        '[id*="breadcrumb" i]',
    ]
    for selector in selectors:
        match = soup.select_one(selector)
        if not match:
            continue
        items = [clean_text(item.get_text(" ", strip=True)) for item in match.find_all(["a", "span", "li"])]
        items = [item for item in items if item and item not in {">", "/", "›", "»"} and len(item) <= 80]
        deduped: list[str] = []
        for item in items:
            if item not in deduped:
                deduped.append(item)
        if deduped:
            return deduped
    return []


def extract_page(url: str, lang: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    path_parts = [part for part in urlparse(url).path.split("/") if part]
    slug = path_parts[-1]
    h1_tag = soup.find("h1")
    breadcrumb = extract_breadcrumb(soup)
    meta_description = meta_content(soup, name="description")
    meta_keywords = meta_content(soup, name="keywords")
    og_title = meta_content(soup, property="og:title")

    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "aside", "form"]):
        tag.decompose()

    content = main_content_area(soup)
    intro_paragraphs = list(visible_paragraphs(content))[:3]

    return {
        "slug": slug,
        "url": url,
        "lang": lang,
        "h1": clean_text(h1_tag.get_text(" ", strip=True)) if h1_tag else None,
        "meta_description": meta_description,
        "meta_keywords": meta_keywords,
        "intro_paragraphs": intro_paragraphs,
        "breadcrumb": breadcrumb,
        "og_title": og_title,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def log_error(errors: list[str], url: str, reason: str) -> None:
    errors.append(f"{datetime.now(timezone.utc).isoformat()}\t{url}\t{reason}")


def write_outputs(records: list[dict], errors: list[str]) -> None:
    OUTPUT_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    ERRORS_FILE.write_text("\n".join(errors) + ("\n" if errors else ""), encoding="utf-8")


def main() -> None:
    slugs = load_slugs()
    hindi_slugs = discover_hindi_treatment_slugs()
    print(f"Discovered {len(hindi_slugs)} Hindi treatment slugs from sitemap.", flush=True)
    started = time.monotonic()
    records: list[dict] = []
    errors: list[str] = []
    english_scraped = 0
    hindi_scraped = 0

    for index, slug in enumerate(slugs, 1):
        print(f"Checking {index}/{len(slugs)}: {slug}", flush=True)
        english_url = f"{BASE_URL}/treatment/{slug}/"
        polite_sleep()
        status, html, error = fetch(english_url)
        if html:
            records.append(extract_page(english_url, "en", html))
            english_scraped += 1
            print("  en: 200", flush=True)
        else:
            log_error(errors, english_url, error or f"HTTP {status}")
            print(f"  en: {error or f'HTTP {status}'}", flush=True)

        if slug not in hindi_slugs:
            print("  hi: skipped (not in sitemap)", flush=True)
        else:
            hindi_url = f"{BASE_URL}/hi/treatment/{slug}/"
            polite_sleep()
            status, html, error = fetch(hindi_url)
            if html:
                records.append(extract_page(hindi_url, "hi", html))
                hindi_scraped += 1
                print("  hi: 200", flush=True)
            elif status == 404:
                print("  hi: 404 skipped", flush=True)
            else:
                log_error(errors, hindi_url, error or f"HTTP {status}")
                print(f"  hi: {error or f'HTTP {status}'}", flush=True)

        if index % 25 == 0 or index == len(slugs):
            write_outputs(records, errors)
            print(
                f"Scraped {index}/{len(slugs)} slugs... "
                f"English: {english_scraped}, Hindi: {hindi_scraped}, Failures: {len(errors)}",
                flush=True,
            )

    write_outputs(records, errors)

    elapsed = time.monotonic() - started
    print(f"Total English scraped: {english_scraped}")
    print(f"Total Hindi scraped: {hindi_scraped}")
    print(f"Total failures: {len(errors)}")
    print(f"Total time taken: {elapsed:.1f} seconds")
    print(f"Saved raw data to: {OUTPUT_FILE}")
    print(f"Saved errors to: {ERRORS_FILE}")


if __name__ == "__main__":
    main()
