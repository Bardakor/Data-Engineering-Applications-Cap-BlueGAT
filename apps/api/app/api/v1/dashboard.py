"""Dashboard endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import resolve_filters
from app.database import get_session
from app.services import build_feedback_dashboard, build_sales_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/sales")
def sales_dashboard(
    filters: dict[str, str] = Depends(resolve_filters),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    """Sales analytics dashboard."""
    return build_sales_dashboard(session, filters)


@router.get("/feedback")
def feedback_dashboard(
    filters: dict[str, str] = Depends(resolve_filters),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    """Feedback analytics dashboard."""
    return build_feedback_dashboard(session, filters)
