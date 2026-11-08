import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from app.ingestion.pipeline import as_utc
from app.matching.index import IndexSnapshot, JobIndex, job_index
from app.matching.text import tokenize
from app.models.job_posting import JobPosting
from app.services.recommender_client import RecommenderClient

logger = logging.getLogger(__name__)

WEIGHTS = {"title": 0.30, "skills": 0.30, "semantic": 0.25, "keywords": 0.15}
CANDIDATES_PER_SIGNAL = 400
SKILL_QUERY_WEIGHT = 0.5
SEMANTIC_FLOOR, SEMANTIC_CEILING = 0.15, 0.65
MIN_SEMANTIC_ONLY = 0.35
MIN_SEMANTIC_WITHOUT_TITLE = 0.40
FRESHNESS_PENALTY = 0.15
FRESHNESS_DAYS = 60
STRONG_TITLE_MATCH = 0.5
PHRASE_WEIGHT = 0.25
MAX_OTHER_LOCATIONS = 10

SENIORITY_LEVELS = {"intern": "intern", "junior": "junior", "mid": "mid", "senior": "senior"}


@dataclass
class RankResult:
    jobs: list[dict] = field(default_factory=list)
    candidates: int = 0
    strong_title_matches: int = 0
    pool_size: int = 0
    used_semantic: bool = False
    used_skills: bool = False


def _title_match(snapshot: IndexSnapshot, rows: np.ndarray, query_tokens: list[str]) -> np.ndarray:
    if not query_tokens:
        return np.zeros(len(rows), dtype=np.float32)
    weights = {token: snapshot.idf(token) for token in query_tokens}
    total = sum(weights.values()) or 1.0
    query_bigrams = set(zip(query_tokens, query_tokens[1:]))

    scores = np.zeros(len(rows), dtype=np.float32)
    for n, i in enumerate(rows):
        title = snapshot.title_tokens[i]
        coverage = sum(weight for token, weight in weights.items() if token in title) / total
        if query_bigrams:
            phrase = len(query_bigrams & snapshot.title_bigrams[i]) / len(query_bigrams)
            coverage = (1 - PHRASE_WEIGHT) * coverage + PHRASE_WEIGHT * phrase
        scores[n] = coverage
    return scores


def _top(scores: np.ndarray, mask: np.ndarray, k: int) -> np.ndarray:
    eligible = np.flatnonzero(mask & (scores > 0))
    if len(eligible) > k:
        eligible = eligible[np.argpartition(-scores[eligible], k)[:k]]
    return eligible


