"""
parsing.py
This is the main ingestion script for the RAG knowledge base.

For every supported file in backend/data/rag (or backend/data):
  1. Parse it with Docling (handles PDF, DOCX, TXT, scanned docs with OCR)
  2. Chunk the extracted text (chunking.py)
  3. Embed each chunk (embedding.py using BAAI/bge-small-en-v1.5)
  4. Store the embedded chunks into local Qdrant (qdrant_store.py)

Run directly with:
    python parsing.py
or:
    python -m rag.parsing
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Enable running directly as `python parsing.py` without package import error
if __package__ is None or __package__ == "":
    backend_dir = str(Path(__file__).resolve().parent.parent)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from rag.chunking import chunk_text
    from rag.embedding import embed_texts
    from rag.qdrant_store import store_chunks
else:
    from .chunking import chunk_text
    from .embedding import embed_texts
    from .qdrant_store import store_chunks

from docling.document_converter import DocumentConverter

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
RAG_DATA_DIR = DATA_DIR / "rag"
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def parse_file(filepath: Path) -> str:
    """
    Parses a single file into clean text using Docling.
    Docling handles PDF/DOCX layout-aware extraction and OCR for scanned
    pages automatically.
    """
    if filepath.suffix.lower() == ".txt":
        return filepath.read_text(encoding="utf-8")

    converter = DocumentConverter()
    result = converter.convert(str(filepath))
    return result.document.export_to_markdown()


def ingest_file(filepath: Path) -> Dict[str, Any]:
    """Ingests a single document into Qdrant."""
    print(f"\n[parsing] Processing: {filepath.name}")

    text = parse_file(filepath)
    if not text or not text.strip():
        print(f"[parsing] WARNING: no text extracted from {filepath.name}, skipping")
        return {"file": filepath.name, "status": "skipped", "reason": "empty_text", "chunks": 0}

    chunks = chunk_text(text, source_filename=filepath.name)
    print(f"[parsing] Split into {len(chunks)} chunks")

    chunk_texts = [c["text"] for c in chunks]
    embeddings = embed_texts(chunk_texts)
    print(f"[parsing] Generated {len(embeddings)} embeddings")

    store_chunks(chunks, embeddings)
    return {"file": filepath.name, "status": "success", "chunks": len(chunks)}


def discover_files(target_path: Optional[Path] = None) -> List[Path]:
    """Finds all supported documents to ingest."""
    if target_path is not None:
        target = Path(target_path).resolve()
        if target.is_file():
            return [target] if target.suffix.lower() in SUPPORTED_EXTENSIONS else []
        if target.is_dir():
            return [
                f for f in target.iterdir()
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
            ]

    candidates = []
    seen = set()

    # Priority 1: Check backend/data/rag specifically
    if RAG_DATA_DIR.exists():
        for f in RAG_DATA_DIR.iterdir():
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                if f.resolve() not in seen:
                    candidates.append(f)
                    seen.add(f.resolve())

    # Priority 2: Check backend/data root
    if DATA_DIR.exists():
        for f in DATA_DIR.iterdir():
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                if f.resolve() not in seen:
                    candidates.append(f)
                    seen.add(f.resolve())

    return candidates


def run_ingestion(target_path: Optional[str | Path] = None) -> Dict[str, Any]:
    """Runs ingestion on discovered files or a specified path."""
    target = Path(target_path) if target_path else None
    files = discover_files(target)

    if not files:
        target_desc = str(target) if target else f"{RAG_DATA_DIR} and {DATA_DIR}"
        print(f"[parsing] No supported files found in {target_desc}")
        return {"status": "empty", "files_found": 0, "results": []}

    print(f"[parsing] Found {len(files)} file(s) to ingest:")
    for f in files:
        print(f"  - {f.name} ({round(f.stat().st_size / 1024, 1)} KB)")

    results = []
    total_chunks = 0
    for filepath in files:
        try:
            res = ingest_file(filepath)
            results.append(res)
            total_chunks += res.get("chunks", 0)
        except Exception as e:
            print(f"[parsing] ERROR processing {filepath.name}: {e}")
            results.append({"file": filepath.name, "status": "error", "error": str(e), "chunks": 0})

    print(f"\n[parsing] Ingestion complete. Ingested {len(files)} files ({total_chunks} total chunks).")
    return {
        "status": "success",
        "files_processed": len(files),
        "total_chunks": total_chunks,
        "results": results,
    }


if __name__ == "__main__":
    cli_target = sys.argv[1] if len(sys.argv) > 1 else None
    run_ingestion(cli_target)