from __future__ import annotations

import re
from typing import Dict, List, Optional
from pathlib import Path

from langchain_core.tools import tool

from tools.pdf.pdf_generate import pdf_generate
from tools.pdf.pdf_read import pdf_read
from tools.pdf.pptx_read import pptx_read
from tools.pdf.docx_write import docx_write
from tools.pdf.pptx_generate import pptx_generate
from tools.pdf.document_converter import convert_document

_IMAGE_PLACEHOLDER_RE = re.compile(r"<!--\s*image\s*-->", re.IGNORECASE)


@tool
def read_pdf_tool(path: str) -> str:
    """
    Read and extract structured text, headings, and tables from a local PDF file.

    Use this whenever you need to read the contents of a PDF attached/uploaded
    or given to you as a local path. Returns the document's extracted markdown text
    (including any tables), or — for a scanned/image-only PDF — the local paths
    of its rendered pages so you can call analyze_image on them.
    """
    try:
        result = pdf_read(path)
        text = result.get("structured_text", "").strip()
        meaningful_text = _IMAGE_PLACEHOLDER_RE.sub("", text).strip()
        scanned_pages = result.get("pages_needing_ocr") or []

        if not meaningful_text:
            if scanned_pages:
                pages_note = "\n".join(
                    f"- Page {p['page_num']}: {p['image_path']}" for p in scanned_pages
                )
                return (
                    f"[This PDF has no extractable text — it is scanned/image-only. "
                    f"Call analyze_image on the rendered page image(s) below (one call "
                    f"per page you need) instead of treating this as text:]\n{pages_note}"
                )
            return f"[No extractable text found in {path}, and no page images could be rendered either.]"

        return text
    except Exception as e:
        return f"[Error reading PDF {path}: {e}]"


@tool
def read_pptx_tool(path: str) -> str:
    """
    Read and extract slides, headings, bullet points, tables, and notes from a PowerPoint (.pptx) presentation.

    Use this whenever you need to read or understand the content of a PowerPoint
    deck (.pptx) provided as a local path or in an [ATTACHED FILES] block.
    """
    try:
        result = pptx_read(path)
        return result.get("structured_text", "")
    except Exception as e:
        return f"[Error reading PowerPoint presentation {path}: {e}]"


@tool
def convert_document_tool(
    source_path: str,
    target_format: str = "docx",
    title: str = "",
    filename: str = "",
) -> str:
    """
    Convert a document (PDF, PPTX, TXT, or Markdown) directly into a formatted Word (.docx) or PDF document.

    Use this when the user asks you to convert, transform, or export an existing
    file from one format to another (e.g. "convert this PDF to docx", "convert this presentation to Word").

    Args:
        source_path: The local path of the file to convert.
        target_format: Target document format ("docx" or "pdf"). Defaults to "docx".
        title: Optional title for the converted document.
        filename: Optional output filename (e.g. "report.docx").

    Returns:
        A confirmation message with the saved document's path and summary.
    """
    try:
        res = convert_document(
            source_path=source_path,
            target_format=target_format or "docx",
            title=title or None,
            output_filename=filename or None,
        )
        return f"[Document converted successfully: {res.get('message')}]"
    except Exception as e:
        return f"[Error converting document {source_path}: {e}]"


@tool
def docx_tool(title: str, content: str, filename: str = "") -> str:
    """
    Generate a high-fidelity, corporate-styled Word (.docx) document with tables, headings, and formatting.

    Use this when creating, exporting, or writing a new Word document / .docx report.

    Args:
        title: The document title / heading.
        content: The full body text of the document (Markdown headings, tables, bullet points, and callouts supported).
        filename: Optional filename (without extension is fine).

    Returns:
        A message confirming the local file path where the .docx was saved.
    """
    try:
        path = docx_write(title=title, content=content, filename=filename or None)
        return f"[Word document generated successfully at: {path}]"
    except Exception as e:
        return f"[Error generating Word document: {e}]"


@tool
def pdf_tool(title: str, content: str, filename: str = "") -> str:
    """
    Generate a PDF (.pdf) report and save it locally.

    Use this ONLY when the user specifically wants a PDF file. If they ask
    for a Word document instead, use docx_tool. If they ask for a
    PowerPoint/slides/presentation, use pptx_tool.

    Args:
        title: The report title / heading.
        content: The full body text of the report.
        filename: Optional filename (without extension is fine).

    Returns:
        A message confirming the local file path where the PDF was saved.
    """
    try:
        path = pdf_generate(title=title, content=content, filename=filename or None)
        return f"[PDF generated successfully at: {path}]"
    except Exception as e:
        return f"[Error generating PDF: {e}]"


@tool
def pptx_tool(title: str, slides: List[Dict[str, str]], filename: str = "") -> str:
    """
    Generate a PowerPoint (.pptx) presentation and save it locally.

    Use this when the user asks you to create, generate, export, or convert
    something into a PowerPoint / slides / presentation / deck.

    Args:
        title: The presentation's title (shown on the title slide).
        slides: A list of slides, each a dict with keys "title" and
            "content", e.g.
            [{"title": "Overview", "content": "Key point one\\nKey point two"}]
        filename: Optional filename (without extension is fine).

    Returns:
        A message confirming the local file path where the .pptx was saved.
    """
    try:
        if not filename:
            filename = "AGNI_Presentation.pptx"
        if not filename.lower().endswith(".pptx"):
            filename += ".pptx"
        output_path = str(Path(__file__).resolve().parent.parent.parent / "data" / "reports" / filename)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        path = pptx_generate(slides_data=slides, output_path=output_path, title=title)
        return f"[PowerPoint generated successfully at: {path}]"
    except Exception as e:
        return f"[Error generating PowerPoint: {e}]"
