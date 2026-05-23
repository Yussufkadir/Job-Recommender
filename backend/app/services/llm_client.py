import requests
import os
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_url = os.getenv("LLM_SERVICE_URL", "http://localhost:8002")

    
    def tailor_cv(self, cv_text, job_description):
        try:
            payload = {
                "cv_text": cv_text,
                "job_description": job_description
            }

            response = requests.post(f"{self.api_url}/tailor", json=payload, timeout=60)

            if response.status_code == 200:
                return response.json().get("tailored_cv")
            else:
                logger.warning("LLM service returned non-200: %s", response.status_code)
                return None

        except Exception as e:
            logger.error("LLM client connection failed: %s", e)
            return None