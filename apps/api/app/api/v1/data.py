"""Data listing and preview endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import resolve_filters
from app.database import get_session
from app.models import CampaignProduct
from app.services import (
    build_data_preview,
    get_feedback_rows,
    get_sale_rows,
    serialize_campaign,
    serialize_feedback,
    serialize_sale,
)

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/preview")
def data_preview(session: Session = Depends(get_session)) -> dict[str, object]:
    """Sample data for UI preview."""
    return build_data_preview(session)


@router.get("/sales")
def list_sales(
    session: Session = Depends(get_session),
    filters: dict[str, str] = Depends(resolve_filters),
) -> list[dict[str, object]]:
    """List sales with optional filters."""
    return [serialize_sale(row) for row in get_sale_rows(session, filters)]


@router.get("/feedback")
def list_feedback(
    session: Session = Depends(get_session),
    filters: dict[str, str] = Depends(resolve_filters),
) -> list[dict[str, object]]:
    """List feedback with optional filters."""
    return [serialize_feedback(row) for row in get_feedback_rows(session, filters)]


@router.get("/campaigns")
def list_campaigns(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    """List campaign-product mappings."""
    campaigns = list(
        session.scalars(select(CampaignProduct).order_by(CampaignProduct.campaign_id.asc()))
    )
    return [serialize_campaign(row) for row in campaigns]
