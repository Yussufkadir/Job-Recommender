# Frontend

This directory contains the SvelteKit frontend for Job Recommender.

## Scripts

```bash
npm install
npm run dev
npm run check
npm run lint
npm run build
```

## Environment

Set one of the following variables to point the frontend at the backend API:

- `VITE_API_URL`
- `VITE_BASE_URL`

If neither value is set, the frontend falls back to `http://localhost:8000`.

See the repository root [README](../README.md) for the full project overview and multi-service setup.
