from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import spacy
from gensim.models import Word2Vec
import numpy as np
import os
import re
import logging
from huggingface_hub import snapshot_download
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 100_000
MAX_BATCH_TEXTS = 64
MAX_BATCH_TEXT_LENGTH = 8_000
MAX_EMBED_TEXTS = 128
MAX_SCORE_JOBS = 1_000
RELATED_FLOOR, RELATED_CEILING = 0.6, 0.9
SKILL_ALIASES = {
    "golang": "go", "angularjs": "angular", "reactjs": "react", "vuejs": "vue", "nodejs": "node",
    "js": "javascript", "ts": "typescript", "k8s": "kubernetes", "postgres": "postgresql",
    "ml": "machinelearning", "ai": "artificialintelligence", "amazonwebservices": "aws",
    "googlecloudplatform": "gcp", "googlecloud": "gcp", "msazure": "azure", "microsoftazure": "azure",
    "sklearn": "scikitlearn", "tf": "tensorflow", "py": "python", "csharp": "c#", "cplusplus": "c++",
}
MAX_RELATED_CREDIT = 0.5
SET_SIMILARITY_FLOOR, SET_SIMILARITY_RANGE = 0.5, 0.45
COVERAGE_WEIGHT = 0.7
MAX_MISSING_SKILLS = 8

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_NER_PATH = os.path.join(SERVICE_DIR, "transformer-models", "model-best")
LOCAL_W2V_PATH = os.path.join(SERVICE_DIR, "job_recommender.model")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

nlp = None
model = None
embedder = None

def download_models():
    model_dir = snapshot_download(
        repo_id="syurmen/recommender_ner_model",
        local_dir="/tmp/model/ner",
        local_dir_use_symlinks=False
    )

    kg_dir = snapshot_download(
        repo_id="syurmen/knowledge_graph_model",
        local_dir="/tmp/model/kg",
        local_dir_use_symlinks=False
    )

    return os.path.join(model_dir, "transformer-models/model-best"), os.path.join(kg_dir, "job_recommender.model")

def resolve_model_paths():
    """Prefer explicit env paths, then models checked out next to this file, then the HF Hub."""
    ner_path = os.getenv("NER_MODEL_PATH")
    w2v_path = os.getenv("W2V_MODEL_PATH")
    if ner_path and w2v_path:
        return ner_path, w2v_path
    if os.path.isdir(LOCAL_NER_PATH) and os.path.isfile(LOCAL_W2V_PATH):
        return LOCAL_NER_PATH, LOCAL_W2V_PATH
    return download_models()

def load_models():
    global nlp, model, embedder

    ner_path, w2v_path = resolve_model_paths()

    nlp = spacy.load(ner_path)
    model = Word2Vec.load(w2v_path)
    logger.info("Models loaded successfully")

    try:
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
        logger.info("Embedding model %s loaded", EMBEDDING_MODEL)
    except Exception as e:
        logger.error("Embedding model failed to load, /embed disabled: %s", e)
        embedder = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_models()
    yield
    pass

app = FastAPI(lifespan=lifespan)

class ScoreRequests(BaseModel):
    user_skills: list[str]
    job_description: str

class ExtractRequest(BaseModel):
    text: str

class ExtractBatchRequest(BaseModel):
    texts: list[str]

class EmbedRequest(BaseModel):
    texts: list[str]

class ScoreBatchRequest(BaseModel):
    user_skills: list[str]
    jobs_skills: list[list[str]]

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

@app.post("/extract_batch")
def extract_skills_batch(req: ExtractBatchRequest):
    """Lowercase skills for each text, in input order."""
    if len(req.texts) > MAX_BATCH_TEXTS:
        raise HTTPException(status_code=400, detail=f"At most {MAX_BATCH_TEXTS} texts per batch")
    texts = [text[:MAX_BATCH_TEXT_LENGTH].lower() for text in req.texts]
    skills = [
        sorted({ent.text.strip() for ent in doc.ents if ent.label_ == "SKILL" and ent.text.strip()})
        for doc in nlp.pipe(texts, batch_size=8)
    ]
    return {"skills": skills}

@app.post("/embed")
def embed_texts(req: EmbedRequest):
    """Unit-length sentence embeddings, so a dot product is the cosine similarity."""
    if embedder is None:
        raise HTTPException(status_code=503, detail="Embedding model is not available")
    if len(req.texts) > MAX_EMBED_TEXTS:
        raise HTTPException(status_code=400, detail=f"At most {MAX_EMBED_TEXTS} texts per batch")
    vectors = embedder.encode(
        [text[:MAX_BATCH_TEXT_LENGTH] for text in req.texts],
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return {"embeddings": vectors.tolist()}

def _skill_key(skill: str) -> str:
    """'Node.js', 'node js' and 'nodejs' are the same skill; so are 'golang' and 'go'."""
    key = re.sub(r"[\s.\-_/]+", "", skill.lower())
    if key.endswith("js") and key[:-2] in {"node", "react", "vue", "angular", "next", "express", "nest"}:
        key = key[:-2]
    return SKILL_ALIASES.get(key, key)

@app.post("/score_batch")
def score_batch(req: ScoreBatchRequest):
    """How well the user's skills cover each job's skills (0-100), with matched/missing lists.

    Score = weighted mix of soft coverage (share of the job's skills the user has, with
    partial credit for related skills) and the similarity of the two skill sets overall.
    """
    if len(req.jobs_skills) > MAX_SCORE_JOBS:
        raise HTTPException(status_code=400, detail=f"At most {MAX_SCORE_JOBS} jobs per batch")

    user_skills = list(dict.fromkeys(s.lower().strip() for s in req.user_skills if s.strip()))
    user_keys = {_skill_key(s) for s in user_skills}
    valid_user = [s for s in user_skills if s in model.wv]
    user_matrix = (
        np.stack([model.wv.get_vector(s, norm=True) for s in valid_user]) if valid_user else None
    )

    results = []
    for job_skills in req.jobs_skills:
        skills = list(dict.fromkeys(s.lower().strip() for s in job_skills if s.strip()))
        if not skills or not user_skills:
            results.append({"score": 0.0, "matched": [], "missing": skills[:MAX_MISSING_SKILLS]})
            continue

        matched, missing, credits = [], [], []
        for skill in skills:
            closest = 0.0
            if user_matrix is not None and skill in model.wv:
                closest = float(np.max(user_matrix @ model.wv.get_vector(skill, norm=True)))
            if _skill_key(skill) in user_keys:
                matched.append(skill)
                credits.append(1.0)
            else:
                missing.append(skill)
                related = (closest - RELATED_FLOOR) / (RELATED_CEILING - RELATED_FLOOR)
                credits.append(min(max(related, 0.0), 1.0) * MAX_RELATED_CREDIT)
        coverage = sum(credits) / len(credits)

        valid_job = [s for s in skills if s in model.wv]
        set_similarity = 0.0
        if valid_user and valid_job:
            raw = float(model.wv.n_similarity(valid_user, valid_job))
            set_similarity = min(max((raw - SET_SIMILARITY_FLOOR) / SET_SIMILARITY_RANGE, 0.0), 1.0)

        score = COVERAGE_WEIGHT * coverage + (1 - COVERAGE_WEIGHT) * set_similarity
        results.append({
            "score": round(score * 100, 1),
            "matched": matched,
            "missing": missing[:MAX_MISSING_SKILLS],
        })
    return {"results": results}
