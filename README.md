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

### Database schema (ER diagram)

```mermaid
erDiagram
    sales {
        int id PK
        string username
        date sale_date
        string country
        string region
        string product
        int quantity
        float unit_price
        float total_amount
        datetime created_at
    }
    campaign_products {
        string campaign_id PK
        string product
        datetime created_at
    }
    feedback {
        int id PK
        string username
        date feedback_date
        string campaign_id FK
        string product
        string country
        string region
        text comment
        string sentiment_label
        float sentiment_score
        json embedding
        datetime created_at
    }
    campaign_products ||--o{ feedback : "campaign_id"
    sales ||--o{ feedback : "username+product lookup"
```

*Logical links: `feedback.campaign_id` → `campaign_products.campaign_id`; feedback enrichment uses `sales` (username + product) to fill country/region.*

### Data flow (api_pusher → API → database)

```mermaid
flowchart LR
    subgraph api_pusher["api_pusher"]
        CSV[CSV mode]
        PUSH[PUSH mode]
    end
    subgraph files["Generated files"]
        sales_csv[sales.csv]
        campaign_csv[campaign_product.csv]
    end
    subgraph API["Nugget API"]
        ingest_campaign[POST /ingest/campaign-mapping-csv]
        ingest_sales[POST /ingest/sales-csv]
        ingest_feedback[POST /ingest/feedback]
    end
    subgraph DB["PostgreSQL"]
        cp[(campaign_products)]
        s[(sales)]
        f[(feedback)]
    end

    CSV --> sales_csv
    CSV --> campaign_csv
    PUSH --> ingest_feedback
    sales_csv --> ingest_sales
    campaign_csv --> ingest_campaign

    ingest_campaign --> cp
    ingest_sales --> s
    ingest_feedback --> f

    s -.->|"enrichment lookup"| ingest_feedback
    cp -.->|"product lookup"| ingest_feedback
```

*Recommended ingestion order: ① campaign mapping → ② sales → ③ feedback.*

---

## Orchestration

The system coordinates data flow through several layers without a dedicated workflow engine. Orchestration is **event-driven** and **request-driven**.

### Startup orchestration

On API startup (`app/main.py`):

1. **Create tables** – `Base.metadata.create_all(bind=engine)` ensures PostgreSQL schema exists
2. **Optional seed** – If `SEED_ON_STARTUP=true` and the database is empty, `seed_database()` populates demo data (campaigns, sales, feedback)
3. **No scheduler** – There is no cron or background job; all ingestion is triggered by HTTP requests or manual CLI runs

### Data generation orchestration (api_pusher)

The **api_pusher** tool is the data producer. It is run manually from the CLI:

| Action | What it does | Output |
|--------|--------------|--------|
| `CSV <count>` | Generates sales + campaign mapping CSVs | `sales.csv`, `campaign_product.csv` on disk |
| `PUSH <count>` | Generates feedbacks and POSTs them to the API | JSON payloads → `POST /api/v1/ingest/feedback` |

Generation mode (`config.ini`):

- **manual** – Random data (no external service)
- **ollama** – AI-generated comments via Ollama

### Ingestion orchestration (order matters)

The API does **not** enforce ingestion order. The user must follow this sequence:

1. **Campaign mapping first** – `POST /ingest/campaign-mapping-csv` so `campaign_id → product` exists
2. **Sales second** – `POST /ingest/sales-csv` so `username + product → country/region` exists
3. **Feedback last** – `POST /ingest/feedback` so enrichment can resolve product, country, region from sales

If feedback is ingested before sales, `enrich_feedback_context()` will still run but will return `(product, None, None)` for unknown users.

### Request orchestration (per request)

Each HTTP request flows through:

```
Client (browser) → Next.js (proxy) → FastAPI → Router → Endpoint → Service → Repository → PostgreSQL
```

