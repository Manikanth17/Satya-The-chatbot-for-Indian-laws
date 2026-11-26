import re
from typing import Any


# Detect numbered rule headings, including headings embedded
# in the middle of an extracted PDF line.
RULE_HEADING = re.compile(
    r"(?<![\w.])(\d{1,2})\.\s+"
    r"(?=[A-Z][A-Za-z]*(?:\s|[.—:-]))"
)

ALPHA_CLAUSE_START = re.compile(
    r"^\s*\([a-z]\)\s+",
    re.IGNORECASE
)

ROMAN_CLAUSE_START = re.compile(
    r"^\s*\([ivxlcdm]+\)\s+",
    re.IGNORECASE
)

PROVISO_START = re.compile(
    r"^\s*Provided\s+(?:further\s+)?that\b",
    re.IGNORECASE
)


def split_paragraphs(page_text: str) -> list[str]:
    normalized = (
        page_text
        .replace("\x00", " ")
        .replace("\r", "\n")
    )

    # Insert a line break before numbered rule headings
    # that appear in the middle of an extracted line.
    normalized = RULE_HEADING.sub(
        lambda match: "\n" + match.group(0),
        normalized
    )

    lines = normalized.splitlines()

    output = []
    current = []

    def save_current():
        if not current:
            return

        text = " ".join(current)
        text = re.sub(r"[\t ]+", " ", text).strip()

        if len(text) >= 35:
            output.append(text)

        current.clear()

    for line in lines:
        stripped = line.strip()

        if not stripped:
            save_current()
            continue

        is_new_provision = (
    RULE_HEADING.match(stripped)
    or ALPHA_CLAUSE_START.match(stripped)
    or ROMAN_CLAUSE_START.match(stripped)
    or PROVISO_START.match(stripped)
)

        if is_new_provision:
            save_current()

        current.append(stripped)

    save_current()

    return output


def build_records(
    doc: dict[str, Any],
    pages: list[str],
    revision: str
) -> list[dict[str, Any]]:

    records = []
    ordinal = 0

    for page_number, page_text in enumerate(pages, start=1):

        for paragraph in split_paragraphs(page_text):
            ordinal += 1

            pid = (
                f"{doc['document_id']}-p{page_number:04d}"
                f"-para{ordinal:06d}"
            )

            records.append({
                "paragraph_id": pid,
                "document_id": doc["document_id"],
                "corpus_revision": revision,
                "document_title": doc["document_title"],
                "pdf_page_number": page_number,
                "printed_page_label": None,
                "original_section_label": None,
                "original_paragraph_label": None,
                "derived_locator": (
                    f"Extracted paragraph {ordinal} "
                    f"on PDF page {page_number}."
                ),
                "exact_text": paragraph,
                "official_source_url": doc["official_source_url"],
                "synthetic": False,
            })

    return records