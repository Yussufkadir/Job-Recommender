from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from ..services.file_processor import extract_text_from_file
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ..services.pdf_generator import generate_pdf_from_tailoring
from ..core.security import get_current_user
from ..models.user import User
from .auth import limiter
import os
import httpx

router = APIRouter()

def _resolve_service_url(raw_url: str, route: str) -> str:
    normalized_url = raw_url.rstrip("/")
    if normalized_url.endswith(route):
        return normalized_url
    return f"{normalized_url}{route}"


LLM_SERVICE_URL = _resolve_service_url(
    os.getenv("LLM_SERVICE_URL", "http://127.0.0.1:8002"),
    "/cv_tailor"
)
RECOMMENDER_URL = os.getenv("RECOMMENDER_URL", "http://127.0.0.1:8001").rstrip("/")
MAX_CV_TEXT_LENGTH = 100_000
MAX_JOB_DESCRIPTION_LENGTH = 20_000

class PDFRequest(BaseModel):
    text: str
    name: str | None = None

@router.post("/download_pdf")
@router.post("/pdf_generator")
@limiter.limit("10/minute")
async def download_tailored_cv(
    request: Request,
    req: PDFRequest,
    current_user: User = Depends(get_current_user)
):
    if len(req.text) > MAX_CV_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail="CV text is too large for PDF generation.")

    pdf_buffer = generate_pdf_from_tailoring(req.text, req.name)
    download_name = (req.name or "").strip() or "Tailored_CV"
    safe_name = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in download_name).strip("-")

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={safe_name or 'Tailored_CV'}.pdf"}
    )

async def generate_tailored_cv(cv_text: str, job_description: str) -> str:
    async with httpx.AsyncClient(timeout=360.0) as client:
        try:
            payload = {
                "cv_text": cv_text,
                "job_description": job_description
            }
            response = await client.post(LLM_SERVICE_URL, json=payload)
            response.raise_for_status()

            tailored_cv = response.json().get("tailored_cv", "").strip()
            if not tailored_cv:
                raise HTTPException(
                    status_code=502,
                    detail="CV tailoring service returned an empty response."
                )

            return tailored_cv
        except httpx.HTTPStatusError as exc:
            print(f"LLM service error: {exc.response.status_code} {exc.response.text}")
            raise HTTPException(
                status_code=502,
                detail="CV tailoring service returned an error."
            ) from exc
        except httpx.HTTPError as exc:
            print(f"Connection error: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Could not reach the CV tailoring service."
            ) from exc

@router.post("/cv_tailor")
@limiter.limit("5/minute")
async def cv_tailor(
    request: Request,
    file: UploadFile | None = File(default=None),
    cv_text: str | None = Form(default=None),
    job_description: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    if len(job_description) > MAX_JOB_DESCRIPTION_LENGTH:
        raise HTTPException(status_code=400, detail="job description is too large for processing")

    resolved_cv_text = (cv_text or "").strip()

    if file is not None:
        file.file.seek(0, 2)
        if file.file.tell() > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="file is too large for processing")

        await file.seek(0)

        resolved_cv_text = await extract_text_from_file(file)
        if not resolved_cv_text:
            raise HTTPException(status_code=400, detail="extraction failed.")

    if not resolved_cv_text:
        raise HTTPException(status_code=400, detail="Provide a CV file or CV text for tailoring.")

    if len(resolved_cv_text) > MAX_CV_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail="CV text is too large for processing")
    
    tailored_content = await generate_tailored_cv(resolved_cv_text, job_description)

    return {"message": "CV processed successfully", "tailored_cv": tailored_content}

@router.post("/parse_cv")
@limiter.limit("10/minute")
async def parse_cv_text(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):

    file.file.seek(0, 2)
    if file.file.tell() > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="file is too large for processing")
    
    await file.seek(0)

    text = await extract_text_from_file(file)

    if not text:
        raise HTTPException(status_code=400, detail="failed to extract the text.")
    
    skills = []
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{RECOMMENDER_URL}/extract",
                json={"text": text}
            )
            if response.status_code == 200:
                skills = response.json().get("skills", [])
    except Exception as e:
        print(f"Skill extraction failed: {e}")

    return {"text": text, "skills": skills}
