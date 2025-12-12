import requests
import os

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
                print(f"LLM service error: {response.status_code}")
                return None
            
        except Exception as e:
            print(f"LLM connection failed: {e}")
            return None