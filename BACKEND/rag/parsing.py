"""
parsing.py
This is the ONLY file you run for ingestion.

For every supported file in the data/ folder:
  1. Parse it with Docling (handles PDF, DOCX, TXT, scanned docs with OCR)
  2. Chunk the extracted text (chunking.py)
  3. Embed each chunk (embedding.py)
  4. Store the embedded chunks into local Qdrant (qdrant_store.py)

Run with:
    python parsing.py
"""

import os
from pathlib import Path
from docling.document_converter import DocumentConverter
from .chunking import chunk_text
from .embedding import embed_texts
from .qdrant_store import store_chunks

DATA_DIR = Path(__file__).parent.parent / "data"
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def parse_file(filepath: Path) -> str:
    """
    Parses a single file into clean text using Docling.
    Docling handles PDF/DOCX layout-aware extraction and OCR for scanned
    pages automatically — no separate OCR step needed for these formats.
    """
    if filepath.suffix.lower() == ".txt":
        # Docling is built for PDF/DOCX/etc — plain text files can just be read directly
        return filepath.read_text(encoding="utf-8")

    converter = DocumentConverter()
    result = converter.convert(str(filepath))
    return result.document.export_to_markdown()


def ingest_file(filepath: Path):
    print(f"\n[parsing] Processing: {filepath.name}")

    text = parse_file(filepath)
    if not text or not text.strip():
        print(f"[parsing] WARNING: no text extracted from {filepath.name}, skipping")
        return

    chunks = chunk_text(text, source_filename=filepath.name)
    print(f"[parsing] Split into {len(chunks)} chunks")

    chunk_texts = [c["text"] for c in chunks]
    embeddings = embed_texts(chunk_texts)
    print(f"[parsing] Generated {len(embeddings)} embeddings")

    store_chunks(chunks, embeddings)


def run_ingestion():
    if not DATA_DIR.exists():
        print(f"[parsing] ERROR: {DATA_DIR} folder not found")
        return

    files = [
        f for f in DATA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        print(f"[parsing] No supported files found in {DATA_DIR}")
        return

    print(f"[parsing] Found {len(files)} file(s) to ingest")

    for filepath in files:
        try:
            ingest_file(filepath)
        except Exception as e:
            print(f"[parsing] ERROR processing {filepath.name}: {e}")

    print("\n[parsing] Ingestion complete.")


if __name__ == "__main__":
    run_ingestion()