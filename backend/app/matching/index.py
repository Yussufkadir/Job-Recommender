import json
import logging
import math
import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ingestion.normalize import SUPPORTED_COUNTRIES
from app.ingestion.pipeline import as_utc
from app.matching.text import tokenize
from app.models.job_posting import JobPosting

logger = logging.getLogger(__name__)

BM25_K1 = 1.2
BM25_B = 0.75
TITLE_WEIGHT = 3
SKILL_WEIGHT = 2
SIGNATURE_CHECK_SECONDS = 15


@dataclass
class _Postings:
    docs: np.ndarray
    tfs: np.ndarray


@dataclass
class IndexSnapshot:
    ids: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    title_tokens: list[frozenset] = field(default_factory=list)
    skills: list[Optional[list[str]]] = field(default_factory=list)
    country_masks: dict[str, np.ndarray] = field(default_factory=dict)
    remote: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=bool))
    seniority: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=object))
    posted_ts: np.ndarray = field(default_factory=lambda: np.zeros(0))
    embeddings: Optional[np.ndarray] = None
    has_embedding: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=bool))
    postings: dict[str, _Postings] = field(default_factory=dict)
    doc_lengths: np.ndarray = field(default_factory=lambda: np.zeros(0))
    avg_doc_length: float = 1.0

    title_bigrams: list[frozenset] = field(default_factory=list)
    dedupe_keys: list[str] = field(default_factory=list)
    rows_by_dedupe_key: dict[str, list[int]] = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.ids)

    def idf(self, token: str) -> float:
        postings = self.postings.get(token)
        doc_count = len(postings.docs) if postings is not None else 0
        return math.log(1 + (self.size - doc_count + 0.5) / (doc_count + 0.5))

    def bm25(self, query_tokens: list[str]) -> np.ndarray:
        scores = np.zeros(self.size, dtype=np.float32)
        if not self.size:
            return scores
        norm = BM25_K1 * (1 - BM25_B + BM25_B * self.doc_lengths / self.avg_doc_length)
        for token in set(query_tokens):
            postings = self.postings.get(token)
            if postings is None:
                continue
            idf = self.idf(token)
            tf = postings.tfs
            scores[postings.docs] += idf * tf * (BM25_K1 + 1) / (tf + norm[postings.docs])
        return scores


def _build(rows) -> IndexSnapshot:
    snapshot = IndexSnapshot()
    n = len(rows)
    snapshot.ids = np.array([row.id for row in rows], dtype=np.int64)
    snapshot.remote = np.array([bool(row.remote) for row in rows], dtype=bool)
    snapshot.seniority = np.array([row.seniority or "mid" for row in rows], dtype=object)
    snapshot.posted_ts = np.array([
        as_utc(row.posted_at or row.first_seen_at).timestamp() if (row.posted_at or row.first_seen_at) else 0.0
        for row in rows
    ])
    snapshot.country_masks = {code: np.zeros(n, dtype=bool) for code in SUPPORTED_COUNTRIES}

    postings: dict[str, tuple[list[int], list[int]]] = defaultdict(lambda: ([], []))
    doc_lengths = np.zeros(n, dtype=np.float32)
    vectors: list[Optional[np.ndarray]] = []

    for i, row in enumerate(rows):
        for code in (row.countries or "").split(","):
            if code in snapshot.country_masks:
                snapshot.country_masks[code][i] = True

        title_tokens = tokenize(row.title)
        skills = json.loads(row.skills) if row.skills else None
        snapshot.title_tokens.append(frozenset(title_tokens))
        snapshot.title_bigrams.append(frozenset(zip(title_tokens, title_tokens[1:])))
        snapshot.dedupe_keys.append(row.dedupe_key)
        snapshot.rows_by_dedupe_key.setdefault(row.dedupe_key, []).append(i)
        snapshot.skills.append(skills)

        bag = Counter()
        for token in title_tokens:
            bag[token] += TITLE_WEIGHT
        for token in tokenize(" ".join(skills or [])):
            bag[token] += SKILL_WEIGHT
        for token in tokenize(row.company):
            bag[token] += 1
        doc_lengths[i] = sum(bag.values())
        for token, tf in bag.items():
            docs, tfs = postings[token]
            docs.append(i)
            tfs.append(tf)

        vectors.append(np.frombuffer(row.embedding, dtype=np.float32) if row.embedding else None)

    snapshot.postings = {
        token: _Postings(np.array(docs, dtype=np.int32), np.array(tfs, dtype=np.float32))
        for token, (docs, tfs) in postings.items()
    }
    snapshot.doc_lengths = doc_lengths
    snapshot.avg_doc_length = float(doc_lengths.mean()) if n else 1.0

    snapshot.has_embedding = np.array([vector is not None for vector in vectors], dtype=bool)
    dims = next((len(vector) for vector in vectors if vector is not None), 0)
    if dims:
        matrix = np.zeros((n, dims), dtype=np.float32)
        for i, vector in enumerate(vectors):
            if vector is not None and len(vector) == dims:
                matrix[i] = vector
            else:
                snapshot.has_embedding[i] = False
        snapshot.embeddings = matrix
    return snapshot


class JobIndex:
    def __init__(self):
        self._snapshot = IndexSnapshot()
        self._signature = None
        self._checked_at = 0.0
        self._lock = threading.Lock()

    def invalidate(self) -> None:
        self._checked_at = 0.0

    def get(self, db: Session) -> IndexSnapshot:
        if time.monotonic() - self._checked_at < SIGNATURE_CHECK_SECONDS:
            return self._snapshot
        with self._lock:
            signature = db.query(
                func.count(JobPosting.id), func.max(JobPosting.id), func.max(JobPosting.updated_at)
            ).one()
            signature = tuple(str(value) for value in signature)
            if signature != self._signature:
                started = time.monotonic()
                rows = db.query(
                    JobPosting.id, JobPosting.title, JobPosting.company, JobPosting.dedupe_key,
                    JobPosting.countries, JobPosting.remote, JobPosting.seniority, JobPosting.skills, JobPosting.embedding,
                    JobPosting.posted_at, JobPosting.first_seen_at,
                ).all()
                self._snapshot = _build(rows)
                self._signature = signature
                logger.info("Job index rebuilt: %d jobs in %.2fs", len(rows), time.monotonic() - started)
            self._checked_at = time.monotonic()
            return self._snapshot


job_index = JobIndex()
