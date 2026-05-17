from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import pipeline
import time


app = FastAPI()

device = "cpu"
if torch.backends.mps.is_available():
    device = "mps"
    print("Mac GPU (MPS) detected! Inference will be on GPU.")
else:
    print("No gpu detected inference will be on cpu.")

try:
    pipe = pipeline(
        "text-generation", 
        model="microsoft/Phi-3-mini-4k-instruct",
        device=device,
        torch_dtype=torch.float16 if device != "cpu" else torch.float32,
        trust_remote_code=True
        )
    print("Model loaded succesfully")
except Exception as e:
    print(f"Model load Failed: {e}")
    pipe = None


class TailorRequest(BaseModel):
    cv_text: str
    job_description: str

@app.post("/cv_tailor")
def tailor_cv(req: TailorRequest):
    print("CV tailoring request is online.")
    
    if not pipe: 
        print("Model not loaded.")
        raise HTTPException(status_code=500, detail="Model is not available.")

    start_time = time.time()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a professional CV writer. Rewrite the candidate CV so it aligns better "
                "with the provided job description while staying truthful to the original content. "
                "Return only the CV text. Do not add explanations, commentary, or introductory "
                "remarks. Preserve the original structure as much as possible and do not invent "
                "experience, skills, or achievements that are not supported by the input CV."
            )
        },
        {
            "role": "user",
            "content": (
                f"### Job Description:\n{req.job_description}\n\n"
                f"### Original CV:\n{req.cv_text}\n\n"
                "### Task:\n"
                "Rewrite the CV so the most relevant experience and skills from the original CV "
                "are highlighted for this role. Output only the tailored CV."
            )
        }
    ]
    outputs = pipe(messages, max_new_tokens=1500, do_sample=True, temperature=0.7)
    generated_output = outputs[0]['generated_text'][-1]['content']

    duration = time.time() - start_time
    print(f"Time taken for generating new cv is {duration:.2f}")
    return {"tailored_cv": generated_output}
