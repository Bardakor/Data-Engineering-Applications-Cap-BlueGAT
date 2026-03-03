"""Data access layer: filtered queries for sales and feedback."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Feedback, Sale


def get_sale_rows(
    session: Session,
    filters: dict[str, str],
    start: date | None = None,
    end: date | None = None,
) -> list[Sale]:
    """Return sales rows matching filters and date range."""
    date_start = start or date.fromisoformat(filters["dateFrom"])
    date_end = end or date.fromisoformat(filters["dateTo"])
    statement = select(Sale).where(Sale.sale_date.between(date_start, date_end))

    if filters["product"] != "All products":
        statement = statement.where(Sale.product == filters["product"])
    if filters["country"] != "All countries":
        statement = statement.where(Sale.country == filters["country"])
    if filters["region"] != "All regions":
        statement = statement.where(Sale.region == filters["region"])

    return list(session.scalars(statement.order_by(Sale.sale_date.asc(), Sale.id.asc())))


def get_feedback_rows(
    session: Session,
    filters: dict[str, str],
    start: date | None = None,
    end: date | None = None,
) -> list[Feedback]:
    """Return feedback rows matching filters and date range."""
    date_start = start or date.fromisoformat(filters["dateFrom"])
    date_end = end or date.fromisoformat(filters["dateTo"])
    statement = select(Feedback).where(Feedback.feedback_date.between(date_start, date_end))

    if filters["product"] != "All products":
        statement = statement.where(Feedback.product == filters["product"])
    if filters["country"] != "All countries":
        statement = statement.where(Feedback.country == filters["country"])
    if filters["region"] != "All regions":
        statement = statement.where(Feedback.region == filters["region"])

    return list(session.scalars(statement.order_by(Feedback.feedback_date.asc(), Feedback.id.asc())))
