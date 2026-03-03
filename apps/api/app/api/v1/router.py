"""V1 API router aggregation."""

from fastapi import APIRouter

from app.api.v1 import dashboard, data, ingest, rag, seed

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(dashboard.router)
api_router.include_router(data.router)
api_router.include_router(ingest.router)
api_router.include_router(rag.router)
api_router.include_router(seed.router)
