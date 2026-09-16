from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import pymupdf

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

PAGE_WIDTH, PAGE_HEIGHT = 595, 842  # A4 in points
MARGIN = 50
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

# ── Shared corporate palette (matches docx_write.py so a PDF and a Word
# report generated from the same content look like one visual family) ──────
NAVY = (0.118, 0.227, 0.541)          # #1E3A8A
BLUE = (0.145, 0.388, 0.922)          # #2563EB
DARK_SLATE = (0.200, 0.255, 0.333)    # #334155
MUTED_SLATE = (0.392, 0.455, 0.545)   # #64748B
BODY_TEXT = (0.122, 0.161, 0.216)     # #1F2937
WHITE = (1, 1, 1)
CODE_BG = (0.945, 0.961, 0.976)       # #F1F5F9
ALT_ROW_BG = (0.973, 0.980, 0.988)    # #F8FAFC
BORDER = (0.804, 0.835, 0.882)        # #CBD5E1
CODE_TEXT = (0.059, 0.090, 0.165)     # #0F172A

FONT = "helv"
FONT_BOLD = "hebo"
FONT_ITALIC = "heit"
FONT_CODE = "cour"

BANNER_HEIGHT = 84
FOOTER_HEIGHT = 34


def _wrap_line(text: str, fontname: str, fontsize: float, max_width: float) -> List[str]:
    """Greedy word-wrap using PyMuPDF's own glyph metrics so lines actually
    fit the page width, instead of guessing a fixed character count (which
    over/under-fills depending on font and text content)."""
    if not text:
        return [""]
    words = text.split(" ")
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if pymupdf.get_text_length(candidate, fontname=fontname, fontsize=fontsize) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


# Inline markdown token pattern shared by every paragraph/heading/bullet
# renderer below — mirrors docx_write.py's _append_formatted_inline_text so
# **bold**, *italic*, and `code` all render consistently across both formats.
_INLINE_TOKEN_RE = re.compile(
    r"(`[^`]+`|\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*)"
)


def _inline_tokens(text: str):
    """Split text into (segment, style) tuples — style is one of
    'plain', 'bold', 'italic', 'bold_italic', 'code'."""
    for part in _INLINE_TOKEN_RE.split(text):
        if not part:
            continue
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            yield part[1:-1], "code"
        elif part.startswith("***") and part.endswith("***") and len(part) >= 6:
            yield part[3:-3], "bold_italic"
        elif part.startswith("**") and part.endswith("**") and len(part) >= 4:
            yield part[2:-2], "bold"
        elif part.startswith("*") and part.endswith("*") and len(part) >= 2:
            yield part[1:-1], "italic"
        else:
            yield part, "plain"


