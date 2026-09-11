from docxtpl import DocxTemplate
from datetime import date


def docx_generate(
    data,
    template_path="template.docx",
    output_path="output.docx"
):
    """
    Generate a Word document from any data
    using a DOCX template.

    The template placeholders should match
    the keys provided in the data dictionary.
    """

    doc = DocxTemplate(template_path)

    # Add current date automatically if not provided
    if "date" not in data:
        data["date"] = str(date.today())

    # Render template using provided data
    doc.render(data)

    # Save generated document
    doc.save(output_path)

    return output_path