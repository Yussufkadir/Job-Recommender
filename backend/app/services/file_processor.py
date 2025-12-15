import os
from pypdf import PdfReader
from docx import Document
from fastapi import UploadFile, HTTPException

async def extract_text_from_file(file:UploadFile) -> str:
    filename = file.filename.lower()
    content = ""

    if filename.endswith("pdf"):
        pass
    elif filename.endswith("docx"):
        pass
    else:
        raise HTTPException(status_code=400, detail="Please upload PDF or a DOCX file")

    try:
        if filename.endswith("pdf"):
            reader = PdfReader(file.file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"
        elif filename.endswith("docx"):
            doc = Document(file.file)
            for paragraph in doc.paragraphs:
                content += paragraph + "\n"
        
        return content.strip()
    
    except Exception as e:
        print(f"Error in reading the files: {e}")
        raise HTTPException(status_code=500, detail="Couldn't read the file.")