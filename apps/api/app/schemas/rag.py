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
