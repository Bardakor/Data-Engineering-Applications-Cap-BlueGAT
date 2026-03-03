"""Database seeding for demo data."""

import random
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CampaignProduct, Feedback, Sale
from app.reference import (
    CAMPAIGN_PRODUCT_MAP,
    COUNTRY_REFERENCE,
    NEGATIVE_FRAGMENTS,
    NEUTRAL_FRAGMENTS,
    POSITIVE_FRAGMENTS,
    PRODUCT_PRICES,
)
from app.services.sentiment import analyze_sentiment


def seed_database(session: Session) -> dict[str, int]:
    """Seed demo data if database is empty."""
    existing_sales = session.scalar(select(func.count(Sale.id))) or 0
    if existing_sales > 0:
        return {
            "sales": existing_sales,
            "feedback": session.scalar(select(func.count(Feedback.id))) or 0,
            "campaigns": session.scalar(select(func.count(CampaignProduct.campaign_id))) or 0,
        }

    rng = random.Random(42)
    users = [f"user{index:03d}" for index in range(1, 361)]
    countries = list(COUNTRY_REFERENCE.keys())
    country_weights = [11, 9, 10, 8, 7, 8, 6, 5, 4, 4]
    products = list(PRODUCT_PRICES.keys())
    product_weights = [14, 11, 8, 10, 7]
    current_day = date.today() - timedelta(days=220)

    for campaign_id, product in CAMPAIGN_PRODUCT_MAP.items():
        session.add(CampaignProduct(campaign_id=campaign_id, product=product))

    sales_created = 0
    for offset in range(220):
        current_date = current_day + timedelta(days=offset)
        for _ in range(rng.randint(4, 10)):
            user = rng.choice(users)
            country = rng.choices(countries, weights=country_weights, k=1)[0]
            product = rng.choices(products, weights=product_weights, k=1)[0]
            reference = COUNTRY_REFERENCE[country]
            quantity = rng.randint(1, 5)
            base_price = PRODUCT_PRICES[product]
            unit_price = round(base_price * rng.uniform(0.92, 1.12), 2)
            total_amount = round(quantity * unit_price, 2)
            session.add(
                Sale(
                    username=user,
                    sale_date=current_date,
                    country=country,
                    region=reference["region"],
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_amount=total_amount,
                )
            )
            sales_created += 1

    session.flush()

    feedback_created = 0
    sales_rows = session.scalars(select(Sale).order_by(Sale.sale_date.asc())).all()
    campaign_by_product = defaultdict(list)
    for campaign_id, product in CAMPAIGN_PRODUCT_MAP.items():
        campaign_by_product[product].append(campaign_id)

    for row in rng.sample(sales_rows, k=min(320, len(sales_rows))):
        sentiment_bucket = rng.choices(
            ["positive", "neutral", "negative"],
            weights=[0.58, 0.22, 0.20],
            k=1,
        )[0]
        if sentiment_bucket == "positive":
            fragment = rng.choice(POSITIVE_FRAGMENTS)
        elif sentiment_bucket == "negative":
            fragment = rng.choice(NEGATIVE_FRAGMENTS)
        else:
            fragment = rng.choice(NEUTRAL_FRAGMENTS)

        comment = f"{row.product}: {fragment}"
        sentiment_label, sentiment_score = analyze_sentiment(comment)
        session.add(
            Feedback(
                username=row.username,
                feedback_date=row.sale_date + timedelta(days=rng.randint(0, 5)),
                campaign_id=rng.choice(campaign_by_product[row.product]),
                product=row.product,
                country=row.country,
                region=row.region,
                comment=comment,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score,
            )
        )
        feedback_created += 1

    session.commit()
    return {
        "sales": sales_created,
        "feedback": feedback_created,
        "campaigns": len(CAMPAIGN_PRODUCT_MAP),
    }