- **Dashboard** – `resolve_filters()` → `build_sales_dashboard()` / `build_feedback_dashboard()` → aggregated JSON
- **RAG** – `normalize_filters()` → `run_feedback_rag()` → retrieval + LLM → answer + citations
- **Ingest** – `ingest_*_csv()` / `ingest_feedback_payloads()` → `session.add()` → `session.commit()`

### Control Room orchestration (frontend)

The **Control Room** (`control-room.ts`) aggregates dashboard data client-side to produce:

- **Narrative** – summary, risk, opportunity, action (derived from sales + feedback metrics)
- **Priority signals** – key opportunity, key risk, recommended action
- **Growth chain** – Campaign → Sentiment → Topic → Market → Revenue

No server-side orchestration; the frontend fetches `/dashboard/sales` and `/dashboard/feedback`, then computes the narrative from the combined payloads.

---

## Bronze / Silver / Gold data ingestion pipeline

The platform follows a **medallion-style** data architecture. Data moves from raw sources (bronze) through cleaned/structured storage (silver) to analytics-ready views (gold).

### Bronze layer – raw data

**Sources:**

| Source | Format | Location |
|--------|--------|----------|
| api_pusher CSV mode | `sales.csv`, `campaign_product.csv` | Files on disk (`apps/api/`) |
| api_pusher PUSH mode | JSON `FeedbackPayload[]` | In-memory before HTTP POST |
| Seed | In-code `CAMPAIGN_PRODUCT_MAP`, `COUNTRY_REFERENCE` | `app/data/reference.json` |

**Characteristics:**

- No schema enforcement at ingestion
- Duplicates possible (e.g. same campaign_id in multiple CSV uploads)
- Minimal transformation: CSV parsed, JSON validated by Pydantic

### Silver layer – cleaned, structured data

**Storage:** PostgreSQL tables `campaign_products`, `sales`, `feedback`

**Transformations applied during ingestion:**

| Table | Bronze input | Silver transformation |
|-------|--------------|------------------------|
| `campaign_products` | `campaign_id, product` CSV | Upsert by `campaign_id` |
| `sales` | `username, sale_date, country, product, quantity, unit_price, total_amount` CSV | `region` added via `COUNTRY_REFERENCE[country]["region"]` |
| `feedback` | `username, feedback_date, campaign_id, comment` JSON | `product` from `campaign_products`; `country`, `region` from `sales` (enrichment); `sentiment_label`, `sentiment_score` from VADER |

**Characteristics:**

- Normalized schema, foreign-key-like relationships
- Enrichment (product, country, region, sentiment) applied at write time
- Single source of truth for analytics

### Gold layer – analytics-ready views

**Consumers:**

| Consumer | Source | Output |
|----------|--------|--------|
| Sales dashboard | `sales` + filters | `heroMetrics`, `revenueTrend`, `regionPerformance`, `countryPerformance`, `productMix`, `mapConnections` |
| Feedback dashboard | `feedback` + `sales` | `heroMetrics`, `sentimentTrend`, `campaignImpact`, `topicSignals`, `sentimentByCountry`, `briefs` |
| RAG (CheepChat) | `feedback` (optionally with embeddings) | Retrieved citations + LLM-generated answer |
| Control Room | Both dashboards | Narrative, priority signals, growth chain |

**Characteristics:**

- Aggregated, filtered, and shaped for specific use cases
- No persistent gold tables; views are computed on demand via `build_sales_dashboard()`, `build_feedback_dashboard()`, `run_feedback_rag()`

### Pipeline flow diagram

