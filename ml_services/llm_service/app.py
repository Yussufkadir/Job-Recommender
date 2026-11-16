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

MODEL_CONTEXT_TOKENS = int(os.getenv("LLM_CONTEXT_TOKENS", "4096"))
TAILOR_MAX_NEW_TOKENS = 1200
ATS_MAX_NEW_TOKENS = 400
MIN_JOB_DESCRIPTION_TOKENS = 256
TOKEN_SAFETY_MARGIN = 16

device = "cpu"
if torch.backends.mps.is_available():
    device = "mps"
    logger.info("Mac GPU (MPS) detected, inference will use GPU")
else:
    logger.info("No GPU detected, inference will use CPU")


try:
    pipe = pipeline(
        "text-generation",
        model="microsoft/Phi-3-mini-4k-instruct",
        device=device,
        torch_dtype=torch.float16 if device != "cpu" else torch.float32,
        trust_remote_code=True
    )
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error("Model load failed: %s", e)
    pipe = None


class TailorRequest(BaseModel):
    cv_text: str
    job_description: str

class ATSRequest(BaseModel):
    cv_text: str
    job_description: str = ""


def _encode(text: str) -> list[int]:
    return pipe.tokenizer.encode(text, add_special_tokens=False)


def _render_prompt(messages: list[dict]) -> str:
    return pipe.tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )


def _fit_prompt(build_messages, cv_text: str, job_description: str, max_new_tokens: int) -> str:
    """Render the chat prompt so it plus max_new_tokens fits the model's context window.

    The job description is trimmed first; a CV that cannot fit even with a
    minimal job description is rejected rather than silently cut.
    """
    budget = MODEL_CONTEXT_TOKENS - max_new_tokens - TOKEN_SAFETY_MARGIN

    prompt = _render_prompt(build_messages(cv_text, job_description))
    overflow = len(_encode(prompt)) - budget
    if overflow <= 0:
        return prompt

    job_tokens = _encode(job_description)
    keep = len(job_tokens) - overflow
    if job_tokens and keep >= min(len(job_tokens), MIN_JOB_DESCRIPTION_TOKENS):
        keep = max(keep - TOKEN_SAFETY_MARGIN, 0)
        trimmed = pipe.tokenizer.decode(job_tokens[:keep], skip_special_tokens=True)
        prompt = _render_prompt(build_messages(cv_text, trimmed))
        if len(_encode(prompt)) <= budget:
            logger.info("Job description trimmed from %d to %d tokens", len(job_tokens), keep)
            return prompt

    cv_tokens = len(_encode(cv_text))
    reclaimable = len(job_tokens) - min(len(job_tokens), MIN_JOB_DESCRIPTION_TOKENS)
    max_cv_tokens = max(cv_tokens - overflow + reclaimable, 0)
    raise HTTPException(
        status_code=400,
        detail=(
            f"Your CV is too long for the AI model (about {cv_tokens} tokens). "
            f"Shorten it to roughly {int(max_cv_tokens * 0.75)} words and try again."
        ),
    )


def _tailor_messages(cv_text: str, job_description: str) -> list[dict]:
    return [
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
                f"### Job Description:\n{job_description}\n\n"
                f"### Original CV:\n{cv_text}\n\n"
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


def _ats_messages(cv_text: str, job_description: str) -> list[dict]:
    prompt = (
        "You are an ATS (Applicant Tracking System) expert. Analyse the CV against the job description (if provided) or general best practices.\n\n"
        f"CV:\n{cv_text}\n\n"
        f"Job Description:\n{job_description if job_description else 'Not provided – perform a general ATS review.'}\n\n"
        "Return only a valid JSON object (no markdown, no backticks) with exactly these keys:\n"
        '- "score": integer from 0 to 100\n'
        '- "missing_keywords": array of strings\n'
        '- "formatting_issues": array of strings\n'
        '- "suggestions": array of strings\n'
    )
    return [{"role": "user", "content": prompt}]


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
    formatted_prompt = _fit_prompt(
        _tailor_messages, req.cv_text, req.job_description, TAILOR_MAX_NEW_TOKENS
    )

    def clean_output(text: str) -> str:
         text = re.sub(r"^```\w*\s*", "", text, flags=re.MULTILINE)
         text = re.sub(r"\n```\s*$", "", text)
         return text.strip()

    outputs = pipe(formatted_prompt, return_full_text = False, max_new_tokens=TAILOR_MAX_NEW_TOKENS, do_sample=True, temperature=0.3, top_p=0.9, repetition_penalty=1.05)
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

    formatted_prompt = _fit_prompt(
        _ats_messages, req.cv_text, req.job_description, ATS_MAX_NEW_TOKENS
    )

    outputs = pipe(
        formatted_prompt,
        return_full_text=False,
        max_new_tokens=ATS_MAX_NEW_TOKENS,
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