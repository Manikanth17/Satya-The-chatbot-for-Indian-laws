#!/usr/bin/env python3
"""Build SATYA's canonical evidence bundle and local retrieval index from a reviewed manifest."""
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="JSON manifest describing 3–5 official PDF documents")
    parser.add_argument("--reviewed", action="store_true", help="Attest that extracted text, page numbers and source URLs have been manually reviewed")
    parser.add_argument("--out", default=str(ROOT / "data"), help="Output directory")
    args = parser.parse_args()
    if not args.reviewed:
        parser.error("Refusing to mark a corpus reviewed. Inspect extracted text, then rerun with --reviewed.")

    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    revision = manifest.get("corpus_revision", "").strip()
    docs = manifest.get("documents", [])
    if not revision or len(docs) < 3 or len(docs) > 5:
        parser.error("Manifest must contain corpus_revision and 3–5 documents (required by current Java importer).")

    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    bundle_docs, all_paragraphs = [], []
    for doc in docs:
        required = ["document_id", "document_title", "pdf_path", "official_source_url"]
        missing = [key for key in required if not doc.get(key)]
        if missing:
            parser.error(f"Document is missing fields: {', '.join(missing)}")
        if len(doc["document_id"]) > 70:
            parser.error("document_id must be 70 characters or fewer.")
        pdf_path = (manifest_path.parent / doc["pdf_path"]).resolve()
        if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
            parser.error(f"PDF not found or not a PDF: {pdf_path}")
        url = urlparse(doc["official_source_url"])
        if url.scheme != "https" or not url.hostname:
            parser.error(f"Official source must be an HTTPS URL: {doc['official_source_url']}")
        pages = extract_pages(pdf_path)
        if not pages:
            parser.error(f"No pages found in {pdf_path.name}")
        metadata = {**doc, "pdf_path": str(pdf_path)}
        bundle_docs.append({
            "document_id": doc["document_id"],
            "corpus_revision": revision,
            "document_title": doc["document_title"],
            "official_source_url": doc["official_source_url"],
            "sha256": sha256(pdf_path),
            "pdf_page_count": len(pages),
            "reviewed": True,
        })
        records = build_records(metadata, pages, revision)
        if not records:
            parser.error(f"No extractable paragraphs found in {pdf_path.name}; OCR may be needed.")
        all_paragraphs.extend(records)
        print(f"Extracted {len(records)} paragraphs from {pdf_path.name} ({len(pages)} pages)")

    bundle = {
        "schema_version": "satya-evidence-v1",
        "corpus_revision": revision,
        "extraction_reviewed": True,
        "documents": bundle_docs,
        "paragraphs": all_paragraphs,
    }
    (output / "evidence_bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "index.json").write_text(json.dumps({"corpus_revision": revision, "paragraphs": all_paragraphs}, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {output / 'evidence_bundle.json'}")
    print(f"Wrote {output / 'index.json'}")
    print("IMPORTANT: Manually review the PDF extraction and bundle before importing it into the Java backend.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
