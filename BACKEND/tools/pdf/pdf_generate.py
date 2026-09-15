from datetime import datetime, timezone
from pathlib import Path

import pymupdf

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

PAGE_WIDTH, PAGE_HEIGHT = 595, 842  # A4 in points
MARGIN = 50
LINE_HEIGHT = 16
FONT_SIZE = 11
TITLE_FONT_SIZE = 16


def pdf_generate(title: str, content: str, filename: str | None = None) -> str:
    """
    Generate a simple text PDF report and save it under data/reports.
    Returns the absolute path of the generated file.
    """
    if not filename:
        filename = f"AGNI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    doc = pymupdf.open()
    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)

    y = MARGIN
    page.insert_text((MARGIN, y), title, fontsize=TITLE_FONT_SIZE, fontname="helv")
    y += TITLE_FONT_SIZE + 6
    page.insert_text(
        (MARGIN, y),
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        fontsize=9,
        fontname="helv",
        color=(0.4, 0.4, 0.4),
    )
    y += LINE_HEIGHT * 2

    max_chars_per_line = 95
    for paragraph in content.splitlines() or [""]:
        words = paragraph.split(" ")
        line = ""
        wrapped_lines = []
        for word in words:
            candidate = f"{line} {word}".strip()
            if len(candidate) > max_chars_per_line:
                wrapped_lines.append(line)
                line = word
            else:
                line = candidate
        wrapped_lines.append(line)

        for wrapped in wrapped_lines:
            if y > PAGE_HEIGHT - MARGIN:
                page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
                y = MARGIN
            page.insert_text((MARGIN, y), wrapped, fontsize=FONT_SIZE, fontname="helv")
            y += LINE_HEIGHT

    output_path = REPORTS_DIR / filename
    doc.save(str(output_path))
    doc.close()

    return str(output_path)
