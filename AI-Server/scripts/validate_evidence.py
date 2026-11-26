#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FIELDS = [
    "document_id",
    "document_title",
    "pdf_path",
    "official_source_url",
]

PLACEHOLDERS = [
    "example",
    "placeholder",
    "your-url",
    "test.com",
]


def validate_manifest(manifest_path: Path) -> bool:

    errors = []
    warnings = []

    if not manifest_path.is_file():
        print(f"ERROR: Manifest not found: {manifest_path}")
        return False

    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON: {exc}")
        return False

    revision = manifest.get("corpus_revision")
    documents = manifest.get("documents", [])

    if not revision:
        errors.append("Missing corpus_revision.")

    if not isinstance(documents, list):
        errors.append("'documents' must be a list.")
        documents = []

    if not 3 <= len(documents) <= 5:
        errors.append("Expected between 3 and 5 documents.")

    seen_ids = set()
    seen_paths = set()
    seen_urls = set()

    print("\nSATYA EVIDENCE VALIDATION")
    print("=" * 45)

    for number, doc in enumerate(documents, start=1):

        print(f"\nChecking document {number}...")

        if not isinstance(doc, dict):
            errors.append(f"Document {number} is not an object.")
            continue

        for field in REQUIRED_FIELDS:
            if not doc.get(field):
                errors.append(
                    f"Document {number}: Missing {field}."
                )

        if any(not doc.get(field) for field in REQUIRED_FIELDS):
            continue

        document_id = doc["document_id"]
        pdf_path_value = doc["pdf_path"]
        source_url = doc["official_source_url"]

        if document_id in seen_ids:
            errors.append(f"Duplicate document ID: {document_id}")

        seen_ids.add(document_id)

        if len(document_id) > 70:
            errors.append(
                f"{document_id}: Document ID exceeds 70 characters."
            )

        pdf_path = (
            manifest_path.parent / pdf_path_value
        ).resolve()

        if pdf_path in seen_paths:
            errors.append(f"Duplicate PDF path: {pdf_path}")

        seen_paths.add(pdf_path)

        if not pdf_path.is_file():
            errors.append(f"PDF does not exist: {pdf_path}")
            continue

        if pdf_path.suffix.lower() != ".pdf":
            errors.append(f"Not a PDF file: {pdf_path}")
            continue

        try:
            reader = PdfReader(str(pdf_path))
            page_count = len(reader.pages)

            if page_count == 0:
                errors.append(
                    f"{document_id}: PDF has no pages."
                )
            else:
                print(f"  PDF: OK ({page_count} pages)")

        except Exception as exc:
            errors.append(
                f"{document_id}: Cannot read PDF: {exc}"
            )

        parsed_url = urlparse(source_url)

        if parsed_url.scheme != "https" or not parsed_url.hostname:
            errors.append(
                f"{document_id}: Invalid HTTPS source URL."
            )
        elif any(
            word in source_url.lower()
            for word in PLACEHOLDERS
        ):
            errors.append(
                f"{document_id}: Placeholder URL detected."
            )

        if source_url in seen_urls:
            warnings.append(
                f"Repeated source URL: {source_url}"
            )

        seen_urls.add(source_url)

        if parsed_url.hostname and not (
            parsed_url.hostname.endswith(".gov.in")
            or parsed_url.hostname == "gov.in"
            or parsed_url.hostname.endswith(".nic.in")
            or parsed_url.hostname == "nic.in"
        ):
            warnings.append(
                f"{document_id}: Verify official domain "
                f"({parsed_url.hostname})."
            )

    print("\n" + "=" * 45)

    for warning in warnings:
        print(f"WARNING: {warning}")

    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print("\nVALIDATION FAILED.")
        return False

    print("\nVALIDATION PASSED.")
    print("Manifest structure and local PDFs look valid.")
    print("Official source authenticity still requires manual review.")

    return True


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Usage: python scripts/validate_evidence.py "
            "<manifest.json>"
        )
        sys.exit(1)

    manifest_file = Path(sys.argv[1]).resolve()

    success = validate_manifest(manifest_file)

    sys.exit(0 if success else 1)