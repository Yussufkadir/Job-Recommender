import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

DEFAULT_CV_NAME = "Candidate Name"
TITLE_FONT = "Helvetica-Bold"
BODY_FONT = "Helvetica"
TITLE_SIZE = 16
HEADER_SIZE = 12
BODY_SIZE = 11
TOP_MARGIN = 50
SIDE_MARGIN = 50
BOTTOM_MARGIN = 50


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _resolve_display_name(text: str, name: str | None) -> str:
    candidate_name = (name or "").strip()
    if candidate_name:
        return candidate_name

    for line in text.splitlines():
        stripped_line = line.strip()
        if stripped_line:
            return stripped_line[:120]

    return DEFAULT_CV_NAME


def _strip_duplicate_leading_name(text: str, display_name: str) -> str:
    lines = text.splitlines()
    normalized_name = _normalize_name(display_name)

    for index, line in enumerate(lines):
        stripped_line = line.strip()
        if not stripped_line:
            continue

        if _normalize_name(stripped_line) == normalized_name:
            del lines[index]
        break

    return "\n".join(lines).strip()


def generate_pdf_from_tailoring(text: str, name: str | None = None) -> io.BytesIO:
    display_name = _resolve_display_name(text, name)
    body_text = _strip_duplicate_leading_name(text, display_name)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setAuthor("CV Generator")
    c.setTitle(f"CV - {display_name}")
    c.setSubject("Job Application")

    c.setFont(TITLE_FONT, TITLE_SIZE)
    c.drawString(SIDE_MARGIN, height - TOP_MARGIN, display_name.upper())

    c.setFont(BODY_FONT, BODY_SIZE)
    y_position = height - 80
    max_width = width - (2 * SIDE_MARGIN)

    paragraphs = body_text.split("\n") if body_text else []

    for paragraph in paragraphs:
        if not paragraph.strip():
            y_position -= 6
            continue

        stripped_paragraph = paragraph.strip()
        is_header = stripped_paragraph.isupper() or stripped_paragraph.endswith(":")

        if is_header:
            c.setFont(TITLE_FONT, HEADER_SIZE)
            y_position -= 6
        else:
            c.setFont(BODY_FONT, BODY_SIZE)

        font_name = TITLE_FONT if is_header else BODY_FONT
        font_size = HEADER_SIZE if is_header else BODY_SIZE
        lines = simpleSplit(paragraph, font_name, font_size, max_width)

        for line in lines:
            if y_position < BOTTOM_MARGIN:
                c.showPage()
                if is_header:
                    c.setFont(TITLE_FONT, HEADER_SIZE)
                else:
                    c.setFont(BODY_FONT, BODY_SIZE)
                y_position = height - TOP_MARGIN

            c.drawString(SIDE_MARGIN, y_position, line)
            y_position -= 14

        if is_header:
            y_position -= 4
        else:
            y_position -= 2

    c.save()
    buffer.seek(0)
    return buffer
