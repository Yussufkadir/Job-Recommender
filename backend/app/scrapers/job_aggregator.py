import pandas as pd
import sys
import os

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

    def get_all_jobs(self, query):
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

        return df

if __name__=="__main__":
    jobs = JobAggregator()
    things = jobs.get_all_jobs(query="AI engineer")
    things.to_csv("jobs.csv")
