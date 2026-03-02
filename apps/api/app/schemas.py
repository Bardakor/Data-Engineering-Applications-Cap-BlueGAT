from datetime import date

from pydantic import BaseModel, Field


class FeedbackPayload(BaseModel):
    username: str = Field(min_length=1)
    feedback_date: date
    campaign_id: str = Field(min_length=1)
    comment: str = Field(min_length=1)


class RagFilterPayload(BaseModel):
    product: str = "All products"
    country: str = "All countries"
    region: str = "All regions"
    dateFrom: str | None = None
    dateTo: str | None = None


class RagQueryPayload(BaseModel):
    query: str = Field(min_length=3)
    filters: RagFilterPayload | None = None
