import requests
import os
import logging

logger = logging.getLogger(__name__)

class RecommenderClient:
    def __init__(self):
        self.api_url = os.getenv("RECOMMENDER_URL", "http://localhost:8001")

    def get_score(self, user_skills, job_description):
        try:
            payload = {
                "user_skills": user_skills,
                "job_description": job_description
            }

            response = requests.post(f"{self.api_url}/score", json=payload, timeout=60)

            if response.status_code == 200:
                return response.json().get("score", 0)
            else:
                logger.warning("Recommender service returned non-200: %s", response)
                return 0

        except Exception as e:
            logger.error("Recommender client connection failed: %s", e)
            return 0
