#!/usr/bin/env python3
r"""
Add \index{} markers to the first occurrence of each glossary term in text.md

This script:
1. Extracts term names from glossary.tex
2. Finds the first occurrence of each term in text.md
3. Adds an \index{} marker after the first occurrence
"""

import re
from pathlib import Path


def extract_glossary_terms(glossary_file: Path) -> list[tuple[str, str]]:
    """
    Extract term names from glossary.tex.
    Returns list of (index_key, search_pattern) tuples.
    """
    terms = []
    content = glossary_file.read_text()

    # Find all \newglossaryentry{key}{name=...} entries
    pattern = r'\\newglossaryentry\{([^}]+)\}\s*\{\s*name=([^,}]+)'

    for match in re.finditer(pattern, content):
        key = match.group(1)
        name = match.group(2).strip()

        # Clean up the name for searching
        # Remove LaTeX commands like \texttt{}
        clean_name = re.sub(r'\\texttt\{([^}]+)\}', r'\1', name)
        clean_name = re.sub(r'\\[a-z]+\{([^}]+)\}', r'\1', clean_name)
        clean_name = clean_name.replace(r'\_', '_')

        terms.append((key, clean_name))

    return terms


def find_and_mark_first_occurrence(text: str, terms: list[tuple[str, str]]) -> str:
    r"""
    Find the first occurrence of each term and add \index{} marker.

    Strategy:
    - Skip front matter (before first # heading)
    - Skip code blocks (between ``` markers)
    - Find first occurrence in regular text
    - Add \index{term} right after the term
    """
    lines = text.split('\n')
    marked = set()  # Track which terms we've already marked
    result = []

    in_code_block = False
    past_front_matter = False

    for line in lines:
        # Track code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result.append(line)
            continue

        # Track when we're past front matter
        if line.startswith('#'):
            past_front_matter = True

        # Don't modify code blocks or front matter
        if in_code_block or not past_front_matter:
            result.append(line)
            continue

        # Try to mark terms in this line
        modified_line = line
        for key, term in terms:
            if key in marked:
                continue

            # Case-insensitive search, but preserve original case
            # Look for word boundaries to avoid partial matches
            # Escape special regex characters in term
            escaped_term = re.escape(term)
            pattern = r'\b(' + escaped_term + r')\b'

            match = re.search(pattern, modified_line, re.IGNORECASE)
            if match:
                # Add index marker right after the first occurrence
                matched_text = match.group(1)
                replacement = matched_text + r'\index{' + key + '}'
                modified_line = modified_line[:match.start()] + replacement + modified_line[match.end():]
                marked.add(key)
                print(f"Marked '{term}' (key: {key}) in: {line[:60]}...")

        result.append(modified_line)

    return '\n'.join(result)


def main():
    book_dir = Path(__file__).parent
    glossary_file = book_dir / 'glossary.tex'
    text_file = book_dir / 'text.md'

    if not glossary_file.exists():
        print(f"Error: {glossary_file} not found")
        return 1

    if not text_file.exists():
        print(f"Error: {text_file} not found")
        return 1

    print("Extracting glossary terms...")
    terms = extract_glossary_terms(glossary_file)
    print(f"Found {len(terms)} glossary terms")

    print("\nReading text.md...")
    text = text_file.read_text()

    print("\nSearching for first occurrences and adding index markers...")
    modified_text = find_and_mark_first_occurrence(text, terms)

    # Backup original
    backup_file = text_file.with_suffix('.md.backup')
    text_file.rename(backup_file)
    print(f"\nOriginal backed up to {backup_file}")

    # Write modified version
    text_file.write_text(modified_text)
    print(f"Modified text written to {text_file}")
    print("\nDone! Rebuild the book with 'make' to see the index populated.")

    return 0


if __name__ == '__main__':
    exit(main())
