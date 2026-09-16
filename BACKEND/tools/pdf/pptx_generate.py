"""
pptx_generate.py
Builds a fully custom-styled PowerPoint deck (blank layout + manually drawn
shapes on every slide) instead of relying on the default PowerPoint theme,
which is what made previous decks look like plain black-text-on-white
textboxes. Shares the same navy/blue corporate palette as docx_write.py and
pdf_generate.py so a deck generated alongside a report looks related to it.
"""

import re
from datetime import datetime, timezone

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

NAVY = RGBColor(0x1E, 0x3A, 0x8A)
BLUE = RGBColor(0x25, 0x63, 0xEB)
LIGHT_BLUE = RGBColor(0xC7, 0xD8, 0xFA)
DARK_SLATE = RGBColor(0x33, 0x41, 0x55)
MUTED_SLATE = RGBColor(0x64, 0x74, 0x8B)
BODY_TEXT = RGBColor(0x1F, 0x29, 0x37)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BG = RGBColor(0xF8, 0xFA, 0xFC)
BORDER = RGBColor(0xCB, 0xD5, 0xE1)

# Cycled across content slides so a long deck doesn't look like one flat
# repeating template — each slide's accent band takes the next color.
ACCENT_CYCLE = [BLUE, RGBColor(0x0E, 0xA5, 0xE9), RGBColor(0x7C, 0x3A, 0xED), RGBColor(0x0D, 0x94, 0x88)]

FONT = "Calibri"


def _no_line(shape):
    shape.line.fill.background()


def _solid(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color


def _add_rect(slide, x, y, w, h, color, line=False):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    _solid(shape, color)
    if not line:
        _no_line(shape)
    shape.shadow.inherit = False
    return shape


def _add_text(slide, x, y, w, h, text, size, color, bold=False, italic=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=FONT, wrap=True):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font
    return box


def _footer(slide, organization, page_label=None):
    y = SLIDE_H - Inches(0.36)
    line = slide.shapes.add_connector(1, Inches(0.5), y, SLIDE_W - Inches(0.5), y)
    line.line.color.rgb = BORDER
    line.line.width = Pt(0.75)
    _add_text(slide, Inches(0.5), y + Pt(4), Inches(8), Inches(0.3), organization, 8, MUTED_SLATE)
    if page_label:
        _add_text(slide, SLIDE_W - Inches(2.5), y + Pt(4), Inches(2), Inches(0.3), page_label, 8, MUTED_SLATE, align=PP_ALIGN.RIGHT)


def _inline_runs(paragraph, text: str, base_size: int, base_color, bold: bool = False):
    """Adds **bold**/*italic*/`code` runs from one line of text into an
    existing paragraph — keeps bullet content from looking like flat,
    unstyled dumps of the model's raw markdown."""
    token_re = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)")
    for part in token_re.split(text):
        if not part:
            continue
        run = paragraph.add_run()
        run.font.size = Pt(base_size)
        run.font.name = FONT
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            run.text = part[1:-1]
            run.font.name = "Consolas"
            run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        elif part.startswith("**") and part.endswith("**") and len(part) >= 4:
            run.text = part[2:-2]
            run.font.bold = True
            run.font.color.rgb = base_color
        elif part.startswith("*") and part.endswith("*") and len(part) >= 2:
            run.text = part[1:-1]
            run.font.italic = True
            run.font.color.rgb = base_color
        else:
            run.text = part
            run.font.bold = bold
            run.font.color.rgb = base_color


def _split_bullets(content: str):
    """Turns raw slide content (a markdown-ish blob, or already-split lines
    joined with \\n by the caller) into a clean list of bullet strings,
    stripping any leading -/*/• markers the model already added."""
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    bullets = []
    for line in lines:
        m = re.match(r"^[-*+•]\s+(.*)$", line)
        bullets.append(m.group(1) if m else line)
    return bullets


