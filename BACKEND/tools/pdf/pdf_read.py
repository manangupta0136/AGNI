import pymupdf
from docling.document_converter import DocumentConverter
import os
from pathlib import Path

# Absolute by default so rendered page images are findable regardless of
# the server process's current working directory (relative to BACKEND/).
DEFAULT_OUTPUT_FOLDER = str(Path(__file__).resolve().parent.parent.parent / "data" / "ocr_pages")


def detect_document_type(text):
    text_lower = text.lower()

    if any(word in text_lower for word in [
        "inspection", "finding", "defect", "severity"
    ]):
        return "inspection_report"

    elif any(word in text_lower for word in [
        "dear sir", "regards", "reference no", "subject:"
    ]):
        return "correspondence"

    elif any(word in text_lower for word in [
        "table", "quantity", "rate", "amount"
    ]):
        return "data_table"

    else:
        return "unknown"


def pdf_read(pdf_path, output_folder=None):

    output_folder = output_folder or DEFAULT_OUTPUT_FOLDER
    os.makedirs(output_folder, exist_ok=True)

    # Namespaced by the source PDF's own filename so rendered pages from
    # different uploads never collide/overwrite each other (e.g. two PDFs
    # both having a "page_1").
    pdf_stem = Path(pdf_path).stem

    # Open PDF using PyMuPDF
    doc = pymupdf.open(pdf_path)

    scanned_pages = []
    digital_pages = []

    # Check every page
    for i, page in enumerate(doc):

        text = page.get_text()

        if text.strip():

            # Store text together with its original PDF page number
            digital_pages.append({
                "page_num": i + 1,
                "text": text
            })

        else:

            image_path = os.path.join(output_folder, f"{pdf_stem}_page_{i + 1}.png")

            pix = page.get_pixmap(dpi=200)
            pix.save(image_path)

            scanned_pages.append({
                "page_num": i + 1,
                "image_path": image_path
            })

    # Run Docling on the complete PDF
    converter = DocumentConverter()

    result = converter.convert(pdf_path)

    structured_text = result.document.export_to_markdown()

    tables = result.document.tables

    # Detect document type
    document_type = detect_document_type(structured_text)

    return {
        "structured_text": structured_text,
        "tables": tables,

        # Provenance: page-wise text with original PDF page number
        "pages": digital_pages,

        "pages_needing_ocr": scanned_pages,
        "digital_pages": digital_pages,
        "total_pages": len(doc),
        "document_type": document_type
    }