import pandas as pd
import sys
import os
import requests


from app.scrapers.adzuna_job_finder import AdzunaJobFinder
from app.scrapers.nofluff_scraper import NoFluffScrapper

class JobAggregator():
    def __init__(self):
        self.adzuna = AdzunaJobFinder()
        self.nofluff = NoFluffScrapper()
        self.scorer_url = os.getenv("RECOMMENDER_URL", "http://127.0.0.1:8001")

    def get_all_jobs(self, query, user_skills=None, seniority=None):
        all_jobs = []

        df_adzuna = self.adzuna.find_jobs(query, seniority=seniority)

        if not df_adzuna.empty:

            adzuna_list = df_adzuna.to_dict("records")
            all_jobs.extend(adzuna_list)

        
        nofluff_jobs = self.nofluff.find_jobs(query, limit=5, seniority=seniority)
        all_jobs.extend(nofluff_jobs)

        df =  pd.DataFrame(all_jobs)

        if df.empty:
            return df
        
        df['decoy_title'] = df['title'].str.lower().str.strip()
        df['decoy_comp'] = df['company'].str.lower().str.strip()

        df = df.drop_duplicates(subset=['decoy_title', 'decoy_comp'], keep='first')

        df = df.drop(columns=['decoy_title', 'decoy_comp'])

        return df

if __name__=="__main__":
    jobs = JobAggregator()
    test_skills = ["Python", "Machine Learning", "TensorFlow", "SQL"]
    
    things = jobs.get_all_jobs(query="AI engineer", user_skills=test_skills)
    
    print(things[['title', 'company', 'score']])
    things.to_csv("jobs.csv")
