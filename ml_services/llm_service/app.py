from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import pipeline


app = FastAPI()

try:
    pipe = pipeline("text-generation", model="microsoft/Phi-3-mini-4k-instruct")
except:
    pipe = None


class TailorRequest(BaseModel):
    cv_text: str
    job_description: str

@app.post("/cv_tailor")
def tailor_cv(req: TailorRequest):
    if not pipe: raise HTTPException(500, "model loading")
    messages = [
        {"role": "system", "content": "You are a professional CV writer. Rewrite the input CV to align with the provided Job Description. OUTPUT RULES: 1. Return ONLY the content of the CV. 2. Do NOT include any introductory or concluding remarks (e.g., 'Here is the tailored CV'). 3. Do NOT include 'AI Suggestions' or reasoning. 4. Maintain the original structure of the CV. 5. Do not consider job description at all, only consider it for reference."},
        {"role": "user", "content": f"### Job Description:\n{req.job_description}\n\n### Original CV:\n{req.cv_text}\n\n### Task:\nRewrite the above CV to match the Job Description and only look at the cv content and do not consider job description at all. Output ONLY the tailored CV."}
    ]
    outputs = pipe(messages, max_new_tokens=1500, do_sample=True, temperature=0.7)
    generated_output = outputs[0]['generated_text'][-1]['content']
    return {"tailored_cv": generated_output}