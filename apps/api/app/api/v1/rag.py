"""RAG query endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.schemas import RagQueryPayload
from app.services import normalize_filters, run_feedback_rag

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query")
def rag_query(
    payload: RagQueryPayload,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    """RAG query over feedback with optional filters."""
    filters = normalize_filters(
        payload.filters.product if payload.filters else None,
        payload.filters.country if payload.filters else None,
        payload.filters.region if payload.filters else None,
        payload.filters.dateFrom if payload.filters else None,
        payload.filters.dateTo if payload.filters else None,
    )
    return run_feedback_rag(session, payload.query, filters)
