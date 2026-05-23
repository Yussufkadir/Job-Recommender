from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from deep_translator import GoogleTranslator
import time
import logging

logger = logging.getLogger(__name__)

class NoFluffScrapper:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--log-level=3")
        self.options.add_argument("--disable-dev-shm-usage")

    def find_jobs(self, query, limit=5, seniority=None):
        final_query = query
        if seniority and seniority.lower() != "all":
            final_query = f"{seniority} {query}"
        
        driver = webdriver.Chrome(options=self.options)
        jobs_data = []

        logger.info("Scraper searching for %s...", final_query)

        try:
            url = f"https://nofluffjobs.com/pl/jobs?criteria=keyword%3D'{final_query}'"
            driver.get(url)
            wait = WebDriverWait(driver,10)

            try:
                accept_btn = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "onetrust-accept-btn-handler")))
                accept_btn.click()
            except:
                pass

            try:
                cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.posting-list-item")))
                links = [card.get_attribute("href") for card in cards[:limit]]
            except:
                logger.info("No jobs found by scraper")
                return []
            
            translator = GoogleTranslator(source="auto", target="en")

            for link in links:
                try:
                    driver.get(link)
                    time.sleep(0.5)

                    title = driver.find_element(By.TAG_NAME, "h1").text.strip()

                    try:
                        company = driver.find_element(By.CSS_SELECTOR, "a.inline-block").text.strip()
                    except:
                        company = "Unknow Company"

                    try:
                        content = driver.find_element(By.CSS_SELECTOR, "article").text
                    except:
                        content = driver.find_element(By.ID, "posting-description").text
                    
                    try:
                        content_en = translator.translate(content[:4999])
                    except:
                        content_en = content

                    jobs_data.append({
                        "title": title,
                        "company": company,
                        "location": "Poland",
                        "description": content_en,
                        "link": link,
                        "source": "NoFluffJobs"
                    })
                    logger.info("Scraped job: %s", title)

                except:
                    continue
                
        finally:
            driver.quit()
        
        return jobs_data