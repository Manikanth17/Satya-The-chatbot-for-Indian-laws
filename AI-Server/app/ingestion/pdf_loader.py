from pathlib import Path

from pypdf import PdfReader


# Pages that require OCR even if PyPDF extracts some text.
# Page numbers are 1-based.
OCR_REQUIRED_PAGES = {
    "rti-rules-2012.pdf": {2,3,4},
    "rti-fee-cost-rules-2005.pdf": {1, 2},
    "rti-fee-cost-amendment-2006.pdf": {2},
}


# Pages containing Hindi text that we are not currently
# processing with English OCR.
OCR_SKIP_PAGES = {
    "rti-fee-cost-rules-2005.pdf": {3, 4},
    "rti-fee-cost-amendment-2006.pdf": {1},
}


MIN_TEXT_LENGTH = 40


def run_ocr(pdf_path: Path, page_number: int) -> str:
    """Extract English text from a specific PDF page using OCR."""

    try:
        import pytesseract
        from pdf2image import convert_from_path

        images = convert_from_path(
            str(pdf_path),
            dpi=300,
            first_page=page_number,
            last_page=page_number,
        )

        if not images:
            raise ValueError("PDF page could not be converted to an image")

        return pytesseract.image_to_string(
            images[0],
            lang="eng",
            config="--psm 6",
        ).strip()

    except ImportError as exc:
        raise RuntimeError(
            "OCR dependencies missing. Run: "
            "python -m pip install -r requirements-ocr.txt"
        ) from exc

    except Exception as exc:
        raise RuntimeError(
            f"OCR failed on page {page_number} "
            f"of {pdf_path.name}: {exc}"
        ) from exc


def extract_pages(pdf_path: Path) -> list[str]:
    """
    Extract PDF text using PyPDF with OCR fallback.

    Known unreliable pages are processed using OCR.
    Pages with insufficient selectable text also use OCR.
    Known Hindi pages are skipped to avoid unreliable English OCR.

    Original PDF page numbering is preserved.
    """

    reader = PdfReader(str(pdf_path))

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise ValueError(
                f"Encrypted PDF cannot be read: {pdf_path.name}"
            ) from exc

    pages = []

    required_pages = OCR_REQUIRED_PAGES.get(pdf_path.name, set())
    skipped_pages = OCR_SKIP_PAGES.get(pdf_path.name, set())

    for page_number, page in enumerate(reader.pages, start=1):

        if page_number in skipped_pages:
            print(
                f"[SKIP] {pdf_path.name}, page {page_number}: "
                "English OCR not enabled for this page."
            )
            pages.append("")
            continue

        force_ocr = page_number in required_pages

        try:
            text = page.extract_text(extraction_mode="layout") or ""

        except Exception as exc:
            raise ValueError(
                f"Text extraction failed on page {page_number} "
                f"of {pdf_path.name}"
            ) from exc

        needs_ocr = (
            force_ocr
            or len(text.strip()) < MIN_TEXT_LENGTH
        )

        if needs_ocr:
            reason = "known unreliable extraction" if force_ocr else "insufficient text"

            print(
                f"[OCR] {pdf_path.name}, page {page_number}: {reason}"
            )

            text = run_ocr(pdf_path, page_number)

        else:
            print(
                f"[PDF TEXT] {pdf_path.name}, page {page_number}"
            )

        pages.append(text.strip())

    return pages