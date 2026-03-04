"""Data ingestion endpoints."""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_session
from app.schemas import FeedbackPayload
from app.services import (
    get_valid_feedback_pairs,
    ingest_campaign_csv,
    ingest_feedback_payloads,
    ingest_sales_csv,
)

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.get("/feedback-valid-pairs")
def get_feedback_valid_pairs_endpoint(
    session: Session = Depends(get_session),
    limit: int = 500,
) -> list[dict[str, str]]:
    """Return (username, campaign_id) pairs that have matching sales for enrichment."""
    return get_valid_feedback_pairs(session, limit=limit)


@router.post("/sales-csv")
async def ingest_sales_csv_endpoint(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> dict[str, int]:
    """Upload sales CSV."""
    content = await file.read()
    return ingest_sales_csv(session, content)


@router.post("/campaign-mapping-csv")
async def ingest_campaign_csv_endpoint(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> dict[str, int]:
    """Upload campaign-product mapping CSV."""
    content = await file.read()
    return ingest_campaign_csv(session, content)


@router.post("/feedback")
def ingest_feedback_endpoint(
    payloads: list[FeedbackPayload],
    session: Session = Depends(get_session),
) -> dict[str, int]:
    """Ingest feedback payloads."""
    return ingest_feedback_payloads(session, payloads)
