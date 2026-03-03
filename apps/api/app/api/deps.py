"""FastAPI dependencies."""

from fastapi import Query

from app.services.filters import normalize_filters


def resolve_filters(
    product: str | None = Query(default=None),
    country: str | None = Query(default=None),
    region: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
) -> dict[str, str]:
    """Normalize query params into filter dict."""
    return normalize_filters(product, country, region, date_from, date_to)
