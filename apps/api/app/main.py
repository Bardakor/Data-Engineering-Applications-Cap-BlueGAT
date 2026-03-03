"""FastAPI application entry point."""

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.database import Base, SessionLocal, engine
from app.services import seed_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("api")

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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log each request with method, path, status, and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    client = request.client.host if request.client else "?"
    logger.info(
        "%s %s %s | %dms | %s",
        request.method,
        request.url.path,
        response.status_code,
        round(duration_ms),
        client,
    )
    return response


@app.on_event("startup")
def startup_event() -> None:
    """Create tables and optionally seed demo data."""
    logger.info("Starting %s", settings.app_name)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready")
    if settings.seed_on_startup:
        with SessionLocal() as session:
            result = seed_database(session)
            logger.info("Seeded demo data: %s", result)
    else:
        logger.info("Seed on startup disabled (SEED_ON_STARTUP=false)")


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
