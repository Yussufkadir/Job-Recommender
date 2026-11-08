# Job Recommender

Job Recommender is an AI-assisted job search workspace that helps a candidate move from CV upload to tailored job applications in one flow.

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
- `JOOBLE_API_KEY` (optional)

Job index values (all optional):

| Variable | Default | Purpose |
|---|---|---|
| `JOBS_DATABASE_URL` | `sqlite:///./jobs.db` (in `backend/`) | Database for the job index, kept separate from users |
| `JOB_INGEST_ENABLED` | `true` | Run collection in a background thread of the API |
| `JOB_INGEST_INTERVAL_HOURS` | `6` | Time between collection runs |
| `JOB_SOURCES` | `ats,adzuna,arbeitnow,remotive,remoteok,jooble` | Source types to collect from |
| `JOB_COUNTRIES` | all supported | Countries for country-based APIs (Adzuna, Jooble) |
| `JOB_EXTRA_BOARDS` | none | Extra company boards, e.g. `greenhouse:slug:Name,lever:slug:Name` |
| `JOB_ENRICH_LIMIT` | `3000` | Max jobs sent for skill extraction + embeddings per run |
| `JOB_STALE_DAYS` | `4` | Remove jobs not seen in this many days |
| `ADZUNA_PAGES` / `ARBEITNOW_PAGES` | `4` / `3` | Pages (50 jobs each for Adzuna) per run |
| `JOB_TRANSLATE` | `true` | Translate non-English postings to English |

Frontend values:

- `VITE_API_URL` or `VITE_BASE_URL`

## How job search works

Job search reads from a job index that a background process keeps up to date. It never
scrapes during a search.

1. **Collection** (`backend/app/sources/`, `backend/app/ingestion/`). Every few hours jobs are
   pulled from sources that offer official access:
   - company job boards on Greenhouse, Lever and Ashby (list in `app/sources/companies.py`)
   - Adzuna (IT category, newest first), Arbeitnow, Remotive, Remote OK, and Jooble if a key is set

   Each job is mapped to the supported countries, translated to English if needed,
   de-duplicated across sources, and stored in the `job_postings` table of the jobs database
   (`JOBS_DATABASE_URL`). That database holds only the job index; accounts and tracker entries
   stay in `DATABASE_URL`, so the index can be wiped and rebuilt without touching user data.
2. **Enrichment**. New or changed jobs get their skills extracted (`/extract_batch`) and a
   description embedding (`/embed`) from the recommender service.
3. **Ranking** (`backend/app/matching/`). A search filters by country, seniority and remote,
   takes candidates from keyword search (BM25 over titles, skills and company) and semantic
   search (embeddings), then scores them on title match, skill coverage (`/score_batch`),
   description similarity and keyword relevance. Each result shows the skills the user
   has and is missing.
4. **Top-up**. When fewer than 10 indexed jobs match a search title, the backend asks
   Adzuna/Jooble for that exact query in the background, so niche searches get better
   on the next try.

Run one collection pass by hand (also suitable for a cron job; set
`JOB_INGEST_ENABLED=false` on the web service if you do this):

```bash
cd backend
python -m app.ingestion                     # all sources
python -m app.ingestion --only greenhouse   # just Greenhouse boards
```

`GET /api/jobs/index-status` reports job counts per source and the last run.

Ranking quality is measured offline with a labeled golden set (Precision@10, NDCG@10,
MRR per ranking variant); see [backend/eval/README.md](backend/eval/README.md).

Backend tests (no network or ML services needed):

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests
```

## Notes

- The recommender service uses `transformer-models/model-best` and `job_recommender.model`
  from its folder when present (or `NER_MODEL_PATH` / `W2V_MODEL_PATH`), otherwise it downloads
  them from the Hugging Face Hub. It also loads `EMBEDDING_MODEL`
  (default `sentence-transformers/all-MiniLM-L6-v2`) for `/embed`.
- With SQLite on a host with an ephemeral disk, the index is rebuilt after each deploy. Use a
  persistent `JOBS_DATABASE_URL` (e.g. Postgres) to keep it.
- While editing backend code with `uvicorn --reload`, each save restarts the server and stops a
  collection in progress. Set `JOB_INGEST_ENABLED=false` for the server and run
  `python -m app.ingestion` in a second terminal instead.
- Remote OK's API terms require linking back to their job page; results link to it directly.
- Password reset email delivery requires a valid Resend configuration.

## Status

This repository is structured as a portfolio-ready MVP with separate services for auth, recommendations, CV tailoring, and application tracking.
