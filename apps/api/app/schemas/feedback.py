"""Feedback-related schemas."""

from datetime import date

from pydantic import BaseModel, Field


class FeedbackPayload(BaseModel):
    """Payload for feedback ingestion."""

    username: str = Field(min_length=1)
    feedback_date: date
    campaign_id: str = Field(min_length=1)
    comment: str = Field(min_length=1)
