from datetime import datetime, timezone
from pathlib import Path

from docx import Document

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def docx_write(title: str, content: str, filename: str | None = None) -> str:
    """
    Generate a freeform Word (.docx) document (no template required) and
    save it under data/reports. Returns the absolute path.
    """
    if not filename:
        filename = f"AGNI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    if not filename.lower().endswith(".docx"):
        filename += ".docx"

    doc = Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph(f"Generated: {datetime.now(timezone.utc).isoformat()}").italic = True

    for paragraph in content.splitlines() or [""]:
        doc.add_paragraph(paragraph)

    output_path = REPORTS_DIR / filename
    doc.save(str(output_path))

    return str(output_path)
