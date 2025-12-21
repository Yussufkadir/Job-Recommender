import pandas as pd
import sys
import os
import requests

try:
    from .adzuna_job_finder import AdzunaJobFinder
    from .nofluff_scraper import NoFluffScrapper
except:
    from adzuna_job_finder import AdzunaJobFinder
    from nofluff_scraper import NoFluffScrapper

class JobAggregator():
    def __init__(self):
        self.adzuna = AdzunaJobFinder()
        self.nofluff = NoFluffScrapper()
        self.scorer_url = "http://localhost:8001/score"

    def get_all_jobs(self, query, user_skills=None):
        all_jobs = []

        df_adzuna = self.adzuna.find_jobs(query)

        if not df_adzuna.empty:

            adzuna_list = df_adzuna.to_dict("records")
            all_jobs.extend(adzuna_list)

        
        nofluff_jobs = self.nofluff.find_jobs(query, limit=5)
        all_jobs.extend(nofluff_jobs)

        df =  pd.DataFrame(all_jobs)

        if df.empty:
            return df
        
        df['decoy_title'] = df['title'].str.lower().str.strip()
        df['decoy_comp'] = df['company'].str.lower().str.strip()

        df = df.drop_duplicates(subset=['decoy_title', 'decoy_comp'], keep='first')

        df = df.drop(columns=['decoy_title', 'decoy_comp'])

        if user_skills:
            print("Start of scoring engine.")

            scores = []

            for desc in df['description']:
                try:
                    response = requests.post(self.scorer_url, json={
                        "user_skills": user_skills,
                        "job_description": desc
                    })
                    if response.status_code == 200:
                        scores.append(response.json().get("score", 0.0))
                    else:
                        scores.append(0.0)
                except Exception as e:
                    print(f"Error with scoring with the error: {e}")
                    scores.append(0.0)
            df["score"] = scores
            df = df[df['score'] > 70]
            df = df.sort_values(by='score', ascending=False)
        else:
            df['score'] = 0.0
        
        return df

if __name__=="__main__":
    jobs = JobAggregator()
    test_skills = ["Python", "Machine Learning", "TensorFlow", "SQL"]
    
    things = jobs.get_all_jobs(query="AI engineer", user_skills=test_skills)
    
    print(things[['title', 'company', 'score']])
    things.to_csv("jobs.csv")
