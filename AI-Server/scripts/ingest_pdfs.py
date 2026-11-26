#!/usr/bin/env python3
"""Build SATYA's evidence bundle and local retrieval index."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ingestion.pdf_loader import extract_pages
from app.ingestion.paragraphs import build_records


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)

    cli.add_argument(
        "--manifest",
        required=True,
        help="JSON manifest describing 3–5 official PDF documents."
    )

    mode = cli.add_mutually_exclusive_group(required=True)

    mode.add_argument(
        "--draft",
        action="store_true",
        help="Generate an unreviewed draft evidence bundle."
    )

    mode.add_argument(
        "--reviewed",
        action="store_true",
        help="Generate a bundle marked as manually reviewed."
    )

    cli.add_argument(
        "--out",
        default=None,
        help="Optional output directory."
    )

    args = cli.parse_args()

    is_reviewed = args.reviewed

    # Select output directory.
    if args.out:
        output_dir = Path(args.out).resolve()
    elif is_reviewed:
        output_dir = ROOT / "data"
    else:
        output_dir = ROOT / "data" / "draft"

    # Load manifest.
    manifest_path = Path(args.manifest).resolve()

    if not manifest_path.is_file():
        cli.error(f"Manifest not found: {manifest_path}")

    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        cli.error(f"Invalid manifest JSON: {exc}")

    revision = manifest.get("corpus_revision", "").strip()
    docs = manifest.get("documents", [])

    if not revision or not isinstance(docs, list) or not 3 <= len(docs) <= 5:
        cli.error(
            "Manifest must contain corpus_revision and 3–5 documents."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    bundle_docs = []
    all_paragraphs = []
    seen_ids = set()

    # Process documents.
    for doc in docs:

        if not isinstance(doc, dict):
            cli.error("Each document must be a JSON object.")

        required = [
            "document_id",
            "document_title",
            "pdf_path",
            "official_source_url"
        ]

        missing = [
            key for key in required
            if not doc.get(key)
        ]

        if missing:
            cli.error(
                f"Document is missing fields: {', '.join(missing)}"
            )

        document_id = doc["document_id"]

        if len(document_id) > 70:
            cli.error(
                f"Document ID exceeds 70 characters: {document_id}"
            )

        if document_id in seen_ids:
            cli.error(f"Duplicate document ID: {document_id}")

        seen_ids.add(document_id)

        # Validate PDF.
        pdf_path = (
            manifest_path.parent / doc["pdf_path"]
        ).resolve()

        if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
            cli.error(f"PDF not found or invalid: {pdf_path}")

        # Validate source URL format.
        url = urlparse(doc["official_source_url"])

        if url.scheme != "https" or not url.hostname:
            cli.error(
                f"Official source must be an HTTPS URL: "
                f"{doc['official_source_url']}"
            )

        # Extract PDF pages.
        print(f"\nProcessing: {doc['document_title']}")

        pages = extract_pages(pdf_path)

        if not pages:
            cli.error(f"No pages found in {pdf_path.name}")

        metadata = {
            **doc,
            "pdf_path": str(pdf_path)
        }

        # Build document metadata.
        bundle_docs.append({
            "document_id": document_id,
            "corpus_revision": revision,
            "document_title": doc["document_title"],
            "official_source_url": doc["official_source_url"],
            "sha256": sha256(pdf_path),
            "pdf_page_count": len(pages),
            "reviewed": is_reviewed
        })

        # Build paragraph records.
        records = build_records(
            metadata,
            pages,
            revision
        )

        if not records:
            cli.error(
                f"No extractable paragraphs found in {pdf_path.name}. "
                "OCR may be required."
            )

        all_paragraphs.extend(records)

        print(
            f"Extracted {len(records)} paragraphs "
            f"from {pdf_path.name} ({len(pages)} pages)"
        )

    # Build evidence bundle.
    bundle = {
        "schema_version": "satya-evidence-v1",
        "corpus_revision": revision,
        "extraction_reviewed": is_reviewed,
        "documents": bundle_docs,
        "paragraphs": all_paragraphs
    }

    # Build retrieval index.
    index = {
        "corpus_revision": revision,
        "paragraphs": all_paragraphs
    }

    bundle_path = output_dir / "evidence_bundle.json"
    index_path = output_dir / "index.json"

    bundle_path.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\n" + "=" * 45)

    print(f"Mode: {'REVIEWED' if is_reviewed else 'DRAFT'}")
    print(f"Documents: {len(bundle_docs)}")
    print(f"Paragraphs: {len(all_paragraphs)}")
    print(f"Output directory: {output_dir}")

    print(f"\nEvidence bundle: {bundle_path}")
    print(f"Retrieval index: {index_path}")

    if is_reviewed:
        print("\nBundle marked as reviewed.")
        print("Ensure manual evidence review was actually completed.")
    else:
        print("\nDRAFT BUNDLE CREATED.")
        print("This evidence has NOT been manually reviewed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