class _PdfWriter:
    """Tracks the write cursor across pages and draws the repeating chrome
    (title banner on page 1, a slim footer with page numbers on every page)
    so the body-content renderers below only need to worry about laying out
    one block at a time and asking for more space when they run out."""

    def __init__(self, title: str, subtitle: Optional[str], organization: str):
        self.doc = pymupdf.open()
        self.title = title
        self.subtitle = subtitle
        self.organization = organization
        self.page = None
        self.y = 0.0
        self._new_page(first=True)

    def _draw_footer(self, page):
        y = PAGE_HEIGHT - FOOTER_HEIGHT
        page.draw_line((MARGIN, y), (PAGE_WIDTH - MARGIN, y), color=BORDER, width=0.75)
        page.insert_text(
            (MARGIN, y + 16),
            f"{self.organization} — Confidential On-Premise Document",
            fontsize=7.5, fontname=FONT, color=MUTED_SLATE,
        )
        page_no = f"Page {len(self.doc)}"
        tw = pymupdf.get_text_length(page_no, fontname=FONT, fontsize=7.5)
        page.insert_text((PAGE_WIDTH - MARGIN - tw, y + 16), page_no, fontsize=7.5, fontname=FONT, color=MUTED_SLATE)

    def _draw_banner(self, page):
        """Full-width colored title banner — the single biggest lever for
        making a generated report look like a designed document instead of
        a plain text dump, so every report gets one on its first page."""
        page.draw_rect(pymupdf.Rect(0, 0, PAGE_WIDTH, BANNER_HEIGHT), color=None, fill=NAVY)
        # A thin accent stripe under the banner for a bit of depth.
        page.draw_rect(pymupdf.Rect(0, BANNER_HEIGHT, PAGE_WIDTH, BANNER_HEIGHT + 4), color=None, fill=BLUE)

        page.insert_text((MARGIN, 22), self.organization.upper(), fontsize=8.5, fontname=FONT_BOLD, color=(0.78, 0.85, 0.98))

        title_size = 20 if len(self.title) <= 46 else 16
        page.insert_text((MARGIN, 48), self.title, fontsize=title_size, fontname=FONT_BOLD, color=WHITE)

        ts_str = datetime.now(timezone.utc).strftime("%B %d, %Y - %H:%M UTC")
        meta = f"Generated: {ts_str}"
        if self.subtitle:
            meta = f"{self.subtitle}  |  {meta}"
        page.insert_text((MARGIN, 68), meta, fontsize=8.5, fontname=FONT_ITALIC, color=(0.82, 0.88, 0.97))

    def _new_page(self, first: bool = False):
        self.page = self.doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        self._draw_footer(self.page)
        if first:
            self._draw_banner(self.page)
            self.y = BANNER_HEIGHT + 4 + 26
        else:
            self.y = MARGIN

    def ensure_space(self, height: float):
        if self.y + height > PAGE_HEIGHT - FOOTER_HEIGHT - 6:
            self._new_page()

    def advance(self, amount: float):
        self.y += amount

    def draw_rect(self, rect: "pymupdf.Rect", fill=None, color=None, width=1.0):
        self.page.draw_rect(rect, color=color, fill=fill, width=width)

    def insert_text(self, point, text, fontsize, fontname, color):
        self.page.insert_text(point, text, fontsize=fontsize, fontname=fontname, color=color)

    def draw_line(self, p1, p2, color, width=1.0):
        self.page.draw_line(p1, p2, color=color, width=width)


def _render_rich_line(writer: _PdfWriter, x: float, text: str, fontsize: float, color, max_width: float, line_height: float):
    """Renders one paragraph's worth of text with inline bold/italic/code
    formatting, wrapping across as many visual lines and pages as needed."""
    # Build (word, style) pairs first so wrapping can still measure width
    # per-token style (bold/code glyphs are wider than plain text).
    tokens = []
    for segment, style in _inline_tokens(text):
        for i, word in enumerate(segment.split(" ")):
            if word == "" and i == 0:
                continue
            tokens.append((word, style))

    font_for = {
        "plain": FONT, "bold": FONT_BOLD, "italic": FONT_ITALIC,
        "bold_italic": FONT_BOLD, "code": FONT_CODE,
    }
    color_for = {
        "plain": color, "bold": color, "italic": color,
        "bold_italic": color, "code": CODE_TEXT,
    }

    line: List[tuple] = []
    line_width = 0.0
    space_w = pymupdf.get_text_length(" ", fontname=FONT, fontsize=fontsize)

    def flush_line():
        nonlocal line, line_width
        if not line:
            return
        writer.ensure_space(line_height)
        cx = x
        for word, style in line:
            fname = font_for[style]
            fcolor = color_for[style]
            writer.insert_text((cx, writer.y), word, fontsize=fontsize, fontname=fname, color=fcolor)
            cx += pymupdf.get_text_length(word, fontname=fname, fontsize=fontsize) + space_w
        writer.advance(line_height)
        line = []
        line_width = 0.0

    for word, style in tokens:
        w = pymupdf.get_text_length(word, fontname=font_for[style], fontsize=fontsize)
        projected = line_width + (space_w if line else 0) + w
        if projected > max_width and line:
            flush_line()
            projected = w
        line.append((word, style))
        line_width = projected
    flush_line()


