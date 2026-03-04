"""RAG query schemas."""

from pydantic import BaseModel, Field


class RagFilterPayload(BaseModel):
    """Optional filters for RAG queries."""

    product: str = "All products"
    country: str = "All countries"
    region: str = "All regions"
    dateFrom: str | None = None
    dateTo: str | None = None


class RagQueryPayload(BaseModel):
    """Payload for RAG query endpoint."""

    query: str = Field(min_length=3)
    filters: RagFilterPayload | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "What are the main complaints in recent feedback?",
                    "filters": {
                        "product": "All products",
                        "country": "All countries",
                        "region": "All regions",
                        "dateFrom": "2025-09-01",
                        "dateTo": "2026-03-04",
                    },
                },
            ]
        }
    }
