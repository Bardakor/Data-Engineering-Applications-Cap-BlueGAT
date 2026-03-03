"""Data ingestion: feedback, sales CSV, campaign mapping CSV."""

import csv
import io
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CampaignProduct, Feedback, Sale
from app.reference import COUNTRY_REFERENCE
from app.schemas import FeedbackPayload
from app.services.sentiment import analyze_sentiment


def enrich_feedback_context(
    session: Session, username: str, campaign_id: str
) -> tuple[str | None, str | None, str | None]:
    """Resolve product, country, region from sales for a feedback record."""
    product_row = session.get(CampaignProduct, campaign_id)
    product = product_row.product if product_row else None

    sale_statement = select(Sale).where(Sale.username == username)
    if product:
        sale_statement = sale_statement.where(Sale.product == product)

    sale = session.scalar(sale_statement.order_by(Sale.sale_date.desc(), Sale.id.desc()))
    if sale:
        return product, sale.country, sale.region

    return product, None, None


def ingest_feedback_payloads(session: Session, payloads: list[FeedbackPayload]) -> dict[str, int]:
    """Insert feedback records from payloads."""
    inserted = 0
    for payload in payloads:
        product, country, region = enrich_feedback_context(
            session,
            payload.username,
            payload.campaign_id,
        )
        sentiment_label, sentiment_score = analyze_sentiment(payload.comment)
        session.add(
            Feedback(
                username=payload.username,
                feedback_date=payload.feedback_date,
                campaign_id=payload.campaign_id,
                product=product,
                country=country,
                region=region,
                comment=payload.comment,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score,
            )
        )
        inserted += 1

    session.commit()
    return {"inserted": inserted}


def ingest_sales_csv(session: Session, content: bytes) -> dict[str, int]:
    """Insert sales from CSV content."""
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    inserted = 0
    for row in reader:
        country = row["country"]
        reference = COUNTRY_REFERENCE.get(country)
        region = reference["region"] if reference else "Unknown"
        session.add(
            Sale(
                username=row["username"],
                sale_date=date.fromisoformat(row["sale_date"]),
                country=country,
                region=region,
                product=row["product"],
                quantity=int(row["quantity"]),
                unit_price=float(row["unit_price"]),
                total_amount=float(row["total_amount"]),
            )
        )
        inserted += 1

    session.commit()
    return {"inserted": inserted}


def ingest_campaign_csv(session: Session, content: bytes) -> dict[str, int]:
    """Insert or update campaign-product mappings from CSV."""
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    inserted = 0
    for row in reader:
        existing = session.get(CampaignProduct, row["campaign_id"])
        if existing:
            existing.product = row["product"]
        else:
            session.add(CampaignProduct(campaign_id=row["campaign_id"], product=row["product"]))
            inserted += 1

    session.commit()
    return {"inserted": inserted}