def _render_table(writer: _PdfWriter, table_lines: List[str]):
    parsed_rows: List[List[str]] = []
    for raw in table_lines:
        stripped = raw.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if all(re.match(r"^:?-+:?$", c) for c in cells if c):
            continue
        if cells:
            parsed_rows.append(cells)
    if not parsed_rows:
        return

    num_cols = max(len(r) for r in parsed_rows)
    col_width = CONTENT_WIDTH / num_cols
    row_height = 24
    cell_pad = 6
    fontsize = 9.5

    for r_idx, row in enumerate(parsed_rows):
        writer.ensure_space(row_height)
        is_header = r_idx == 0
        row_y = writer.y
        bg = NAVY if is_header else (ALT_ROW_BG if r_idx % 2 == 0 else WHITE)
        for c_idx in range(num_cols):
            cx = MARGIN + c_idx * col_width
            writer.draw_rect(pymupdf.Rect(cx, row_y, cx + col_width, row_y + row_height), fill=bg, color=BORDER, width=0.6)
            text = row[c_idx] if c_idx < len(row) else ""
            text_color = WHITE if is_header else BODY_TEXT
            fname = FONT_BOLD if is_header else FONT
            # Single-line truncation with ellipsis keeps table rows a fixed,
            # predictable height rather than growing per-cell — acceptable
            # for the short labels/values these reports' tables carry.
            max_w = col_width - 2 * cell_pad
            display = text
            while pymupdf.get_text_length(display, fontname=fname, fontsize=fontsize) > max_w and len(display) > 1:
                display = display[:-1]
            if display != text and len(display) > 1:
                display = display[:-1] + "…"
            writer.insert_text((cx + cell_pad, row_y + row_height / 2 + 3), display, fontsize=fontsize, fontname=fname, color=text_color)
        writer.advance(row_height)
    writer.advance(10)


def _render_code_block(writer: _PdfWriter, code_lines: List[str]):
    fontsize = 9.0
    line_height = 13
    pad = 10
    block_height = pad * 2 + line_height * max(len(code_lines), 1)
    writer.ensure_space(min(block_height, PAGE_HEIGHT - BANNER_HEIGHT - FOOTER_HEIGHT - 40))

    start_y = writer.y
    # If the block doesn't fit on the remaining page at all, let it flow
    # onto a fresh page as a whole rather than splitting mid-block.
    if writer.y + block_height > PAGE_HEIGHT - FOOTER_HEIGHT - 6:
        writer._new_page()
        start_y = writer.y

    writer.draw_rect(pymupdf.Rect(MARGIN, start_y, MARGIN + CONTENT_WIDTH, start_y + block_height), fill=CODE_BG, color=BORDER, width=0.6)
    ty = start_y + pad + 9
    for line in code_lines:
        writer.insert_text((MARGIN + pad, ty), line, fontsize=fontsize, fontname=FONT_CODE, color=CODE_TEXT)
        ty += line_height
    writer.advance(block_height + 10)


def _render_callout(writer: _PdfWriter, quote_lines: List[str]):
    text = " ".join(q.lstrip("> ").strip() for q in quote_lines if q.strip())
    fontsize = 10
    line_height = 15
    pad = 12
    wrapped = _wrap_line(text, FONT_ITALIC, fontsize, CONTENT_WIDTH - 2 * pad - 6)
    block_height = pad * 2 + line_height * len(wrapped)
    writer.ensure_space(block_height)
    start_y = writer.y
    writer.draw_rect(pymupdf.Rect(MARGIN, start_y, MARGIN + CONTENT_WIDTH, start_y + block_height), fill=CODE_BG, color=None)
    writer.draw_rect(pymupdf.Rect(MARGIN, start_y, MARGIN + 4, start_y + block_height), fill=NAVY, color=None)
    ty = start_y + pad + 8
    for line in wrapped:
        writer.insert_text((MARGIN + pad + 6, ty), line, fontsize=fontsize, fontname=FONT_ITALIC, color=DARK_SLATE)
        ty += line_height
    writer.advance(block_height + 10)


_HEADING_STYLE = {
    1: (16, NAVY, 12),
    2: (13.5, BLUE, 10),
    3: (11.5, DARK_SLATE, 8),
    4: (10.5, MUTED_SLATE, 6),
}


