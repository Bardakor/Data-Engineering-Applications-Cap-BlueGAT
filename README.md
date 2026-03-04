# Nugget Data & AI Initiative

Map-first analytics platform with:

- a sales dashboard
- a feedback dashboard
- a CheepChat RAG assistant
- CSV and JSON ingestion endpoints
- **api_pusher** – fake data generator (Ollama or random) for campaign feedbacks & sales

Based on [api_pusher](https://github.com/Prjprj/api_pusher) for the EFREI Data Engineering Applications course.

---

## How the database works

PostgreSQL stores three tables:

| Table             | Purpose                                                                 |
|-------------------|-------------------------------------------------------------------------|
| `sales`           | Transactions: username, sale_date, country, region, product, quantity, amounts |
| `campaign_products` | Mapping: campaign_id → product (e.g. CAMP012 → Chicken Nuggets)      |
| `feedback`        | Customer feedback: username, campaign_id, comment, sentiment (auto-computed) |

**Data flow (api_pusher → API → database):**

1. **api_pusher** generates fake data in two ways:
   - **CSV mode** → creates `sales.csv` and `campaign_product.csv`
   - **PUSH mode** → sends JSON feedback directly to the API

2. **Ingestion order matters:**
   - Upload **campaign mapping** first (so campaign_id → product is known)
   - Upload **sales** second (so username → country/region exists)
   - Push **feedback** last (API enriches each feedback with product/country/region from sales)

3. **Feedback enrichment:** When you ingest feedback, the API looks up the username in `sales` to fill product, country, region. If no sale exists, those fields stay empty.

**Data formats (api_pusher compatible):**

| Type              | Format | Example |
|-------------------|--------|---------|
| Feedback (JSON)   | `username`, `feedback_date`, `campaign_id`, `comment` | `{"username":"user_demo","feedback_date":"2025-01-01","campaign_id":"CAMP012","comment":"demo"}` |
| Sales (CSV)        | `username,sale_date,country,product,quantity,unit_price,total_amount` | `user149,2025-05-10,India,Chicken Nuggets,5,11.14,55.7` |
| Campaign mapping (CSV) | `campaign_id,product` | `CAMP012,Spicy Strips` |

**Visualize the database:** Adminer runs at `http://localhost:8080`. Login: Server `db`, User `nugget`, Password `nugget`, Database `nugget`.

---

## Project structure

- `apps/web`: Next.js 16 frontend
- `apps/api`: FastAPI backend (includes `tools/api_pusher` – fake data generator)
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

For **api_pusher** with AI generation:

- [Ollama](https://ollama.com) (or LM Studio – see config)

## Recommended way: run with Docker

### 1. Create the environment file

From the repository root:

```bash
cp .env.example .env
```

Optional:

- set `OPENAI_API_KEY` if you want OpenAI-backed RAG answers
- or use **Ollama** for local RAG: run `ollama pull tinyllama`, set `OLLAMA_BASE_URL=http://host.docker.internal:11434` in `.env` when using Docker
- keep `SEED_ON_STARTUP=true` if you want demo data loaded automatically on first start

### 2. Start the stack

From the repository root:

```bash
docker compose up --build
```

**Fresh data (wipe DB + seed demo):**

```bash
make newdata
# or: ./scripts/newdata.sh
# or: docker compose down -v && SEED_ON_STARTUP=true docker compose up --build
```

### 3. Open the app

- Web app: `http://localhost:3001`
- API docs: `http://localhost:8001/docs`
- API health: `http://localhost:8001/health`
- Database UI (Adminer): `http://localhost:8080` → Server `db`, User `nugget`, Password `nugget`

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

There are three ways to populate demo data:

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

### Option 3. api_pusher – generate fake data (Ollama or random)

The **api_pusher** tool lives in the backend (`apps/api/tools/api_pusher`) and generates campaign feedbacks and sales data compatible with the Nugget API.

**1. Install Ollama (optional, for AI-generated data)**

```bash
# Install Ollama: https://ollama.com
# Then pull the smallest model (~638MB):
ollama pull tinyllama
```

**2. Ensure the API is running** (Docker or manual) so `http://localhost:8001` is up.

**3. Push feedbacks to the API**

```bash
# From apps/api – manual mode (random, no Ollama needed):
cd apps/api && python -m tools.api_pusher PUSH 10

# With Ollama: edit apps/api/tools/api_pusher/config.ini, set mode = ollama
cd apps/api && python -m tools.api_pusher PUSH 10
```

**4. Generate CSV files** (sales + campaign/product mapping)

```bash
cd apps/api && python -m tools.api_pusher CSV 20
```

This creates `sales.csv` and `campaign_product.csv` in `apps/api/`. Then ingest them:

```bash
curl -X POST http://localhost:8001/api/v1/ingest/campaign-mapping-csv -F "file=@apps/api/campaign_product.csv"
curl -X POST http://localhost:8001/api/v1/ingest/sales-csv -F "file=@apps/api/sales.csv"
```

**Config:** `apps/api/tools/api_pusher/config.ini`

- `endpoint_url` – Nugget API (default `http://localhost:8001/api/v1/ingest/feedback`)
- `ollama_url` – `127.0.0.1:11434` for Ollama; LM Studio uses a different port if you enable its local server
- `ollama_model` – `tinyllama` (smallest, ~638MB) or `phi3:mini`, `llama3.2:1b`, etc.
- `mode` – `manual` (random, no LLM) or `ollama` (local LLM)

**Quick Ollama setup:**

```bash
./scripts/setup-ollama.sh
# or: ollama pull tinyllama
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
- `POST /api/v1/ingest/feedback`

---

## How each endpoint works

### Root & health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Returns app info and links to docs, dashboards, and ingest endpoints. |
| `GET` | `/health` | Health check. Returns `{"status": "ok"}`. |
| `GET` | `/docs` | Swagger UI – interactive API documentation. |
| `GET` | `/openapi.json` | OpenAPI 3.1 schema. |

### Dashboard

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/dashboard/sales` | Sales analytics: revenue, orders, growth by country/region/product, trend over time. |
| `GET` | `/api/v1/dashboard/feedback` | Feedback analytics: sentiment by country/campaign, topic signals, campaign impact. |

**Query parameters** (optional, for both dashboard endpoints):

- `product` – Filter by product (default: `All products`)
- `country` – Filter by country (default: `All countries`)
- `region` – Filter by region (default: `All regions`)
- `date_from` – Start date, ISO format `YYYY-MM-DD`
- `date_to` – End date, ISO format `YYYY-MM-DD`

### Data

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/data/preview` | Sample data for UI preview: last 40 sales, 40 feedback rows, and all campaign mappings. No filters. |
| `GET` | `/api/v1/data/sales` | List all sales rows, optionally filtered by product, country, region, date range. |
| `GET` | `/api/v1/data/feedback` | List all feedback rows, optionally filtered by product, country, region, date range. |
| `GET` | `/api/v1/data/campaigns` | List all campaign–product mappings (campaign_id → product). |

**Query parameters** (optional, for `/sales` and `/feedback`): same as dashboard (`product`, `country`, `region`, `date_from`, `date_to`).

### Ingest

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/ingest/sales-csv` | Upload a sales CSV. Expects `file` (multipart/form-data). Returns `{"sales": N}`. |
| `POST` | `/api/v1/ingest/campaign-mapping-csv` | Upload a campaign mapping CSV. Expects `file` (multipart/form-data). Returns `{"campaigns": N}`. |
| `POST` | `/api/v1/ingest/feedback` | Ingest feedback as JSON array. Each item: `username`, `feedback_date`, `campaign_id`, `comment`. Returns `{"feedback": N}`. |

**Ingestion order:** Upload campaign mapping first, then sales, then feedback (so the API can enrich feedback with product/country/region from sales).

### RAG (CheepChat)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/rag/query` | RAG query over feedback. Retrieves relevant feedback, then generates an answer via Ollama (or OpenAI if configured). |

**Request body** (JSON):

```json
{
  "query": "What are the main complaints in recent feedback?",
  "filters": {
    "product": "All products",
    "country": "All countries",
    "region": "All regions",
    "dateFrom": "2025-09-01",
    "dateTo": "2026-03-04"
  }
}
```

- `query` – Natural language question (min 3 characters).
- `filters` – Optional. Same semantics as dashboard filters. Invalid dates fall back to defaults.

**Response:**

- `answer` – Generated answer (from Ollama, OpenAI, or fallback template).
- `retrievalMode` – `lexical` (keyword) or `openai` (embeddings).
- `generationMode` – `ollama`, `openai`, or `fallback` (proves answer came from LLM vs template).
- `citations` – Up to 5 feedback rows used as context (feedbackId, campaignId, product, country, comment, etc.).

### Seed

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/seed/demo` | Reseed demo data. If tables are empty, inserts sales, campaigns, and feedback. Returns counts (`{"sales": N, "campaigns": N, "feedback": N}`). If already seeded, returns existing counts. |

---

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
curl -X POST http://localhost:8001/api/v1/ingest/feedback \
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
- `ADMINER_PORT` default: `8080` (database web UI)

## Notes

- The frontend proxies backend requests through `apps/web/src/app/api/backend/[...path]/route.ts`
- In Docker, the frontend talks to the API with `API_BASE_URL=http://api:8000`
- In local development, the frontend defaults to `http://localhost:8001` if `API_BASE_URL` is not set
- OpenAI is optional; without an API key, RAG uses lexical retrieval + Ollama (if running) for answers