def _build_title_slide(prs, title, subtitle, organization):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank

    _add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, NAVY)
    # Decorative overlapping accent shapes — the single biggest lever for
    # making a title slide look designed instead of a plain color fill.
    # python-pptx's ColorFormat has no alpha/transparency API, so "subtle
    # accent" is emulated with an actual blended color (a navy/blue mix)
    # rather than a lighter version of BLUE laid over the background at
    # partial opacity.
    circle1 = slide.shapes.add_shape(MSO_SHAPE.OVAL, SLIDE_W - Inches(4.2), -Inches(2.2), Inches(6), Inches(6))
    _solid(circle1, RGBColor(0x27, 0x4B, 0xB8))
    _no_line(circle1)
    circle1.shadow.inherit = False

    circle2 = slide.shapes.add_shape(MSO_SHAPE.OVAL, SLIDE_W - Inches(2.4), Inches(3.6), Inches(3.2), Inches(3.2))
    _solid(circle2, RGBColor(0x14, 0x2F, 0x73))
    _no_line(circle2)
    circle2.shadow.inherit = False

    accent_bar = _add_rect(slide, Inches(0.7), Inches(3.05), Inches(1.1), Inches(0.08), BLUE)

    _add_text(slide, Inches(0.7), Inches(0.55), Inches(6), Inches(0.4), organization.upper(), 12, LIGHT_BLUE, bold=True)
    _add_text(slide, Inches(0.65), Inches(2.35), Inches(9.5), Inches(1.5), title, 40, WHITE, bold=True)
    if subtitle:
        _add_text(slide, Inches(0.7), Inches(3.3), Inches(9), Inches(0.6), subtitle, 18, LIGHT_BLUE, italic=True)

    ts_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    _add_text(slide, Inches(0.7), SLIDE_H - Inches(0.7), Inches(6), Inches(0.4), f"Generated {ts_str}  |  Confidential On-Premise Document", 10, RGBColor(0x9F, 0xB2, 0xE6))
    return slide


def _build_content_slide(prs, index, slide_title, bullets, organization, source_page=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    accent = ACCENT_CYCLE[index % len(ACCENT_CYCLE)]

    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.15), NAVY)
    _add_rect(slide, 0, Inches(1.15), SLIDE_W, Pt(3), accent)
    _add_text(slide, Inches(0.6), Inches(0.32), SLIDE_W - Inches(1.2), Inches(0.6), slide_title or f"Section {index}", 26, WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    # Small numbered chip top-right — a recurring detail that reads as
    # "designed template" rather than one-off manual formatting.
    chip = slide.shapes.add_shape(MSO_SHAPE.OVAL, SLIDE_W - Inches(1.0), Inches(0.28), Inches(0.6), Inches(0.6))
    _solid(chip, accent)
    _no_line(chip)
    chip.shadow.inherit = False
    chip.text_frame.text = str(index)
    chip.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    chip.text_frame.paragraphs[0].runs[0].font.size = Pt(18)
    chip.text_frame.paragraphs[0].runs[0].font.bold = True
    chip.text_frame.paragraphs[0].runs[0].font.color.rgb = WHITE

    body_top = Inches(1.55)
    body_box = slide.shapes.add_textbox(Inches(0.7), body_top, SLIDE_W - Inches(1.4), SLIDE_H - body_top - Inches(0.7))
    tf = body_box.text_frame
    tf.word_wrap = True

    if not bullets:
        p = tf.paragraphs[0]
        _inline_runs(p, "(no content provided)", 16, MUTED_SLATE)
    else:
        for i, bullet in enumerate(bullets):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(14)
            marker_run = p.add_run()
            marker_run.text = "▸  "
            marker_run.font.size = Pt(18)
            marker_run.font.bold = True
            marker_run.font.color.rgb = accent
            marker_run.font.name = FONT
            _inline_runs(p, bullet, 18, BODY_TEXT)

    if source_page:
        _add_text(slide, Inches(0.7), SLIDE_H - Inches(0.62), Inches(5), Inches(0.3), f"Source: Page {source_page} of original PDF", 10, MUTED_SLATE, italic=True)

    _footer(slide, organization, page_label=f"{index:02d}")
    return slide


def pptx_generate(
    slides_data,
    output_path="board_summary.pptx",
    title="AGNI INDUSTRIAL OPERATIONS",
    subtitle="Equipment Inspection Report",
    organization="AGNI AIR-GAPPED INTELLIGENCE WORKBENCH",
):
    """
    Generate a colorful, custom-styled PowerPoint deck: a designed title
    slide (navy background, layered accent shapes), and content slides with
    a colored header band (color rotates per slide), a numbered chip,
    properly split/styled bullet points (bold/italic/code honored), and a
    consistent footer. Returns the output path.
    """
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    _build_title_slide(prs, title, subtitle, organization)

    for i, slide_info in enumerate(slides_data, start=1):
        if isinstance(slide_info, str):
            slide_info = {"title": slide_info, "content": ""}

        slide_title = slide_info.get("title") or slide_info.get("heading") or ""
        slide_content = slide_info.get("content")
        if slide_content is None:
            slide_content = slide_info.get("text") or slide_info.get("body") or ""
        if isinstance(slide_content, (list, tuple)):
            slide_content = "\n".join(str(c) for c in slide_content)

        bullets = _split_bullets(str(slide_content))
        _build_content_slide(prs, i, str(slide_title), bullets, organization, source_page=slide_info.get("source_page"))

    prs.save(output_path)
    return output_path
