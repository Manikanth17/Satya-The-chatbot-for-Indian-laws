"""Optional OCR helper for scanned PDFs; requires Tesseract installed separately."""
from __future__ import annotations
from pathlib import Path

def extract_scanned_pdf(path: str | Path, languages: str = "eng") -> list[dict]:
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError as exc:
        raise RuntimeError("Install OCR extras from requirements-ocr.txt") from exc
    pages = convert_from_path(str(path))
    result = []
    for page_number, image in enumerate(pages, 1):
        text = pytesseract.image_to_string(image, lang=languages).strip()
        result.append({"page_number": page_number, "text": text, "ocr": True})
    return result
