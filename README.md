# Job Recommender

An AI-assisted job search workspace built for IT professionals. Upload your CV, extract your skills automatically, find matched roles, tailor your application, and track your pipeline — all in one flow.
Built as a personal project to go end to end on full-stack ML: custom NER model, Word2Vec knowledge graph, transformer-based CV tailoring, and a complete FastAPI + SvelteKit application.

## Honest status

The live deployment has constraints. The Adzuna job API does not work reliably on the current hosting provider and the LLM tailoring service runs slower on free-tier infrastructure. The best experience is running it locally where all services have full resources.

## Stack

Frontend: SvelteKit
Backend: FastAPI, SQLAlchemy, JWT auth
Recommender service: spaCy NER + Word2Vec similarity scoring
Tailoring service: transformer-based text generation
Database: SQLite by default

# Repository structure

frontend/ — SvelteKit client
backend/ — API, auth, job search, CV parsing, tracker
ml_services/recommender_service/ — skill extraction and scoring
ml_services/llm_service/ — CV tailoring
datasets/ — notebooks and training assets


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