```mermaid
flowchart TB
    subgraph bronze["Bronze – Raw"]
        csv_files[CSV files]
        json_payloads[JSON payloads]
        seed_ref[reference.json]
    end
    subgraph silver["Silver – Structured"]
        cp[(campaign_products)]
        s[(sales)]
        f[(feedback)]
    end
    subgraph gold["Gold – Analytics"]
        sales_dash[Sales dashboard]
        feedback_dash[Feedback dashboard]
        rag[RAG / CheepChat]
        control[Control Room]
    end

    csv_files --> ingest_campaign[ingest_campaign_csv]
    csv_files --> ingest_sales[ingest_sales_csv]
    json_payloads --> ingest_feedback[ingest_feedback_payloads]
    seed_ref --> seed_database

    ingest_campaign --> cp
    ingest_sales --> s
    ingest_feedback --> f
    seed_database --> cp
    seed_database --> s
    seed_database --> f

    cp --> sales_dash
    s --> sales_dash
    s --> feedback_dash
    f --> feedback_dash
    f --> rag
    sales_dash --> control
    feedback_dash --> control
```

---

## Project structure

- `apps/web`: Next.js 16 frontend
- `apps/api`: FastAPI backend (includes `tools/api_pusher` – fake data generator)
- `docker-compose.yml`: full local stack

### Architecture (Docker stack)

```mermaid
flowchart TB
    subgraph client["Client"]
        browser[Browser :3001]
    end
    subgraph stack["Docker Compose"]
        web[web - Next.js :3000]
        api[api - FastAPI :8000]
        db[(db - PostgreSQL :5432)]
        adminer[adminer :8080]
    end
    subgraph optional["Optional (host)"]
        ollama[Ollama :11434]
    end

    browser --> web
    web -->|API_BASE_URL| api
    api --> db
    adminer --> db
    api -.->|OLLAMA_BASE_URL| ollama
```

### Component diagram

```mermaid
flowchart LR
    subgraph frontend["apps/web"]
        pages[Pages / Dashboards]
        api_route[API proxy route]
    end
    subgraph backend["apps/api"]
        router[API Router]
        dashboard[Dashboard endpoints]
        data[Data endpoints]
        ingest[Ingest endpoints]
        rag[RAG endpoint]
        seed[Seed endpoint]
    end
    subgraph services["Services"]
        dashboards[dashboards.py]
        repositories[repositories.py]
        ingestion[ingestion.py]
        rag_service[rag.py]
    end
    subgraph storage["Storage"]
        postgres[(PostgreSQL)]
    end

    pages --> api_route
    api_route --> router
    router --> dashboard
    router --> data
    router --> ingest
    router --> rag
    router --> seed
    dashboard --> dashboards
    data --> repositories
    ingest --> ingestion
    rag --> rag_service
    dashboards --> postgres
    repositories --> postgres
    ingestion --> postgres
    rag_service --> postgres
```

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

### API overview

```mermaid
flowchart TB
    subgraph root["Root"]
        health["/health"]
        docs["/docs"]
    end
    subgraph v1["/api/v1"]
        dash["/dashboard/sales, /feedback"]
        data["/data/preview, /sales, /feedback, /campaigns"]
        ingest["/ingest/sales-csv, campaign-mapping-csv, feedback"]
        rag["/rag/query"]
        seed["/seed/demo"]
    end

    root --> v1
    dash --> DB[(PostgreSQL)]
    data --> DB
    ingest --> DB
    rag --> DB
    seed --> DB
```

---

## How each endpoint works (detailed)

Each endpoint is wired in `apps/api/app/api/v1/router.py` (prefix `/api/v1`). Root routes live in `apps/api/app/main.py`.

---

### 1. Root & health

| Method | Path | Handler | File |
|--------|------|---------|------|
| `GET` | `/` | `read_root()` | `app/main.py` |
| `GET` | `/health` | `health_check()` | `app/main.py` |
| `GET` | `/docs` | *(FastAPI built-in)* | — |
| `GET` | `/openapi.json` | *(FastAPI built-in)* | — |

**`read_root()`** – Returns `{"name", "docs", "sales_dashboard", "feedback_dashboard", "feedback_ingest"}`. No DB access.

**`health_check()`** – Returns `{"status": "ok"}`. No DB access.

---

### 2. Dashboard

