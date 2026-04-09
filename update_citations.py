#!/usr/bin/env python3
"""
Update citation counts in _bibliography/publications.bib using Google Scholar.

Usage:
    pip install scholarly
    python update_citations.py

This script:
1. Parses all BibTeX entries in publications.bib
2. Searches Google Scholar for each paper by title
3. Updates the `citations = {N}` field in the .bib file with the real count

Note: Google Scholar may rate-limit frequent requests. If you get blocked,
wait a few minutes and try again, or use a VPN/proxy.
"""

import re
import time
import sys

try:
    from scholarly import scholarly
except ImportError:
    print("Error: 'scholarly' package not found.")
    print("Install it with:  pip install scholarly")
    sys.exit(1)

BIB_FILE = "_bibliography/publications.bib"
STATS_FILE = "_data/scholar_stats.yml"

# Prefixes to strip before searching Scholar
TITLE_PREFIXES = ["[ABSTRACT] ", "[PRE-PRINT] "]


def clean_title(title: str) -> str:
    for prefix in TITLE_PREFIXES:
        title = title.replace(prefix, "")
    return title.strip()


def fetch_citations(title: str) -> int | None:
    """Search Google Scholar for a paper by title and return its citation count."""
    query = clean_title(title)
    try:
        results = scholarly.search_pubs(query)
        pub = next(results, None)
        if pub is None:
            return None
        return pub.get("num_citations", 0)
    except Exception as e:
        print(f"  Warning: Scholar query failed — {e}")
        return None


def update_bib_citations(bib_path: str) -> None:
    with open(bib_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all entries: capture key and full entry body
    entry_pattern = re.compile(
        r"(@\w+\s*\{([^,]+),)(.*?)(?=\n@|\Z)", re.DOTALL
    )

    updated_content = content
    entries = list(entry_pattern.finditer(content))

    if not entries:
        print("No BibTeX entries found.")
        return

    print(f"Found {len(entries)} entries. Fetching citation counts...\n")

    for match in entries:
        entry_text = match.group(0)
        entry_key = match.group(2).strip()

        # Extract title
        title_match = re.search(r'title\s*=\s*[{"](.*?)[}"],?\s*\n', entry_text, re.DOTALL)
        if not title_match:
            print(f"[{entry_key}] Could not find title, skipping.")
            continue

        raw_title = title_match.group(1).replace("\n", " ").strip()
        print(f"[{entry_key}] Searching: {clean_title(raw_title)[:70]}...")

        count = fetch_citations(raw_title)

        if count is None:
            print(f"  -> No result found, keeping existing value.")
            # Add a small delay before next request
            time.sleep(2)
            continue

        print(f"  -> {count} citations")

        # Replace the citations field in this entry
        citations_pattern = re.compile(r'(citations\s*=\s*\{)\d+(\})', re.MULTILINE)
        if citations_pattern.search(entry_text):
            new_entry = citations_pattern.sub(rf'\g<1>{count}\2', entry_text)
        else:
            # Add citations field before the closing brace of the entry
            new_entry = re.sub(
                r'(\n})',
                f'\n  citations     = {{{count}}},\n}}',
                entry_text,
                count=1
            )

        updated_content = updated_content.replace(entry_text, new_entry, 1)

        # Be polite to Google Scholar — avoid rate limiting
        time.sleep(3)

    with open(bib_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    # Recompute total and update scholar_stats.yml
    total = sum(int(m) for m in re.findall(r'citations\s*=\s*\{(\d+)\}', updated_content))
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        f.write(f"total_citations: {total}\n")

    print(f"Done. Updated {bib_path} and {STATS_FILE} (total citations: {total})")


if __name__ == "__main__":
    update_bib_citations(BIB_FILE)
