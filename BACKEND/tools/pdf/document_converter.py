from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from tools.pdf.docx_write import docx_write
from tools.pdf.pdf_read import pdf_read
from tools.pdf.pptx_read import pptx_read
from tools.pdf.pdf_generate import pdf_generate

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def convert_document(
    source_path: str,
    target_format: str = "docx",
    title: Optional[str] = None,
    output_filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert a document (PDF, PPTX, TXT, Markdown) into a formatted Word (.docx) or PDF document.

    Args:
        source_path: Path to the source document on disk.
        target_format: Target format extension ("docx" or "pdf"). Defaults to "docx".
        title: Optional title override for the generated document.
        output_filename: Optional filename for the output file.

    Returns:
        Dict with keys:
            - status: "success" or "error"
            - output_path: Absolute path to the generated document
            - source_type: Format of the source file
            - target_format: Format of the generated file
            - title: Title of the document
            - total_units: Total slides or pages converted
            - structured_text: Extracted markdown text
            - message: Human-readable summary
    """
    resolved_src = Path(source_path).resolve()
    if not resolved_src.is_file():
        raise FileNotFoundError(f"Source file not found at: {source_path}")

    ext = resolved_src.suffix.lower()
    source_type = ext.lstrip(".")
    target_ext = target_format.lower().lstrip(".")

    doc_title = title or resolved_src.stem.replace("_", " ")
    structured_content = ""
    total_units = 0

    # 1. Extract content according to source type
    if ext in (".pptx", ".ppt"):
        pptx_data = pptx_read(str(resolved_src))
        structured_content = pptx_data.get("structured_text", "")
        total_units = pptx_data.get("total_slides", 0)
        if not title and pptx_data.get("title"):
            doc_title = pptx_data.get("title")

    elif ext == ".pdf":
        pdf_data = pdf_read(str(resolved_src))
        structured_content = pdf_data.get("structured_text", "")
        total_units = pdf_data.get("total_pages", 0)
        if not title and pdf_data.get("title"):
            doc_title = pdf_data.get("title")

    elif ext in (".txt", ".md", ".csv", ".json", ".log"):
        with open(resolved_src, "r", encoding="utf-8", errors="replace") as f:
            structured_content = f.read()
        total_units = len(structured_content.splitlines())

    elif ext in (".docx", ".doc"):
        # Read docx paragraphs
        import docx
        doc_in = docx.Document(str(resolved_src))
        paras = [p.text for p in doc_in.paragraphs if p.text.strip()]
        structured_content = "\n\n".join(paras)
        total_units = len(paras)

    else:
        # Fallback text read
        with open(resolved_src, "r", encoding="utf-8", errors="replace") as f:
            structured_content = f.read()
        total_units = 1

    if not structured_content.strip():
        structured_content = f"Document converted from {resolved_src.name} (no text extracted)."

    # 2. Output filename calculation
    if not output_filename:
        safe_stem = resolved_src.stem
        output_filename = f"{safe_stem}_Converted.{target_ext}"
    elif not output_filename.lower().endswith(f".{target_ext}"):
        output_filename = f"{output_filename}.{target_ext}"

    # 3. Generate target document
    if target_ext in ("docx", "doc"):
        subtitle_note = f"Converted from {source_type.upper()} ({resolved_src.name})"
        output_path = docx_write(
            title=doc_title,
            content=structured_content,
            filename=output_filename,
            subtitle=subtitle_note,
        )
    elif target_ext == "pdf":
        output_path = pdf_generate(
            title=doc_title,
            content=structured_content,
            filename=output_filename,
        )
    else:
        raise ValueError(f"Unsupported target format: {target_format}. Use 'docx' or 'pdf'.")

    return {
        "status": "success",
        "output_path": output_path,
        "source_type": source_type,
        "target_format": target_ext,
        "title": doc_title,
        "total_units": total_units,
        "structured_text": structured_content,
        "message": f"Successfully converted {source_type.upper()} ({total_units} units) to {target_ext.upper()} at: {output_path}",
    }
