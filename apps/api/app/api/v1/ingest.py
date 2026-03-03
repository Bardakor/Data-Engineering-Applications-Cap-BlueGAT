"""Data ingestion endpoints."""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_session
from app.schemas import FeedbackPayload
from app.services import ingest_campaign_csv, ingest_feedback_payloads, ingest_sales_csv

router = APIRouter(prefix="/ingest", tags=["ingest"])


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