def pdf_generate(
    title: str,
    content: str,
    filename: Optional[str] = None,
    subtitle: Optional[str] = None,
    organization: str = "AGNI AIR-GAPPED INTELLIGENCE WORKBENCH",
) -> str:
    """
    Generate a styled PDF report from Markdown-ish text — a colored title
    banner, colored headings, native tables, code blocks, callouts, and a
    page-numbered footer, matching the visual language of docx_write.py so
    a PDF and a Word report generated from the same content look related.
    Returns the absolute file path of the created .pdf file.
    """
    if not filename:
        clean_title = re.sub(r"[^\w\-_]", "_", title)[:40].strip("_") or "Report"
        filename = f"AGNI_{clean_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    writer = _PdfWriter(title=title, subtitle=subtitle, organization=organization)

    lines = content.splitlines()
    idx = 0
    total = len(lines)

    while idx < total:
        line = lines[idx]
        stripped = line.strip()

        if not stripped:
            idx += 1
            continue

        if stripped.startswith("```"):
            code_lines = []
            idx += 1
            while idx < total and not lines[idx].strip().startswith("```"):
                code_lines.append(lines[idx])
                idx += 1
            idx += 1
            _render_code_block(writer, code_lines)
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines = []
            while idx < total and lines[idx].strip().startswith("|"):
                table_lines.append(lines[idx])
                idx += 1
            _render_table(writer, table_lines)
            continue

        if stripped.startswith(">"):
            quote_lines = []
            while idx < total and lines[idx].strip().startswith(">"):
                quote_lines.append(lines[idx])
                idx += 1
            _render_callout(writer, quote_lines)
            continue

        if stripped in ("---", "***", "___") or re.match(r"^[-*_]{3,}$", stripped):
            writer.ensure_space(16)
            writer.draw_line((MARGIN, writer.y), (MARGIN + CONTENT_WIDTH, writer.y), color=BORDER, width=0.75)
            writer.advance(16)
            idx += 1
            continue

        heading_match = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            size, color, space_after = _HEADING_STYLE[level]
            writer.ensure_space(size + space_after + 6)
            writer.advance(size * 0.35)
            writer.insert_text((MARGIN, writer.y), heading_match.group(2), fontsize=size, fontname=FONT_BOLD, color=color)
            writer.advance(size * 0.55 + space_after)
            idx += 1
            continue

        bullet_match = re.match(r"^(\s*)[-*+•]\s+(.*)$", line)
        if bullet_match:
            indent = MARGIN + 14 * (len(bullet_match.group(1)) // 2)
            line_height = 15
            # Ensure space for the marker+text line ONCE, then draw both at
            # the exact same writer.y/baseline — drawing the marker with its
            # own separate ensure_space+offset let it drift out of sync with
            # where the wrapped text actually landed (different height, or
            # even a page break happening between the two draws).
            writer.ensure_space(line_height)
            writer.insert_text((indent, writer.y), "•", fontsize=10.5, fontname=FONT_BOLD, color=BLUE)
            _render_rich_line(writer, indent + 14, bullet_match.group(2), 10.5, BODY_TEXT, CONTENT_WIDTH - (indent + 14 - MARGIN), line_height)
            idx += 1
            continue

        num_match = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
        if num_match:
            indent = MARGIN
            marker = f"{num_match.group(2)}."
            line_height = 15
            writer.ensure_space(line_height)
            writer.insert_text((indent, writer.y), marker, fontsize=10.5, fontname=FONT_BOLD, color=BLUE)
            offset = pymupdf.get_text_length(marker, fontname=FONT_BOLD, fontsize=10.5) + 8
            _render_rich_line(writer, indent + offset, num_match.group(3), 10.5, BODY_TEXT, CONTENT_WIDTH - offset, line_height)
            idx += 1
            continue

        _render_rich_line(writer, MARGIN, stripped, 10.5, BODY_TEXT, CONTENT_WIDTH, 15)
        writer.advance(4)
        idx += 1

    output_path = REPORTS_DIR / filename
    writer.doc.save(str(output_path))
    writer.doc.close()
    return str(output_path)
