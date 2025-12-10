import requests 
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

class AdzunaJobFinder():
    def __init__(self, country="pl"):
        self.app_id = os.getenv("ADZUNA_APPLICATION_ID")
        self.app_key = os.getenv("ADZUNA_APPLICATION_KEY")
        self.country = country 

        self.base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"

        if not self.app_id or self.app_key:
            print("Adzuna API keys did not found")

    def find_jobs(self, query="python", result_per_page=20):
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": result_per_page,
            "what": query,
            "content-type": "application/json"
        }

        print(f"Search engine searching for {query} in {self.country}")

        try:
            response = requests.get(self.base_url, params=params)

            if response.status_code == 200:
                print("things are ok")
            if response.status_code == 401:
                print("Adzuna Error: 401 Unauthorized (Check API keys)")
                return pd.DataFrame()
            if response.status_code == 429:
                print("Limit reach good old api days are over")

            response.raise_for_status()
            data = response.json()

            jobs = []

            for item in data.get('results', []):
                jobs.append({
                    "title": item.get("title"),
                    "company": item.get("company", {}).get("display_name"),
                    "location": item.get("location", {}).get("display_name"),
                    "description": item.get("description"),
                    "link": item.get("base_url"),
                    "source": "Adzuna API"
                })

            if jobs:
                print(f"Engine found {len(jobs)} jobs.")
            else:
                print("No jobs found by the Engine")
            
            return pd.DataFrame(jobs)
        
        except Exception as e:
            print(f"Adzuna connection error: {e}")
            return pd.DataFrame()
        
if __name__=="__main__":
    test = AdzunaJobFinder()
    test.find_jobs()
