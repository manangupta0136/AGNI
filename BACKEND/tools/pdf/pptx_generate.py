from pptx import Presentation
from pptx.util import Inches, Pt


def pptx_generate(slides_data, output_path="board_summary.pptx"):
    """
    Generate a clean PowerPoint presentation.
    """

    prs = Presentation()

    # -----------------------------
    # TITLE SLIDE
    # -----------------------------

    slide = prs.slides.add_slide(prs.slide_layouts[0])

    slide.shapes.title.text = "AGNI INDUSTRIAL OPERATIONS"
    slide.placeholders[1].text = "Equipment Inspection Report"


    # -----------------------------
    # CONTENT SLIDES
    # -----------------------------

    for slide_info in slides_data:

        slide = prs.slides.add_slide(prs.slide_layouts[5])

        # Title
        title_box = slide.shapes.add_textbox(
            Inches(0.6),
            Inches(0.4),
            Inches(12),
            Inches(0.7)
        )

        title_frame = title_box.text_frame
        title_frame.text = slide_info["title"]

        title_frame.paragraphs[0].font.size = Pt(26)
        title_frame.paragraphs[0].font.bold = True


        # Content
        content_box = slide.shapes.add_textbox(
            Inches(0.8),
            Inches(1.4),
            Inches(11.5),
            Inches(5.2)
        )

        content_frame = content_box.text_frame
        content_frame.word_wrap = True
        content_frame.text = slide_info["content"]

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(18)


        # Source page
        source_page = slide_info.get("source_page")

        if source_page:

            source_box = slide.shapes.add_textbox(
                Inches(0.8),
                Inches(6.8),
                Inches(5),
                Inches(0.4)
            )

            source_box.text_frame.text = (
                f"Source: Page {source_page} of original PDF"
            )

            source_box.text_frame.paragraphs[0].font.size = Pt(11)


    # Save
    prs.save(output_path)

    return output_path