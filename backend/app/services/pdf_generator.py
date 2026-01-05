import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

def generate_pdf_from_tailoring(text: str) -> io.BytesIO:

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter


    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "CV")

    c.setFont("Helvetica", 11)
    y_position = height - 80
    margin = 50
    max_width = width - (2 * margin)

    paragraphs = text.split('\n')

    for paragraph in paragraphs:
        lines = simpleSplit(paragraph, "Helvetica", 11, max_width)

        for line in lines:
            if y_position < 50:
                c.showPage()
                c.setFont("Helvetica", 11)
                y_position = height - 50

            c.drawString(margin, y_position, line)
            y_position -= 14

        y_position -= 6
    
    c.save()
    buffer.seek(0)
    return buffer

