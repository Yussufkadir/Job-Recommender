from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from ..services.file_processor import extract_text_from_file
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ..services.pdf_generator import generate_pdf_from_tailoring
import os
import httpx

router = APIRouter()

LLM_SERVICE_URL = "http://127.0.0.1:8002/cv_tailor"

class PDFRequest(BaseModel):
    text: str

@router.post("/download_pdf")
async def download_tailored_cv(req: PDFRequest):
    pdf_buffer = generate_pdf_from_tailoring(req.text)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Tailored_CV.pdf"}
    )

async def generate_tailored_cv(cv_text: str, job_description: str) -> str:
    async with httpx.AsyncClient(timeout=360.0) as client:
        try:
            payload = {
                "cv_text": cv_text,
                "job_description": job_description
            }
            response = await client.post(LLM_SERVICE_URL, json=payload)

            if response.status_code == 200:
                return response.json().get("tailored_cv", "No output received")
            else:
                print(f"LLM service error: {response.text}")
                return "Error: LLM service failure."
        except Exception as e:
            print(f"Connection error: {e}")
            return "Error: could not connect to LLM service."

@router.post("/cv_tailor")
async def cv_tailor(background_tasks: BackgroundTasks, file: UploadFile = File(...), job_description: str = Form(...)):
   
    file.file.seek(0, 2)
    if file.file.tell() > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="file is too large for processing")
    
    await file.seek(0)
    
    cv_text = await extract_text_from_file(file)
    if not cv_text:
        raise HTTPException(status_code=400, detail="extraction failed.")
    
    tailored_content = await generate_tailored_cv(cv_text, job_description)

    return {"message": "CV processed successfully", "tailored_cv": tailored_content}

@router.post("/parse_cv")
async def parse_cv_text(file: UploadFile = File(...)):

    file.file.seek(0, 2)
    if file.file.tell() > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="file is too large for processing")
    
    await file.seek(0)

    text = await extract_text_from_file(file)

    if not text:
        raise HTTPException(status_code=400, detail="failed to extract the text.")
    
    skills = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                "http://localhost:8001/extract",
                json={"text": text}
            )
            if response.status_code == 200:
                skills = response.json().get("skills", [])
    except Exception as e:
        print(f"Skill extraction failed: {e}")

    return {"text": text, "skills": skills}

