"""Aggregation helpers for dashboards."""

from datetime import date, timedelta

from app.models import Feedback, Sale


def aggregate_sales_period(rows: list[Sale]) -> dict[str, float]:
    """Aggregate revenue, units, orders for a list of sales."""
    revenue = sum(row.total_amount for row in rows)
    units = sum(row.quantity for row in rows)
    orders = len(rows)
    avg_order = revenue / orders if orders else 0.0
    return {
        "revenue": revenue,
        "units": units,
        "orders": orders,
        "avg_order": avg_order,
    }


def aggregate_feedback_period(rows: list[Feedback]) -> dict[str, float]:
    """Aggregate feedback counts and sentiment for a list of feedback."""
    total = len(rows)
    positive = sum(1 for row in rows if row.sentiment_label == "positive")
    negative = sum(1 for row in rows if row.sentiment_label == "negative")
    avg_sentiment = sum(row.sentiment_score for row in rows) / total if total else 0.0
    return {
        "total": total,
        "positive_share": positive / total if total else 0.0,
        "negative_share": negative / total if total else 0.0,
        "avg_sentiment": avg_sentiment,
    }


def percentage_delta(current: float, previous: float) -> float:
    """Return percentage change from previous to current."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


def week_bucket(day: date) -> str:
    """Return ISO date of the Monday for the week containing day."""
    monday = day - timedelta(days=day.weekday())
    return monday.isoformat()
