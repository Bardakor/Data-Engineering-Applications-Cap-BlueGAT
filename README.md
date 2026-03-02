# Nugget Data & AI Initiative

Map-first analytics platform with:

- a sales dashboard
- a feedback dashboard
- a CheepChat RAG assistant
- CSV and JSON ingestion endpoints

## Project structure

- `apps/web`: Next.js 16 frontend
- `apps/api`: FastAPI backend
- `docker-compose.yml`: full local stack

## Prerequisites

For the recommended Docker flow:

- Docker
- Docker Compose

For a manual local run:

- Node.js 22
- npm
- Python 3.11
- PostgreSQL 16

## Recommended way: run with Docker

### 1. Create the environment file

From the repository root:

```bash
cp .env.example .env
```

Optional:

- set `OPENAI_API_KEY` if you want OpenAI-backed RAG answers
- keep `SEED_ON_STARTUP=true` if you want demo data loaded automatically on first start

### 2. Start the stack

From the repository root:

```bash
docker compose up --build
```

### 3. Open the app

- Web app: `http://localhost:3001`
- API docs: `http://localhost:8001/docs`
- API health: `http://localhost:8001/health`

### 4. Stop the stack

```bash
docker compose down
```

To also remove the PostgreSQL volume and start from a clean database:

```bash
docker compose down -v
```

## Manual local run without Docker

Use this only if you want to run the frontend, API, and database separately.

### 1. Start PostgreSQL

Create a database matching the default backend settings, or provide your own `DATABASE_URL`.

Default connection expected by the API:

```text
postgresql+psycopg://nugget:nugget@localhost:5432/nugget
```

### 2. Start the API

Open a terminal in `apps/api`:

```bash
cd apps/api
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then export the required environment variables and run the server:

```bash
export DATABASE_URL="postgresql+psycopg://nugget:nugget@localhost:5432/nugget"
export CORS_ORIGINS="http://localhost:3000"
export SEED_ON_STARTUP="true"
export OPENAI_API_KEY=""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Notes:

- `SEED_ON_STARTUP=true` seeds demo data on the first API start if the database is empty
- leave `OPENAI_API_KEY` empty if you only want lexical retrieval mode
- if you run the frontend on another port, update `CORS_ORIGINS`

### 3. Start the frontend

Open a second terminal in `apps/web`:

```bash
cd apps/web
npm ci
API_BASE_URL=http://localhost:8001 npm run dev
```

Then open:

- Web app: `http://localhost:3000`

If you want the frontend on port `3001` instead:

```bash
PORT=3001 API_BASE_URL=http://localhost:8001 npm run dev
```

In that case, also set:

```bash
export CORS_ORIGINS="http://localhost:3001"
```

before starting the API.

## First-run data seeding

There are two ways to populate demo data:

### Option 1. Automatic seeding on startup

Set:

```bash
SEED_ON_STARTUP=true
```

This works in both Docker and manual local execution.

### Option 2. Seed manually through the API

If the stack is already running:

```bash
curl -X POST http://localhost:8001/api/v1/seed/demo
```

## API endpoints

Main endpoints:

- `GET /health`
- `GET /docs`
- `GET /api/v1/dashboard/sales`
- `GET /api/v1/dashboard/feedback`
- `POST /api/v1/rag/query`
- `GET /api/v1/data/preview`
- `POST /api/v1/ingest/sales-csv`
- `POST /api/v1/ingest/campaign-mapping-csv`
- `POST /afc/api`

## Quick validation commands

### Health check

```bash
curl http://localhost:8001/health
```

### Seed demo data manually

```bash
curl -X POST http://localhost:8001/api/v1/seed/demo
```

### Check the sales dashboard endpoint

```bash
curl http://localhost:8001/api/v1/dashboard/sales
```

### Send feedback in the `api_pusher` format

```bash
curl -X POST http://localhost:8001/afc/api \
  -H "Content-Type: application/json" \
  -d '[
    {
      "username": "user_demo",
      "feedback_date": "2026-02-20",
      "campaign_id": "CAMP012",
      "comment": "The promo was clear and the nuggets felt fresh."
    }
  ]'
```

### Upload a sales CSV

```bash
curl -X POST http://localhost:8001/api/v1/ingest/sales-csv \
  -F "file=@/path/to/sales.csv"
```

### Upload a campaign mapping CSV

```bash
curl -X POST http://localhost:8001/api/v1/ingest/campaign-mapping-csv \
  -F "file=@/path/to/campaign_product.csv"
```

### Run a RAG query

```bash
curl -X POST http://localhost:8001/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the most common complaints in the latest promotions?",
    "filters": {
      "product": "All products",
      "country": "All countries",
      "region": "All regions",
      "dateFrom": "2025-09-01",
      "dateTo": "2026-03-02"
    }
  }'
```

## Docker ports

These values are read from the root `.env` file:

- `WEB_PORT` default: `3001`
- `API_PORT` default: `8001`
- `DB_PORT` default: `5433`

## Notes

- The frontend proxies backend requests through `apps/web/src/app/api/backend/[...path]/route.ts`
- In Docker, the frontend talks to the API with `API_BASE_URL=http://api:8000`
- In local development, the frontend defaults to `http://localhost:8001` if `API_BASE_URL` is not set
- OpenAI is optional; without an API key, RAG falls back to lexical retrieval
