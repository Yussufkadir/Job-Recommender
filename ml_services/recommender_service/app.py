from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import spacy
from gensim.models import Word2Vec
import os
import logging
from huggingface_hub import snapshot_download

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 100_000

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
    if len(req.job_description) > MAX_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail="Job description too large")

    doc = nlp(req.job_description.lower())
    job_skills = [ent.text for ent in doc.ents if ent.label_ == "SKILL"]

    logger.debug("Extracted job skills: %s", job_skills)

    if not req.user_skills or not job_skills:
        return {"score": 0.0}

    enforced_skills = [s.lower().strip() for s in req.user_skills]

    valid_user = [s for s in enforced_skills if s in model.wv]
    valid_job = [s for s in job_skills if s in model.wv]

    logger.debug("Valid user skills: %s", valid_user)
    logger.debug("Valid job skills: %s", valid_job)

    if not valid_user or not valid_job:
        return {"score": 0.0}

    similarity = model.wv.n_similarity(valid_user, valid_job)
    logger.debug("Similarity score: %s", similarity)
    return {"score": round(similarity * 100, 1)}

@app.post("/extract")
def extract_skills_endpoint(req: ExtractRequest):
    if len(req.text) > MAX_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail="Text too large")
    doc = nlp(req.text.lower())
    skills = list(set([ent.text.title() for ent in doc.ents if ent.label_ == "SKILL"]))
    return {"skills": skills}