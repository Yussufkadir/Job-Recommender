from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import pipeline
import time
import re


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
    print(f"Time taken for generating new cv is {duration:.2f}")
    return {"tailored_cv": clean_output(generated_output)}
