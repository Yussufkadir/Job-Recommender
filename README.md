# 🎯 Job Recommender

An AI-powered job recommendation platform that reads your CV, understands your skills, and surfaces only the roles that genuinely match your profile — not just keyword hits.

> **Live demo**: [job-recommender-phi.vercel.app](https://job-recommender-phi.vercel.app)

---

## What it does

Most job boards show you everything and let you figure it out. This does the opposite — it reads your CV, extracts your actual skills, and then goes out and finds jobs, scores each one against your profile, and only shows you the ones that cross a 70% semantic match threshold.

You upload your CV once. The rest is automated.

---

## How it works

**1. CV parsing**
Upload a PDF or DOCX. A custom-trained spaCy NER model — trained on annotated resume data — extracts your skills and technologies. Not regex, not keyword lists. An actual named entity model built for this.

**2. Skill enrichment**
Extracted skills are passed through a Gensim knowledge graph that understands relationships between technologies. If your CV says PyTorch, the system also knows you likely know NumPy, Python, and ML pipelines. This gives the matching step a fuller picture of your profile.

**3. Job discovery**
Jobs are fetched live from Adzuna and scraped from NoFluffJobs. You can narrow the search with a job title and seniority level before the scrapers run.

**4. Semantic matching**
Each job description is scored against your skill profile using a semantic similarity model. Only jobs above 70% similarity are shown. No filler, no unrelated listings.

**5. CV tailoring** *(optional)*
For any job you want to apply to, you can generate a tailored version of your CV using Phi-3 Mini. The output can be downloaded as a PDF.

---

## Screenshots

<!-- Screenshots will be added here -->

---

## Features

- Google and GitHub OAuth, plus email/password signup
- Password reset via email
- CV upload (PDF or DOCX)
- Skill extraction via custom spaCy NER model
- Knowledge graph built with Gensim Word2Vec
- Live job scraping from Adzuna and NoFluffJobs
- Semantic job-to-CV matching with a 70% cutoff
- Job title and seniority filters
- AI CV tailoring with Phi-3 Mini
- PDF export of tailored CV

---

## Tech

**Frontend** — SvelteKit  
**Backend** — FastAPI, Pydantic, SQLAlchemy  
**NER** — spaCy (custom trained), Label Studio for annotation  
**Knowledge graph** — Gensim Word2Vec  
**Semantic matching** — Gensim similarity model  
**Job sources** — Adzuna API, NoFluffJobs (Selenium)  
**CV tailoring** — Phi-3 Mini  
**Auth** — JWT, Google OAuth, GitHub OAuth  

---

## Author

**YussufKadir Syurmen** — [@Yussufkadir](https://github.com/Yussufkadir)

---

## License

MIT
