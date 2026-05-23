from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import pipeline
import time
import re
import json
import logging
import os

logger = logging.getLogger(__name__)

app = FastAPI()

MAX_CV_TEXT_LENGTH = 100_000
MAX_JOB_DESCRIPTION_LENGTH = 20_000

device = "cpu"
if torch.backends.mps.is_available():
    device = "mps"
    logger.info("Mac GPU (MPS) detected, inference will use GPU")
else:
    logger.info("No GPU detected, inference will use CPU")

PHI3_REVISION = os.getenv("PHI3_REVISION", "f9d2efc393b8a8f1b1afb2b3e5c6c6f25be5caaa")

try:
    pipe = pipeline(
        "text-generation",
        model="microsoft/Phi-3-mini-4k-instruct",
        revision=PHI3_REVISION,
        device=device,
        torch_dtype=torch.float16 if device != "cpu" else torch.float32,
        trust_remote_code=True
    )
    logger.info("Model loaded successfully (revision: %s)", PHI3_REVISION)
except Exception as e:
    logger.error("Model load failed: %s", e)
    pipe = None


class TailorRequest(BaseModel):
    cv_text: str
    job_description: str

class ATSRequest(BaseModel):
    cv_text: str
    job_description: str = ""

@app.post("/cv_tailor")
def tailor_cv(req: TailorRequest):
    logger.info("CV tailoring request received")

    if len(req.cv_text) > MAX_CV_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail="CV text too large")
    if len(req.job_description) > MAX_JOB_DESCRIPTION_LENGTH:
        raise HTTPException(status_code=400, detail="Job description too large")

    if not pipe:
        raise HTTPException(status_code=500, detail="Model is not available.")

    start_time = time.time()
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert CV writer and ATS optimisation specialist. "
                "You rewrite CVs to match specific job descriptions while staying completely truthful to the candidate's actual experience. "
                "NEVER invent any new roles, companies, dates, skills, or achievements. "
                "Use ONLY the information present in the original CV. "
                "Return ONLY the tailored CV as plain text with clear section headers (SUMMARY, EXPERIENCE, SKILLS, EDUCATION). "
                "Do NOT include any notes, comments, or explanations after the CV. The output must end with the last section of the CV."
            )
        },
        {
            "role": "user",
            "content": (
                f"### Job Description:\n{req.job_description}\n\n"
                f"### Original CV:\n{req.cv_text}\n\n"
                "### Task:\n"
                "1. Analyse the job description for the top 5–8 key skills and keywords.\n"
                "2. Rewrite the professional summary (2-3 sentences) to directly address the role’s main requirements.\n"
                "3. Reorder bullet points under each role so that the most relevant achievements appear first.\n"
                "4. Incorporate missing keywords naturally into the experience and skills sections, but only if the candidate genuinely possesses them or can reasonably claim them based on their background.\n"
                "5. Quantify results wherever possible (e.g., 'Increased efficiency by 30%' rather than 'Improved processes').\n"
                "6. Remove any experience or skills that are completely irrelevant to this job.\n"
                "7. Output the tailored CV as plain text. Do not add any explanations."
            )
        }
    ]
    formatted_prompt = pipe.tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    def clean_output(text: str) -> str:
         text = re.sub(r"^```\w*\s*", "", text, flags=re.MULTILINE)
         text = re.sub(r"\n```\s*$", "", text)
         return text.strip()

    outputs = pipe(formatted_prompt, return_full_text = False, max_new_tokens=1200, do_sample=True, temperature=0.3, top_p=0.9, repetition_penalty=1.05)
    generated_output = clean_output(outputs[0]['generated_text'].strip())

    duration = time.time() - start_time
    logger.info("CV tailoring completed in %.2fs", duration)
    return {"tailored_cv": clean_output(generated_output)}

@app.post("/ats_score")
def ats_score(req: ATSRequest):
    if len(req.cv_text) > MAX_CV_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail="CV text too large")
    if req.job_description and len(req.job_description) > MAX_JOB_DESCRIPTION_LENGTH:
        raise HTTPException(status_code=400, detail="Job description too large")

    if not pipe:
        raise HTTPException(status_code=500, detail="Model not available.")

    prompt = (
        "You are an ATS (Applicant Tracking System) expert. Analyse the CV against the job description (if provided) or general best practices.\n\n"
        f"CV:\n{req.cv_text}\n\n"
        f"Job Description:\n{req.job_description if req.job_description else 'Not provided – perform a general ATS review.'}\n\n"
        "Return only a valid JSON object (no markdown, no backticks) with exactly these keys:\n"
        '- "score": integer from 0 to 100\n'
        '- "missing_keywords": array of strings\n'
        '- "formatting_issues": array of strings\n'
        '- "suggestions": array of strings\n'
    )

    messages = [{"role": "user", "content": prompt}]
    formatted_prompt = pipe.tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    outputs = pipe(
        formatted_prompt,
        return_full_text=False,
        max_new_tokens=400,
        do_sample=True,
        temperature=0.1,
        top_p=0.9,
        repetition_penalty=1.05
    )

    raw = outputs[0]['generated_text'].strip()


    raw = re.sub(r'```json\s*', '', raw, flags=re.DOTALL)
    raw = re.sub(r'```\s*', '', raw)
    raw = raw.strip()

    start = raw.find('{')
    end = raw.rfind('}')
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end+1]

    result = {
        "score": 0,
        "missing_keywords": [],
        "formatting_issues": [],
        "suggestions": ["Unable to parse ATS analysis. The raw output could not be processed."]
    }

    try:
        parsed = json.loads(raw)
        result = {
            "score": parsed.get("score", 0),
            "missing_keywords": parsed.get("missing_keywords", []),
            "formatting_issues": parsed.get("formatting_issues", []),
            "suggestions": parsed.get("suggestions", [])
        }
    except json.JSONDecodeError:
        pass

    return result