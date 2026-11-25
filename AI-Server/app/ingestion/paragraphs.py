import re
from typing import Any


def split_paragraphs(page_text: str) -> list[str]:
    normalized = page_text.replace("\x00", " ").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n+", normalized)
    output = []
    for block in blocks:
        text = re.sub(r"[\t ]+", " ", block)
        text = re.sub(r"\n+", " ", text).strip()
        if len(text) >= 35:
            output.append(text)
    return output


def build_records(doc: dict[str, Any], pages: list[str], revision: str) -> list[dict[str, Any]]:
    records = []
    ordinal = 0
    for page_number, page_text in enumerate(pages, start=1):
        for paragraph in split_paragraphs(page_text):
            ordinal += 1
            pid = f"{doc['document_id']}-p{page_number:04d}-para{ordinal:06d}"
            records.append({
                "paragraph_id": pid,
                "document_id": doc["document_id"],
                "corpus_revision": revision,
                "document_title": doc["document_title"],
                "pdf_page_number": page_number,
                "printed_page_label": None,
                "original_section_label": None,
                "original_paragraph_label": None,
                "derived_locator": f"Extracted paragraph {ordinal} on PDF page {page_number}.",
                "exact_text": paragraph,
                "official_source_url": doc["official_source_url"],
                "synthetic": False,
            })
    return records
