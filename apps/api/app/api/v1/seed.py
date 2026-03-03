"""Seed/demo endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.services import seed_database

router = APIRouter(prefix="/seed", tags=["seed"])


@router.post("/demo")
def reseed_demo(session: Session = Depends(get_session)) -> dict[str, int]:
    """Reseed demo data (or return counts if already seeded)."""
    return seed_database(session)
