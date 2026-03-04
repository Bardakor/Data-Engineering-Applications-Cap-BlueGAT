"""Filter normalization and options."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Sale
from app.reference import DEFAULT_DATE_FROM, DEFAULT_DATE_TO


def _parse_date_or_default(value: str | None, default: str) -> str:
    """Return value if it's a valid ISO date, else default."""
    if not value:
        return default
    try:
        date.fromisoformat(value)
        return value
    except (ValueError, TypeError):
        return default


def normalize_filters(
    product: str | None,
    country: str | None,
    region: str | None,
    date_from: str | None,
    date_to: str | None,
) -> dict[str, str]:
    """Normalize query params into a filter dict."""
    return {
        "product": product or "All products",
        "country": country or "All countries",
        "region": region or "All regions",
        "dateFrom": _parse_date_or_default(date_from, DEFAULT_DATE_FROM),
        "dateTo": _parse_date_or_default(date_to, DEFAULT_DATE_TO),
    }


def build_filter_options(session: Session) -> dict[str, object]:
    """Build available filter options from database."""
    products = [
        row[0]
        for row in session.execute(select(Sale.product).distinct().order_by(Sale.product))
        if row[0]
    ]
    countries = [
        row[0]
        for row in session.execute(select(Sale.country).distinct().order_by(Sale.country))
        if row[0]
    ]
    regions = [
        row[0]
        for row in session.execute(select(Sale.region).distinct().order_by(Sale.region))
        if row[0]
    ]
    min_date = session.scalar(select(func.min(Sale.sale_date))) or date.fromisoformat(DEFAULT_DATE_FROM)
    max_date = session.scalar(select(func.max(Sale.sale_date))) or date.fromisoformat(DEFAULT_DATE_TO)

    return {
        "products": ["All products", *products],
        "countries": ["All countries", *countries],
        "regions": ["All regions", *regions],
        "minDate": min_date.isoformat(),
        "maxDate": max_date.isoformat(),
    }
