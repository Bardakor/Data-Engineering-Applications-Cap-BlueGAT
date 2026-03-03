"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.database import Base, SessionLocal, engine
from app.services import seed_database

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
    """Create tables and optionally seed demo data."""
    Base.metadata.create_all(bind=engine)
    if settings.seed_on_startup:
        with SessionLocal() as session:
            seed_database(session)


@app.get("/")
def read_root() -> dict[str, str]:
    """Root: app info and links."""
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "sales_dashboard": f"{settings.api_prefix}/dashboard/sales",
        "feedback_dashboard": f"{settings.api_prefix}/dashboard/feedback",
        "feedback_ingest": f"{settings.api_prefix}/ingest/feedback",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


app.include_router(api_router)