| Method | Path | Handler | File |
|--------|------|---------|------|
| `GET` | `/api/v1/dashboard/sales` | `sales_dashboard()` | `app/api/v1/dashboard.py` |
| `GET` | `/api/v1/dashboard/feedback` | `feedback_dashboard()` | `app/api/v1/dashboard.py` |

**Call chain:**

```
sales_dashboard(filters, session)
  → resolve_filters(product?, country?, region?, date_from?, date_to?)  [app/api/deps.py]
      → normalize_filters()  [services/filters.py]
          → _parse_date_or_default() for dates
  → build_sales_dashboard(session, filters)  [services/dashboards.py]
```

**`build_sales_dashboard()` step-by-step:**

1. `get_sale_rows(session, filters)` – current period
2. `get_sale_rows(session, filters, previous_start, previous_end)` – previous period (same length)
3. `aggregate_sales_period(current_rows)` → `{revenue, units, orders, avg_order}`
4. `aggregate_sales_period(previous_rows)` for deltas
5. Build `region_map`, `country_map`, `product_map`, `trend_map` (by `week_bucket`)
6. `build_filter_options(session)` – distinct products/countries/regions, min/max dates
7. `COUNTRY_REFERENCE` (lat/lng, region) from `app/data/reference.json`
8. `REGION_HUBS` for map connections
9. Return: `heroMetrics`, `revenueTrend`, `regionPerformance`, `countryPerformance`, `productMix`, `mapConnections`, `spotlights`

**`build_feedback_dashboard()` step-by-step:**

1. `get_feedback_rows()` for current and previous period
2. `aggregate_feedback_period()` → `{total, positive_share, negative_share, avg_sentiment}`
3. `sentiment_trend` by week, `campaign_map`, `country_map`
4. `get_sale_rows()` to compute `revenue_by_product` (linked revenue)
5. `extract_topics(current_rows)` – tokenize comments, filter STOPWORDS/TOPIC_KEYWORDS, compute avg sentiment per topic, assign tone (positive/neutral/negative)
6. `build_filter_options(session)`
7. Return: `heroMetrics`, `sentimentTrend`, `campaignImpact`, `topicSignals`, `recentFeedback`, `sentimentByCountry`, `mapConnections`, `briefs`

**Tables:** `sales`, `feedback`, `campaign_products`

**Dashboard flow:**

```mermaid
flowchart TD
    A[GET /dashboard/sales or /feedback] --> B[resolve_filters]
    B --> C[normalize_filters]
    C --> D{Endpoint?}
    D -->|sales| E[build_sales_dashboard]
    D -->|feedback| F[build_feedback_dashboard]
    E --> G[get_sale_rows]
    E --> H[aggregate_sales_period]
    E --> I[build_filter_options]
    F --> J[get_feedback_rows]
    F --> K[aggregate_feedback_period]
    F --> L[extract_topics]
    G --> M[(sales)]
    J --> N[(feedback)]
    H --> O[heroMetrics, trend maps, etc.]
    K --> P[heroMetrics, sentiment, topics, etc.]
```

---

### 3. Data

| Method | Path | Handler | File |
|--------|------|---------|------|
| `GET` | `/api/v1/data/preview` | `data_preview()` | `app/api/v1/data.py` |
| `GET` | `/api/v1/data/sales` | `list_sales()` | `app/api/v1/data.py` |
| `GET` | `/api/v1/data/feedback` | `list_feedback()` | `app/api/v1/data.py` |
| `GET` | `/api/v1/data/campaigns` | `list_campaigns()` | `app/api/v1/data.py` |

**`data_preview()`** (`services/preview.py`):

1. `select(Sale).order_by(sale_date.desc()).limit(40)`
2. `select(Feedback).order_by(feedback_date.desc()).limit(40)`
3. `select(CampaignProduct).order_by(campaign_id)`
4. `serialize_sale`, `serialize_feedback`, `serialize_campaign` for each row
5. Return `{sales, feedback, campaigns}`

**`list_sales()` / `list_feedback()`:**

