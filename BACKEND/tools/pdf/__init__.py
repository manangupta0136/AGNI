import re
from typing import List, Dict

from langchain_core.tools import tool

from tools.pdf.pdf_generate import pdf_generate
from tools.pdf.pdf_read import pdf_read
from tools.pdf.docx_write import docx_write
from tools.pdf.pptx_generate import pptx_generate

# Docling emits this placeholder markdown for a page it couldn't extract
# real text from (no OCR configured in the DocumentConverter) — a scanned
# page's export_to_markdown() output is just repeated "<!-- image -->"
# comments, which is non-empty text but not actually readable content.
_IMAGE_PLACEHOLDER_RE = re.compile(r"<!--\s*image\s*-->", re.IGNORECASE)


@tool
def read_pdf_tool(path: str) -> str:
    """
    Read and extract text content from a local PDF file (digital or scanned).

    Use this — not the generic file reader — whenever you need to read the
    contents of a PDF that has already been attached/uploaded and given to
    you as a local path (e.g. in an [ATTACHED FILES] block). Returns the
    document's extracted text, or — for a scanned/image-only PDF — the
    local paths of its rendered pages so you can call analyze_image on them
    instead.
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
def docx_tool(title: str, content: str, filename: str = "") -> str:
    """
    Generate a Word (.docx) document and save it locally.

    Use this when the user asks you to create, generate, export, or convert
    something into a Word document / .docx / report they can edit (e.g.
    "convert this PDF into a Word document", "make this a docx").

    Args:
        title: The document title / heading.
        content: The full body text of the document.
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
        from pathlib import Path
        output_path = str(Path(__file__).resolve().parent.parent.parent / "data" / "reports" / filename)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        path = pptx_generate(slides_data=slides, output_path=output_path, title=title)
        return f"[PowerPoint generated successfully at: {path}]"
    except Exception as e:
        return f"[Error generating PowerPoint: {e}]"
