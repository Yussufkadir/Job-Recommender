import requests 
import pandas as pd
import os
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

load_dotenv()

class AdzunaJobFinder():
    def __init__(self, country="pl"):
        self.app_id = os.getenv("ADZUNA_APPLICATION_ID")
        self.app_key = os.getenv("ADZUNA_APPLICATION_KEY")
        self.country = country 
        self.translator = GoogleTranslator(source='auto', target='en')

        self.base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"

        if not self.app_id or not self.app_key:
            print("Adzuna API keys did not found")

    def find_jobs(self, query, result_per_page=20, seniority=None):
        final_query = query
        if seniority and seniority.lower() != "all":
            final_query = f"{seniority} {query}"

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": result_per_page,
            "what": final_query,
            "content-type": "application/json"
        }

        print(f"Search engine searching for {final_query} in {self.country}")

        try:
            response = requests.get(self.base_url, params=params)

            if response.status_code == 200:
                print("things are ok")
            if response.status_code == 401:
                print("Adzuna Error: 401 Unauthorized (Check API keys)")
                return pd.DataFrame()
            if response.status_code == 429:
                print("Limit reached")

            response.raise_for_status()
            data = response.json()

            jobs = []
            
            for item in data.get('results', []):
                raw_description = item.get("description", "")
                final_description = raw_description

                if raw_description:
                    try:
                        final_description = self.translator.translate(raw_description[:4999])
                    except Exception as trans_error:
                        print(f"Traslation failed with error: {trans_error}")

                jobs.append({
                    "title": item.get("title"),
                    "company": item.get("company", {}).get("display_name"),
                    "location": item.get("location", {}).get("display_name"),
                    "description": final_description,
                    "link": item.get("redirect_url"),
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