1. `resolve_filters()` → `normalize_filters()`
2. `get_sale_rows(session, filters)` or `get_feedback_rows(session, filters)` (`services/repositories.py`)
   - `select(Sale|Feedback).where(sale_date|feedback_date.between(dateFrom, dateTo))`
   - Optional `.where(product=...)`, `.where(country=...)`, `.where(region=...)` if not "All"
3. `serialize_sale(row)` or `serialize_feedback(row)` for each
4. Return list of dicts

**`list_campaigns()`:**

1. `select(CampaignProduct).order_by(campaign_id)`
2. `serialize_campaign(row)` for each
3. Return list of `{campaignId, product}`

**Serializers** (`services/serializers.py`):

- `serialize_sale`: `id, username, saleDate, country, region, product, quantity, unitPrice, totalAmount`
- `serialize_feedback`: `id, username, feedbackDate, campaignId, product, country, region, sentimentLabel, sentimentScore, comment`
- `serialize_campaign`: `campaignId, product`

---

### 4. Ingest

| Method | Path | Handler | File |
|--------|------|---------|------|
| `POST` | `/api/v1/ingest/sales-csv` | `ingest_sales_csv_endpoint()` | `app/api/v1/ingest.py` |
| `POST` | `/api/v1/ingest/campaign-mapping-csv` | `ingest_campaign_csv_endpoint()` | `app/api/v1/ingest.py` |
| `POST` | `/api/v1/ingest/feedback` | `ingest_feedback_endpoint()` | `app/api/v1/ingest.py` |

**`ingest_sales_csv_endpoint()`:**

1. `file: UploadFile = File(...)` – multipart form
2. `content = await file.read()`
3. `ingest_sales_csv(session, content)` (`services/ingestion.py`)
   - `csv.DictReader` expects: `username, sale_date, country, product, quantity, unit_price, total_amount`
   - `COUNTRY_REFERENCE[country]["region"]` for region (or "Unknown")
   - `session.add(Sale(...))` per row
   - `session.commit()`
4. Return `{"inserted": N}`

**`ingest_campaign_csv_endpoint()`:**

1. `ingest_campaign_csv(session, content)`
   - CSV: `campaign_id, product`
   - `session.get(CampaignProduct, campaign_id)` – if exists, update `product`; else `session.add(CampaignProduct(...))`
   - Return `{"inserted": N}` (new rows only)

**`ingest_feedback_endpoint()`:**

1. Body: `list[FeedbackPayload]` – Pydantic validates each `{username, feedback_date, campaign_id, comment}`
2. `ingest_feedback_payloads(session, payloads)`
   - For each payload: `enrich_feedback_context(session, username, campaign_id)`
     - `session.get(CampaignProduct, campaign_id)` → product
     - `select(Sale).where(username=...).where(product=...).order_by(sale_date.desc())` → latest sale
     - Return `(product, country, region)` from that sale
   - `analyze_sentiment(comment)` → `(sentiment_label, sentiment_score)` via VADER
   - `session.add(Feedback(...))`
   - `session.commit()`
3. Return `{"inserted": N}`

**Tables:** `sales`, `campaign_products`, `feedback`

**Feedback ingestion flow:**

```mermaid
flowchart TD
    A[POST /ingest/feedback] --> B[FeedbackPayload list]
    B --> C[For each payload]
    C --> D[enrich_feedback_context]
    D --> E[Lookup campaign_id → product]
    D --> F[Lookup username + product in sales]
    E --> G[(campaign_products)]
    F --> H[(sales)]
    D --> I[product, country, region]
    C --> J[analyze_sentiment]
    J --> K[VADER → sentiment_label, score]
    I --> L[Feedback row]
    K --> L
    L --> M[(feedback)]
```

---

### 5. RAG (CheepChat)

| Method | Path | Handler | File |
|--------|------|---------|------|
| `POST` | `/api/v1/rag/query` | `rag_query()` | `app/api/v1/rag.py` |