def rank_jobs(
    db: Session,
    query: str,
    skills: list[str],
    countries: list[str],
    seniority: Optional[str] = None,
    remote_only: bool = False,
    limit: int = 30,
    client: Optional[RecommenderClient] = None,
    weights: Optional[dict[str, float]] = None,
    index: Optional[JobIndex] = None,
    now: Optional[float] = None,
) -> RankResult:
    client = client or RecommenderClient()
    weights = WEIGHTS if weights is None else weights
    snapshot = (index or job_index).get(db)
    now = time.time() if now is None else now
    result = RankResult()
    if not snapshot.size:
        return result

    mask = np.zeros(snapshot.size, dtype=bool)
    for code in countries:
        if code in snapshot.country_masks:
            mask |= snapshot.country_masks[code]
    level = SENIORITY_LEVELS.get((seniority or "").lower())
    if level:
        mask &= snapshot.seniority == level
    if remote_only:
        mask &= snapshot.remote
    result.pool_size = int(mask.sum())
    if not result.pool_size:
        return result

    query_tokens = tokenize(query)
    query_lexical = snapshot.bm25(query_tokens)
    retrieval = query_lexical + SKILL_QUERY_WEIGHT * snapshot.bm25(tokenize(" ".join(skills)))
    candidate_rows = set(_top(retrieval, mask, CANDIDATES_PER_SIGNAL).tolist())

    semantic = None
    if snapshot.embeddings is not None and snapshot.has_embedding.any():
        query_text = query + (". Skills: " + ", ".join(skills[:30]) if skills else "")
        vectors = client.embed([query_text])
        if vectors:
            semantic = snapshot.embeddings @ np.asarray(vectors[0], dtype=np.float32)
            semantic_mask = mask & snapshot.has_embedding & (semantic >= MIN_SEMANTIC_ONLY)
            candidate_rows |= set(_top(semantic, semantic_mask, CANDIDATES_PER_SIGNAL).tolist())
            result.used_semantic = True

    rows = np.array(sorted(candidate_rows), dtype=np.int64)
    title_scores = _title_match(snapshot, rows, query_tokens)
    if query_tokens:
        related = title_scores > 0
        if semantic is not None:
            related |= snapshot.has_embedding[rows] & (semantic[rows] >= MIN_SEMANTIC_WITHOUT_TITLE)
        rows, title_scores = rows[related], title_scores[related]
    result.candidates = len(rows)
    if not len(rows):
        return result

    signals: dict[str, np.ndarray] = {}
    available: dict[str, np.ndarray] = {}

    signals["title"] = title_scores
    available["title"] = np.full(len(rows), bool(query_tokens))

    best_lexical = float(query_lexical[rows].max())
    signals["keywords"] = query_lexical[rows] / best_lexical if best_lexical > 0 else np.zeros(len(rows))
    available["keywords"] = np.full(len(rows), best_lexical > 0)

    if semantic is not None:
        signals["semantic"] = np.clip(
            (semantic[rows] - SEMANTIC_FLOOR) / (SEMANTIC_CEILING - SEMANTIC_FLOOR), 0, 1
        )
        available["semantic"] = snapshot.has_embedding[rows]

    skill_details: list[Optional[dict]] = [None] * len(rows)
    if skills:
        jobs_skills = [snapshot.skills[i] or [] for i in rows]
        scored = client.score_batch(skills, jobs_skills)
        if scored and len(scored) == len(rows):
            skill_details = scored
            signals["skills"] = np.array([item["score"] / 100 for item in scored], dtype=np.float32)
            available["skills"] = np.array([bool(snapshot.skills[i]) for i in rows])
            result.used_skills = True

    total = np.zeros(len(rows), dtype=np.float32)
    weight_sum = np.zeros(len(rows), dtype=np.float32)
    for name, values in signals.items():
        weight = weights.get(name, 0.0) * available[name]
        total += weight * values
        weight_sum += weight
    final = np.divide(total, weight_sum, out=np.zeros_like(total), where=weight_sum > 0)

    age_days = (now - snapshot.posted_ts[rows]) / 86400
    final *= 1 - FRESHNESS_PENALTY * np.clip(age_days / FRESHNESS_DAYS, 0, 1)

    result.strong_title_matches = int((signals["title"] >= STRONG_TITLE_MATCH).sum())

    order, seen_keys = [], set()
    for i in np.argsort(-final):
        key = snapshot.dedupe_keys[rows[i]]
        if key in seen_keys:
            continue
        seen_keys.add(key)
        order.append(i)
        if len(order) == limit:
            break
    siblings = {
        i: [r for r in snapshot.rows_by_dedupe_key[snapshot.dedupe_keys[rows[i]]] if mask[r] and r != rows[i]]
        for i in order
    }

    top_ids = [int(snapshot.ids[rows[i]]) for i in order]
    postings = {job.id: job for job in db.query(JobPosting).filter(JobPosting.id.in_(top_ids))}
    sibling_ids = [int(snapshot.ids[r]) for rs in siblings.values() for r in rs]
    sibling_locations = dict(
        db.query(JobPosting.id, JobPosting.location).filter(JobPosting.id.in_(sibling_ids))
    ) if sibling_ids else {}

    for i in order:
        job = postings.get(int(snapshot.ids[rows[i]]))
        if job is None:
            continue 
        details = skill_details[i] or {}
        other_locations = list(dict.fromkeys(
            location for r in siblings[i]
            if (location := sibling_locations.get(int(snapshot.ids[r]))) and location != job.location
        ))
        result.jobs.append({
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location or ", ".join(job.countries.split(",")).upper(),
            "other_locations": other_locations[:MAX_OTHER_LOCATIONS],
            "other_locations_total": len(other_locations),
            "description": job.description,
            "link": job.url,
            "source": job.source,
            "remote": job.remote,
            "posted_at": as_utc(job.posted_at).isoformat() if job.posted_at else None,
            "match_score": int(round(float(final[i]) * 100)),
            "matched_skills": details.get("matched", []),
            "missing_skills": details.get("missing", []),
            "job_skills": json.loads(job.skills) if job.skills else [],
            "score_breakdown": {
                name: int(round(float(signals[name][i]) * 100))
                for name in signals if available[name][i]
            },
        })
    return result
