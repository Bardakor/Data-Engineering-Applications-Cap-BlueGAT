from fastapi import Depends, FastAPI, File, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import Base, SessionLocal, engine, get_session
from app.models import CampaignProduct
from app.schemas import FeedbackPayload, RagQueryPayload
from app.services import (
    build_data_preview,
    build_feedback_dashboard,
    build_sales_dashboard,
    get_feedback_rows,
    get_sale_rows,
    ingest_campaign_csv,
    ingest_feedback_payloads,
    ingest_sales_csv,
    normalize_filters,
    run_feedback_rag,
    seed_database,
    serialize_campaign,
    serialize_feedback,
    serialize_sale,
)

app = FastAPI(
    title=settings.app_name,
    default_response_class=ORJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    Base.metadata.create_all(bind=engine)
    if settings.seed_on_startup:
        with SessionLocal() as session:
            seed_database(session)


def resolve_filters(
    product: str | None = Query(default=None),
    country: str | None = Query(default=None),
    region: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
) -> dict[str, str]:
    return normalize_filters(product, country, region, date_from, date_to)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "sales_dashboard": f"{settings.api_prefix}/dashboard/sales",
        "feedback_dashboard": f"{settings.api_prefix}/dashboard/feedback",
        "feedback_ingest": "/afc/api",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/afc/api")
def ingest_feedback_endpoint(
    payloads: list[FeedbackPayload],
    session: Session = Depends(get_session),
) -> dict[str, int]:
    return ingest_feedback_payloads(session, payloads)


@app.post("/api/v1/ingest/sales-csv")
async def ingest_sales_csv_endpoint(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> dict[str, int]:
    content = await file.read()
    return ingest_sales_csv(session, content)


@app.post("/api/v1/ingest/campaign-mapping-csv")
async def ingest_campaign_csv_endpoint(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> dict[str, int]:
    content = await file.read()
    return ingest_campaign_csv(session, content)


@app.get("/api/v1/dashboard/sales")
def sales_dashboard(
    filters: dict[str, str] = Depends(resolve_filters),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    return build_sales_dashboard(session, filters)


@app.get("/api/v1/dashboard/feedback")
def feedback_dashboard(
    filters: dict[str, str] = Depends(resolve_filters),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    return build_feedback_dashboard(session, filters)


@app.post("/api/v1/rag/query")
def rag_query(
    payload: RagQueryPayload,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    filters = normalize_filters(
        payload.filters.product if payload.filters else None,
        payload.filters.country if payload.filters else None,
        payload.filters.region if payload.filters else None,
        payload.filters.dateFrom if payload.filters else None,
        payload.filters.dateTo if payload.filters else None,
    )
    return run_feedback_rag(session, payload.query, filters)


@app.get("/api/v1/data/preview")
def data_preview(session: Session = Depends(get_session)) -> dict[str, object]:
    return build_data_preview(session)


@app.get("/api/v1/data/sales")
def list_sales(
    session: Session = Depends(get_session),
    filters: dict[str, str] = Depends(resolve_filters),
) -> list[dict[str, object]]:
    return [serialize_sale(row) for row in get_sale_rows(session, filters)]


@app.get("/api/v1/data/feedback")
def list_feedback(
    session: Session = Depends(get_session),
    filters: dict[str, str] = Depends(resolve_filters),
) -> list[dict[str, object]]:
    return [serialize_feedback(row) for row in get_feedback_rows(session, filters)]


@app.get("/api/v1/data/campaigns")
def list_campaigns(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    campaigns = session.scalars(select(CampaignProduct).order_by(CampaignProduct.campaign_id.asc())).all()
    return [serialize_campaign(row) for row in campaigns]


@app.post("/api/v1/seed/demo")
def reseed_demo(session: Session = Depends(get_session)) -> dict[str, int]:
    return seed_database(session)