**Schema:** `RagQueryPayload` – `query: str` (min 3 chars), `filters?: RagFilterPayload` (product, country, region, dateFrom, dateTo)

**Call chain:**

```
rag_query(payload, session)
  → normalize_filters(payload.filters.product, ...)  [services/filters.py]
  → run_feedback_rag(session, payload.query, filters)  [services/rag.py]
```

**`run_feedback_rag()` step-by-step:**

1. `get_feedback_rows(session, filters)` – all feedback in date range + product/country/region filters
2. If empty → return `{answer: "No feedback...", retrievalMode: "empty", generationMode: "fallback", citations: []}`

3. **Scoring:**
   - If `get_openai_client()` (OPENAI_API_KEY set) and `not use_ollama_for_rag`:
     - `ensure_feedback_embeddings(session, feedback_rows, client)` – fill missing `row.embedding` via OpenAI
     - `client.embeddings.create(input=query)` → query_embedding
     - `cosine_similarity(query_embedding, row.embedding)` per row → `retrieval_mode = "openai"`
   - Else:
     - `lexical_score(query, row)` per row – token overlap / sqrt(doc_length) → `retrieval_mode = "lexical"`

4. **Top 5:** `sorted(scored_rows, reverse=True)[:5]` where `score > 0`

5. **Citations:** build `{feedbackId, campaignId, product, country, feedbackDate, sentimentLabel, score, comment}` for each top row

6. **Generation:**
   - If OpenAI client + citations + not use_ollama: `client.chat.completions.create()` or `client.responses.create()` → `generation_mode = "openai"`
   - Elif citations: `answer_with_ollama(query, context)` – POST to `{OLLAMA_BASE_URL}/api/chat` with `{model, messages, options: {num_predict: 150}}`. If success → `generation_mode = "ollama"`; else `answer_without_openai()` → `generation_mode = "fallback"`
   - Else (no citations): `answer_with_ollama(query, "", general_mode=True)` – general Q&A. If success → `ollama`; else `fallback`

7. **`answer_without_openai()`** – Counter on campaign/country/sentiment, top 2 comment examples, template: `"From the retrieved feedback, the main signal is {sentiment} sentiment centered on {campaign}..."`

8. Return `{answer, retrievalMode, generationMode, citations}`

**Tables:** `feedback` (and `embedding` column when OpenAI used)

**RAG query flow:**

```mermaid
flowchart TD
    A[POST /rag/query] --> B[normalize_filters]
    B --> C[get_feedback_rows]
    C --> D{Empty?}
    D -->|yes| E[Return fallback]
    D -->|no| F{OPENAI_API_KEY?}
    F -->|yes| G[ensure_feedback_embeddings]
    G --> H[cosine_similarity]
    F -->|no| I[lexical_score]
    H --> J[Top 5 by score]
    I --> J
    J --> K[Build citations]
    K --> L{OpenAI client?}
    L -->|yes| M[chat.completions.create]
    L -->|no| N{Ollama?}
    N -->|yes| O[POST /api/chat]
    N -->|no| P[answer_without_openai]
    M --> Q[Return answer + citations]
    O --> Q
    P --> Q
```

---

### 6. Seed

| Method | Path | Handler | File |
|--------|------|---------|------|
| `POST` | `/api/v1/seed/demo` | `reseed_demo()` | `app/api/v1/seed.py` |

**`seed_database(session)`** (`services/seed.py`):

1. If `count(Sale) > 0` → return existing counts `{sales, feedback, campaigns}` (no insert)
2. Insert `CampaignProduct` from `CAMPAIGN_PRODUCT_MAP` (reference.json)
3. 220 days of sales: `rng` (seed 42), users `user001`–`user360`, countries/products weighted, `COUNTRY_REFERENCE`, `PRODUCT_PRICES`
4. Sample ~320 sales → create feedback: `POSITIVE_FRAGMENTS` / `NEGATIVE_FRAGMENTS` / `NEUTRAL_FRAGMENTS`, `analyze_sentiment(comment)`, link to campaign via `campaign_by_product`
5. `session.commit()`
6. Return `{sales, feedback, campaigns}`

