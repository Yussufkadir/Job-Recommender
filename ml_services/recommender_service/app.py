from fastapi import FastApi
from pydantic import BaseModel
import spacy 
from gensim.models import Word2Vec
import os

app = FastApi()

model_dir = os.path.join(os.getcwd(), "transformer-models/model-best")
nlp = spacy.load("en_core_web_lg")
model = Word2Vec.load(model_dir)

class ScoreRequests(BaseModel):
    user_skills: list[str]
    job_description: str
    
@app.post("/score")
def calculate_score(req: ScoreRequests):

    doc = nlp(req.job_description.lower())
    job_skills = [ent.text for ent in doc.ents if ent.label_ == "SKILL"]

    if not req.user_skills or not job_skills:
        return {"score": 0.0}
    
    valid_user = [s for s in req.user_skills if s in model.wv]
    valid_job = [s for s in req.job_skills if s in model.wv]

    if not valid_user or not valid_job:
        return {"score": 0.0}
    
    similarity = model.wv.n_similarity(valid_user, valid_job)
    return {"score": round(similarity * 100, 1)}