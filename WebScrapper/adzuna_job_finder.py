import requests
import pandas as pd
import os 
from dotenv import load_dotenv

load_dotenv()

class AdzunaJobFinder:
    def __init__(self, country="pl"):
        self.app_id = os.getenv("ADZUNA_APPLICATION_ID")
        self.app_key = os.getenv("ADZUNA_APPLICATION_KEY")
        self.country = country
        self.base_url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1?app_id={self.app_id}&app_key={self.app_key}"

        if not self.app_id or not self.app_key:
            print("Configure your adzuna env")

        
    def find_jobs(self, query, results_per_page=20):
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": results_per_page,
            "what": query,
            "content-type": "application/json"
        }

        print(f"trying to connect to adzuna api looking for {query}")

        try:
            response = requests.get(self.base_url, params=params)

            if response.status_code == 401:
                print("Could not connect to the Adzuna API activate a key !")
                return pd.DataFrame
            
            response.raise_for_status()
            data = response.json()

            jobs = []
            for item in data.get('results', []):
                jobs.append({
                    "title": item.get('title'),
                    "company": item.get('company', {}).get('display_name'),
                    "location": item.get('location', {}).get('display_name'),
                    "description": item.get('description'),
                    "link": item.get('redirect_url'),
                    "date_posted": item.get('created')
                })
            
            if jobs:
                print(f"Live data fetched: found {len(jobs)} for '{query}'")
            else:
                print(f"No jobs found for {query}")

            return pd.DataFrame(jobs)
        except Exception as e:
            print(f"Connection error: {e}")
            return pd.DataFrame()
    
    def search_from_cv_profile(self, cv_entities):

        titles = [text for text, label in cv_entities if label == "TITLE"]

        if titles:
            query = titles[0]
            print(f"Found role {query}")
        else:
            skills = [text for text, label in cv_entities if label == "SKILL"]
            if skills:
                query = " ".join(skills)
                print(f"smart match: detected role '{query}' from CV") 
            else:
                query = "developer"

        return self.find_jobs(query)
if __name__ == "__main__":
    finder = AdzunaJobFinder()

    df = finder.find_jobs("AI Engineer")

    if not df.empty:
        print("----------------------------------")
        print("            LIVE DATA          ")
        print(df[['title', 'company']].head())

    fake_cv = [
        ("Data Scientist", "TITLE"),
        ("Python", "SKILL"),
        ("Tensorflow", "SKILL")
    ]

    print("\n--- TESTING WITH FAKE CV ---")
    df_fake1 = finder.search_from_cv_profile(fake_cv)
    if not df_fake1.empty:
        print(df_fake1[['title', 'company']].head(2))

    print("\n--- TESTING WITH ONLY SKILLS FAKE CV")
    fake_cv_skills = [
        ("Java", "SKILL"),
        ("Spring Boot", "SKILL"),
        ("Hibernate", "SKILL")
    ]
    df_fake2 = finder.search_from_cv_profile(fake_cv_skills)
    if not df_fake2.empty:
        print(df_fake2[["title", "company"]].head(2))