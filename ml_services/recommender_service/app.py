from fastapi import FastAPI
from pydantic import BaseModel
import spacy 
from gensim.models import Word2Vec
import os
from huggingface_hub import snapshot_download

MODEL_DIR = snapshot_download(
    repo_id="syurmen/recommender_ner_model",
    local_dir="/tmp/model",
    local_dir_use_symlinks=False
)

KG_DIR = snapshot_download(
    repo_id="syurmen/knowledge_graph_model",
    local_dir="/tmp/model",
    local_dir_use_symlinks=False
)

app = FastAPI()

nlp = spacy.load(os.path.join(MODEL_DIR, "transformer-models/model-best"))
model = Word2Vec.load(os.path.join(KG_DIR, "job_recommender.model"))

class ScoreRequests(BaseModel):
    user_skills: list[str]
    job_description: str

class ExtractRequest(BaseModel):
    text: str
    
@app.post("/score")
def calculate_score(req: ScoreRequests):

    doc = nlp(req.job_description.lower())
    job_skills = [ent.text for ent in doc.ents if ent.label_ == "SKILL"]

    print(f"Extracted Job Skills: {job_skills}")

    if not req.user_skills or not job_skills:
        return {"score": 0.0}
    
    enforced_skills = [s.lower().strip() for s in req.user_skills]

    valid_user = [s for s in enforced_skills if s in model.wv]
    valid_job = [s for s in job_skills if s in model.wv]

    print(f"Valid user skills are: {valid_user}")
    print(f"Valid job skills are: {valid_job}")

    if not valid_user or not valid_job:
        return {"score": 0.0}
    
    similarity = model.wv.n_similarity(valid_user, valid_job)
    print(f"similarity of the job is: {similarity}")
    return {"score": round(similarity * 100, 1)}

@app.post("/extract")
def extract_skills_endpoint(req: ExtractRequest):
    doc = nlp(req.text.lower())
    skills = list(set([ent.text.title() for ent in doc.ents if ent.label_ == "SKILL"]))
    return {"skills": skills}