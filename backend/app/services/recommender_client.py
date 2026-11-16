import requests
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RecommenderClient:
    def __init__(self):
        self.api_url = os.getenv("RECOMMENDER_URL", "http://localhost:8001").rstrip("/")
        self.session = requests.Session()

    def _post(self, path: str, payload: dict, timeout: float):
        try:
            response = self.session.post(f"{self.api_url}{path}", json=payload, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            logger.warning("Recommender %s returned %s", path, response.status_code)
        except Exception as e:
            logger.error("Recommender %s failed: %s", path, e)
        return None

    def extract_skills_batch(self, texts: list[str]) -> Optional[list[list[str]]]:
        data = self._post("/extract_batch", {"texts": texts}, timeout=600)
        if data is not None:
            return data.get("skills")

        results = []
        for text in texts:
            single = self._post("/extract", {"text": text}, timeout=120)
            if single is None:
                return None
            results.append([skill.lower() for skill in single.get("skills", [])])
        return results

    def embed(self, texts: list[str]) -> Optional[list[list[float]]]:
        data = self._post("/embed", {"texts": texts}, timeout=300)
        return data.get("embeddings") if data else None

    def score_batch(self, user_skills: list[str], jobs_skills: list[list[str]]) -> Optional[list[dict]]:
        data = self._post("/score_batch", {"user_skills": user_skills, "jobs_skills": jobs_skills}, timeout=120)
        return data.get("results") if data else None
