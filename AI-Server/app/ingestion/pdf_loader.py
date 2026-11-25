from pathlib import Path
from pypdf import PdfReader


def extract_pages(pdf_path: Path) -> list[str]:
    reader = PdfReader(str(pdf_path))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise ValueError(f"Encrypted PDF cannot be read: {pdf_path.name}") from exc
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            pages.append(page.extract_text(extraction_mode="layout") or "")
        except Exception as exc:
            raise ValueError(f"Text extraction failed on page {page_number} of {pdf_path.name}") from exc
    return pages
