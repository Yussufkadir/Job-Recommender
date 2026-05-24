# Job Recommender

An AI-assisted job search workspace built for IT professionals. Upload your CV, extract your skills automatically, find matched roles, tailor your application, and track your pipeline — all in one flow.
Built as a personal project to go end to end on full-stack ML: custom NER model, Word2Vec knowledge graph, transformer-based CV tailoring, and a complete FastAPI + SvelteKit application.
Honest status
The live deployment has constraints. The Adzuna job API does not work reliably on the current hosting provider, and the LLM tailoring service runs slower on free-tier infrastructure than locally. The best experience is running it locally where all services have full resources.
What works well

CV parsing and skill extraction (fast, custom IT-domain NER model)
Job-CV similarity scoring via Word2Vec knowledge graph
Application tracker and pipeline dashboard
CV export to PDF

## What is constrained in deployment

Job search depends on Adzuna API availability on the host
CV tailoring via local LLM is slower on free-tier inference


## What the project does

- Parses CVs from PDF and DOCX files
- Extracts skills with a dedicated NLP service
- Aggregates job listings from external sources
- Scores roles against a candidate profile
- Rewrites CV content for a selected job description
- Tracks saved applications and pipeline status in a dashboard
- Exports CV content as a clean PDF

## Stack

- Frontend: SvelteKit
- Backend: FastAPI, SQLAlchemy, JWT auth
- Recommender service: spaCy NER + Word2Vec similarity scoring
- Tailoring service: transformer-based text generation
- Database: SQLite by default

## Repository structure

- `frontend/`: SvelteKit client application
- `backend/`: FastAPI API, auth, job search, CV parsing, tracker endpoints
- `ml_services/recommender_service/`: skills extraction and recommendation scoring
- `ml_services/llm_service/`: CV tailoring service
- `datasets/`: notebooks and training assets used during model development

## Local development

### 1. Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the backend at `http://localhost:8000` by default. You can override it with `VITE_API_URL` or `VITE_BASE_URL`.

### 2. Backend API

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Recommender service

```bash
cd ml_services/recommender_service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8001
```

### 4. CV tailoring service

```bash
cd ml_services/llm_service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8002
```

## Environment variables

Backend values:

- `SECRET_KEY`
- `FRONTEND_URL`
- `BACKEND_URL`
- `RECOMMENDER_URL`
- `LLM_SERVICE_URL`
- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`
- `ADZUNA_APPLICATION_ID`
- `ADZUNA_APPLICATION_KEY`

Frontend values:

- `VITE_API_URL` or `VITE_BASE_URL`

## Notes

- The recommender service downloads model artifacts on first run.
- Job search quality depends on external providers and configured API keys.
- Password reset email delivery requires a valid Resend configuration.

## Status

This repository is structured as a portfolio-ready MVP with separate services for auth, recommendations, CV tailoring, and application tracking.
