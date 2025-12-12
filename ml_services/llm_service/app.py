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

@app.post("/tailor")
def tailor_cv(req: TailorRequest):
    if not pipe: raise HTTPException(500, "model loading")

    messages = [
        {"role": "system", "content": "You are a advisor who tailors CV's according to the job requirements. Rewrite the user's ENTIRE CV to match the Job Description precisely. Make sure to fit it into one page. Make sure to keep its same with the user's structure"},
        {"role": "user", "content": f"Job: {req.job_description}\nCV: {req.cv_text}\n\nGENERATE TAILORED CV:"}
    ]

    outputs = pipe(messages, max_new_tokens=1500, do_sample=True, temperature=0.7)
    generated_output = outputs[0]['generated_text'][-1]['content']
    return {"tailored_cv": generated_output}