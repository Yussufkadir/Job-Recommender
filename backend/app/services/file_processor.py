from pypdf import PdfReader
from docx import Document
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)

VALID_CONTENT_TYPES = {
    "pdf": ["application/pdf", "application/x-pdf"],
    "docx": [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    ],
}

async def extract_text_from_file(file: UploadFile) -> str:
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    if filename.endswith(".pdf"):
        file_type = "pdf"
    elif filename.endswith(".docx"):
        file_type = "docx"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload a PDF or DOCX file.")

    allowed_types = VALID_CONTENT_TYPES.get(file_type, [])
    if content_type and content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File content type '{file.content_type}' does not match its extension.",
        )

    content = ""
    try:
        if file_type == "pdf":
            reader = PdfReader(file.file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"
        elif file_type == "docx":
            doc = Document(file.file)
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    content += paragraph.text + "\n"

        return content.strip()

    except Exception as e:
        logger.error("Error reading file: %s", e)
        raise HTTPException(status_code=500, detail="Couldn't read the file.")
