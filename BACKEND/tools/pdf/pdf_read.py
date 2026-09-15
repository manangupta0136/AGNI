from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import pymupdf

try:
    from docling.document_converter import DocumentConverter
    has_docling = True
except ImportError:
    DocumentConverter = None
    has_docling = False

try:
    import pdfplumber
    has_pdfplumber = True
except ImportError:
    has_pdfplumber = False

DEFAULT_OUTPUT_FOLDER = str(Path(__file__).resolve().parent.parent.parent / "data" / "ocr_pages")


def detect_document_type(text: str) -> str:
    text_lower = text.lower()
    if any(word in text_lower for word in ["inspection", "finding", "defect", "severity", "equipment"]):
        return "inspection_report"
    elif any(word in text_lower for word in ["dear sir", "regards", "reference no", "subject:"]):
        return "correspondence"
    elif any(word in text_lower for word in ["table", "quantity", "rate", "amount", "schedule", "cost"]):
        return "data_table"
    elif any(word in text_lower for word in ["standard", "oisd", "asme", "clause", "procedure"]):
        return "engineering_standard"
    return "general_document"


def _format_table_as_markdown(table_rows: List[List[Any]]) -> str:
    """Convert a 2D list of cells into a Markdown table."""
    if not table_rows or len(table_rows) < 1:
        return ""

    cleaned_rows: List[List[str]] = []
    max_cols = 0
    for row in table_rows:
        cleaned_row = [str(c or "").strip().replace("\n", " ") for c in row]
        if any(cleaned_row):
            cleaned_rows.append(cleaned_row)
            if len(cleaned_row) > max_cols:
                max_cols = len(cleaned_row)

    if not cleaned_rows:
        return ""

    # Pad rows to max_cols
    for row in cleaned_rows:
        while len(row) < max_cols:
            row.append("")

    headers = cleaned_rows[0]
    md_lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * max_cols) + " |",
    ]
    for row in cleaned_rows[1:]:
        md_lines.append("| " + " | ".join(row) + " |")

    return "\n".join(md_lines)


def pdf_read(pdf_path: str, output_folder: Optional[str] = None) -> Dict[str, Any]:
    """
    Read and extract structured content from a local PDF file.

    Features:
    - Extracts text page-by-page preserving block structure
    - Detects and extracts tables into clean Markdown tables
    - Extracts scanned page snapshots for OCR/Vision analysis
    - Returns structured markdown, provenance, and metadata
    """
    resolved_path = Path(pdf_path).resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    output_folder = output_folder or DEFAULT_OUTPUT_FOLDER
    os.makedirs(output_folder, exist_ok=True)
    pdf_stem = resolved_path.stem

    doc = pymupdf.open(str(resolved_path))

    scanned_pages: List[Dict[str, Any]] = []
    digital_pages: List[Dict[str, Any]] = []
    all_extracted_tables: List[Dict[str, Any]] = []

    # Try pdfplumber for high-accuracy table extraction if available
    plumber_doc = None
    if has_pdfplumber:
        try:
            plumber_doc = pdfplumber.open(str(resolved_path))
        except Exception:
            plumber_doc = None

    for i, page in enumerate(doc):
        page_num = i + 1
        page_tables: List[str] = []

        # 1. Extract tables from this page
        # Method A: PyMuPDF find_tables
        try:
            pymupdf_tables = page.find_tables()
            for t in pymupdf_tables:
                extracted = t.extract()
                if extracted and len(extracted) > 1:
                    md_t = _format_table_as_markdown(extracted)
                    if md_t:
                        page_tables.append(md_t)
                        all_extracted_tables.append({"page_num": page_num, "markdown": md_t})
        except Exception:
            pass

        # Method B: pdfplumber fallback if no tables found yet
        if not page_tables and plumber_doc and i < len(plumber_doc.pages):
            try:
                p_page = plumber_doc.pages[i]
                p_tables = p_page.extract_tables()
                for pt in p_tables:
                    if pt and len(pt) > 1:
                        md_t = _format_table_as_markdown(pt)
                        if md_t:
                            page_tables.append(md_t)
                            all_extracted_tables.append({"page_num": page_num, "markdown": md_t})
            except Exception:
                pass

        # 2. Extract text
        text = page.get_text()

        if text.strip():
            # Clean up and assemble page content
            page_content = text.strip()
            if page_tables:
                # Append extracted tables if not already embedded
                page_content += "\n\n### Extracted Tables\n" + "\n\n".join(page_tables)

            digital_pages.append({
                "page_num": page_num,
                "text": page_content,
                "tables": page_tables,
            })
        else:
            # Scanned / image-only page -> render pixmap for OCR/Vision
            image_path = os.path.join(output_folder, f"{pdf_stem}_page_{page_num}.png")
            pix = page.get_pixmap(dpi=200)
            pix.save(image_path)
            scanned_pages.append({
                "page_num": page_num,
                "image_path": image_path,
            })

    if plumber_doc:
        try:
            plumber_doc.close()
        except Exception:
            pass

    # 3. Build overall structured markdown
    structured_text = ""
    if has_docling and DocumentConverter is not None:
        try:
            converter = DocumentConverter()
            result = converter.convert(str(resolved_path))
            structured_text = result.document.export_to_markdown()
        except Exception:
            structured_text = "\n\n".join([f"## Page {p['page_num']}\n{p['text']}" for p in digital_pages])
    else:
        structured_text = "\n\n".join([f"## Page {p['page_num']}\n{p['text']}" for p in digital_pages])

    document_type = detect_document_type(structured_text)

    return {
        "title": pdf_stem.replace("_", " "),
        "structured_text": structured_text,
        "tables": all_extracted_tables,
        "pages": digital_pages,
        "digital_pages": digital_pages,
        "pages_needing_ocr": scanned_pages,
        "total_pages": len(doc),
        "document_type": document_type,
    }