**Reference:** `app/data/reference.json` – `CAMPAIGN_PRODUCT_MAP`, `COUNTRY_REFERENCE`, `PRODUCT_PRICES`, `seed_fragments`, `topic_keywords`, `stopwords`

---

### File map

| Layer | File | Functions / purpose |
|-------|------|---------------------|
| **API** | `app/main.py` | `read_root`, `health_check`, `startup_event`, CORS, `log_requests` middleware |
| | `app/api/v1/router.py` | `api_router` – includes dashboard, data, ingest, rag, seed |
| | `app/api/v1/dashboard.py` | `sales_dashboard`, `feedback_dashboard` |
| | `app/api/v1/data.py` | `data_preview`, `list_sales`, `list_feedback`, `list_campaigns` |
| | `app/api/v1/ingest.py` | `ingest_sales_csv_endpoint`, `ingest_campaign_csv_endpoint`, `ingest_feedback_endpoint` |
| | `app/api/v1/rag.py` | `rag_query` |
| | `app/api/v1/seed.py` | `reseed_demo` |
| | `app/api/deps.py` | `resolve_filters(product?, country?, region?, date_from?, date_to?)` |
| **Services** | `services/dashboards.py` | `build_sales_dashboard`, `build_feedback_dashboard`, `extract_topics` |
| | `services/repositories.py` | `get_sale_rows`, `get_feedback_rows` |
| | `services/preview.py` | `build_data_preview` |
| | `services/serializers.py` | `serialize_sale`, `serialize_feedback`, `serialize_campaign` |
| | `services/ingestion.py` | `ingest_sales_csv`, `ingest_campaign_csv`, `ingest_feedback_payloads`, `enrich_feedback_context` |
| | `services/filters.py` | `normalize_filters`, `build_filter_options`, `_parse_date_or_default` |
| | `services/rag.py` | `run_feedback_rag`, `answer_with_ollama`, `answer_without_openai`, `lexical_score`, `build_feedback_document`, `cosine_similarity`, `ensure_feedback_embeddings` |
| | `services/seed.py` | `seed_database` |
| | `services/aggregation.py` | `aggregate_sales_period`, `aggregate_feedback_period`, `percentage_delta`, `week_bucket` |
| | `services/sentiment.py` | `analyze_sentiment` (VADER) |
| | `services/clients.py` | `get_openai_client` |
| **Models** | `models/sale.py` | `Sale` – id, username, sale_date, country, region, product, quantity, unit_price, total_amount |
| | `models/feedback.py` | `Feedback` – id, username, feedback_date, campaign_id, product, country, region, comment, sentiment_label, sentiment_score, embedding |
| | `models/campaign_product.py` | `CampaignProduct` – campaign_id (PK), product |
| **Schemas** | `schemas/feedback.py` | `FeedbackPayload` – username, feedback_date, campaign_id, comment |
| | `schemas/rag.py` | `RagQueryPayload`, `RagFilterPayload` |

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

```mermaid
flowchart LR
    subgraph host["localhost"]
        web_port[":3001"]
        api_port[":8001"]
        db_port[":5433"]
        adminer_port[":8080"]
    end
    subgraph containers["Containers"]
        web["web :3000"]
        api["api :8000"]
        db["db :5432"]
        adminer["adminer"]
    end

    web_port --> web
    api_port --> api
    db_port --> db
    adminer_port --> adminer
```

## Notes

- The frontend proxies backend requests through `apps/web/src/app/api/backend/[...path]/route.ts`
- In Docker, the frontend talks to the API with `API_BASE_URL=http://api:8000`
- In local development, the frontend defaults to `http://localhost:8001` if `API_BASE_URL` is not set
- OpenAI is optional; without an API key, RAG uses lexical retrieval + Ollama (if running) for answers
