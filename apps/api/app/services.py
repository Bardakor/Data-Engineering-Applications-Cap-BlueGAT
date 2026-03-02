import csv
import io
import random
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

import numpy as np
from openai import OpenAI
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.core.config import settings
from app.models import CampaignProduct, Feedback, Sale
from app.reference import (
    CAMPAIGN_PRODUCT_MAP,
    COUNTRY_REFERENCE,
    DEFAULT_DATE_FROM,
    DEFAULT_DATE_TO,
    NEGATIVE_FRAGMENTS,
    NEUTRAL_FRAGMENTS,
    POSITIVE_FRAGMENTS,
    PRODUCT_PRICES,
    REGION_HUBS,
    STOPWORDS,
    TOPIC_KEYWORDS,
)
from app.schemas import FeedbackPayload

sentiment_analyzer = SentimentIntensityAnalyzer()


def get_openai_client() -> OpenAI | None:
    if not settings.openai_api_key:
        return None

    return OpenAI(api_key=settings.openai_api_key)


def normalize_filters(
    product: str | None,
    country: str | None,
    region: str | None,
    date_from: str | None,
    date_to: str | None,
) -> dict[str, str]:
    return {
        "product": product or "All products",
        "country": country or "All countries",
        "region": region or "All regions",
        "dateFrom": date_from or DEFAULT_DATE_FROM,
        "dateTo": date_to or DEFAULT_DATE_TO,
    }


def analyze_sentiment(comment: str) -> tuple[str, float]:
    score = sentiment_analyzer.polarity_scores(comment)["compound"]
    if score >= 0.25:
        return "positive", round(score, 4)
    if score <= -0.15:
        return "negative", round(score, 4)
    return "neutral", round(score, 4)


def build_filter_options(session: Session) -> dict[str, object]:
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


def get_sale_rows(session: Session, filters: dict[str, str], start: date | None = None, end: date | None = None) -> list[Sale]:
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


def aggregate_sales_period(rows: list[Sale]) -> dict[str, float]:
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
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


def week_bucket(day: date) -> str:
    monday = day - timedelta(days=day.weekday())
    return monday.isoformat()


def build_sales_dashboard(session: Session, filters: dict[str, str]) -> dict[str, object]:
    current_rows = get_sale_rows(session, filters)
    current_start = date.fromisoformat(filters["dateFrom"])
    current_end = date.fromisoformat(filters["dateTo"])
    period_days = max(1, (current_end - current_start).days + 1)
    previous_start = current_start - timedelta(days=period_days)
    previous_end = current_start - timedelta(days=1)
    previous_rows = get_sale_rows(session, filters, previous_start, previous_end)

    current = aggregate_sales_period(current_rows)
    previous = aggregate_sales_period(previous_rows)
    total_revenue = current["revenue"] or 1

    trend_map: dict[str, dict[str, float]] = defaultdict(lambda: {"revenue": 0.0, "orders": 0})
    region_map: dict[str, dict[str, float]] = defaultdict(
        lambda: {"revenue": 0.0, "orders": 0, "quantity": 0}
    )
    country_map: dict[str, dict[str, float]] = defaultdict(
        lambda: {"revenue": 0.0, "orders": 0}
    )
    product_map: dict[str, dict[str, float]] = defaultdict(
        lambda: {"revenue": 0.0, "units": 0}
    )
    previous_country_revenue: dict[str, float] = defaultdict(float)

    for row in previous_rows:
        previous_country_revenue[row.country] += row.total_amount

    for row in current_rows:
        trend_key = week_bucket(row.sale_date)
        trend_map[trend_key]["revenue"] += row.total_amount
        trend_map[trend_key]["orders"] += 1

        region_map[row.region]["revenue"] += row.total_amount
        region_map[row.region]["orders"] += 1
        region_map[row.region]["quantity"] += row.quantity

        country_map[row.country]["revenue"] += row.total_amount
        country_map[row.country]["orders"] += 1

        product_map[row.product]["revenue"] += row.total_amount
        product_map[row.product]["units"] += row.quantity

    region_performance = []
    for region, values in sorted(region_map.items(), key=lambda item: item[1]["revenue"], reverse=True):
        orders = values["orders"] or 1
        region_performance.append(
            {
                "region": region,
                "revenue": round(values["revenue"], 2),
                "orders": int(values["orders"]),
                "avgOrderValue": round(values["revenue"] / orders, 2),
                "share": round(values["revenue"] / total_revenue, 4),
            }
        )

    country_performance = []
    for country, values in sorted(country_map.items(), key=lambda item: item[1]["revenue"], reverse=True):
        previous_revenue = previous_country_revenue.get(country, 0.0)
        reference = COUNTRY_REFERENCE.get(country, {"region": "Unknown", "lat": 0.0, "lng": 0.0})
        country_performance.append(
            {
                "country": country,
                "region": reference["region"],
                "revenue": round(values["revenue"], 2),
                "orders": int(values["orders"]),
                "growth": percentage_delta(values["revenue"], previous_revenue),
                "lat": reference["lat"],
                "lng": reference["lng"],
            }
        )

    product_mix = []
    for product, values in sorted(product_map.items(), key=lambda item: item[1]["revenue"], reverse=True):
        product_mix.append(
            {
                "product": product,
                "revenue": round(values["revenue"], 2),
                "units": int(values["units"]),
                "share": round(values["revenue"] / total_revenue, 4),
            }
        )

    map_connections = []
    for row in country_performance:
        hub = REGION_HUBS.get(row["region"])
        if not hub:
            continue
        map_connections.append(
            {
                "start": hub,
                "end": {
                    "lat": row["lat"],
                    "lng": row["lng"],
                    "label": row["country"],
                },
                "revenue": row["revenue"],
                "orders": row["orders"],
                "share": round(row["revenue"] / total_revenue, 4),
            }
        )

    strongest_region = region_performance[0]["region"] if region_performance else "No region"
    fastest_country = country_performance[0]["country"] if country_performance else "No market"
    top_product = product_mix[0]["product"] if product_mix else "No product"

    return {
        "generatedAt": datetime.utcnow().isoformat(),
        "filters": build_filter_options(session),
        "appliedFilters": filters,
        "heroMetrics": [
            {
                "label": "Revenue",
                "value": round(current["revenue"], 2),
                "delta": percentage_delta(current["revenue"], previous["revenue"]),
                "format": "currency",
                "caption": "vs previous matched period",
            },
            {
                "label": "Units moved",
                "value": int(current["units"]),
                "delta": percentage_delta(current["units"], previous["units"]),
                "format": "number",
                "caption": "transaction volume across all markets",
            },
            {
                "label": "Avg order value",
                "value": round(current["avg_order"], 2),
                "delta": percentage_delta(current["avg_order"], previous["avg_order"]),
                "format": "currency",
                "caption": "basket quality and cross-sell depth",
            },
            {
                "label": "Top region share",
                "value": region_performance[0]["share"] if region_performance else 0,
                "delta": percentage_delta(
                    region_performance[0]["share"] if region_performance else 0,
                    0.0,
                ),
                "format": "percent",
                "caption": "concentration of revenue in the lead region",
            },
        ],
        "mapConnections": map_connections,
        "revenueTrend": [
            {
                "date": bucket,
                "revenue": round(values["revenue"], 2),
                "orders": int(values["orders"]),
            }
            for bucket, values in sorted(trend_map.items())
        ],
        "regionPerformance": region_performance,
        "countryPerformance": country_performance,
        "productMix": product_mix,
        "spotlights": [
            f"{strongest_region} leads the network and remains the revenue anchor in the selected window.",
            f"{fastest_country} is currently the strongest visible market in the filtered dataset.",
            f"{top_product} is the top product by revenue and should stay central in the commercial narrative.",
        ],
    }


def extract_topics(feedback_rows: list[Feedback]) -> list[dict[str, object]]:
    counter: Counter[str] = Counter()
    sentiment_scores: dict[str, list[float]] = defaultdict(list)

    for row in feedback_rows:
        words = re.findall(r"[a-zA-Z']+", row.comment.lower())
        for word in words:
            if word in STOPWORDS or len(word) < 4:
                continue
            if word in TOPIC_KEYWORDS or word.startswith("promo"):
                counter[word] += 1
                sentiment_scores[word].append(row.sentiment_score)

    topics = []
    for topic, count in counter.most_common(8):
        avg_sentiment = sum(sentiment_scores[topic]) / len(sentiment_scores[topic])
        if avg_sentiment >= 0.25:
            tone = "positive"
        elif avg_sentiment <= -0.15:
            tone = "negative"
        else:
            tone = "neutral"
        topics.append({"topic": topic, "count": count, "tone": tone})
    return topics


def build_feedback_dashboard(session: Session, filters: dict[str, str]) -> dict[str, object]:
    current_rows = get_feedback_rows(session, filters)
    current_start = date.fromisoformat(filters["dateFrom"])
    current_end = date.fromisoformat(filters["dateTo"])
    period_days = max(1, (current_end - current_start).days + 1)
    previous_start = current_start - timedelta(days=period_days)
    previous_end = current_start - timedelta(days=1)
    previous_rows = get_feedback_rows(session, filters, previous_start, previous_end)

    current = aggregate_feedback_period(current_rows)
    previous = aggregate_feedback_period(previous_rows)

    sentiment_trend: dict[str, dict[str, int]] = defaultdict(
        lambda: {"positive": 0, "neutral": 0, "negative": 0}
    )
    campaign_map: dict[str, dict[str, object]] = defaultdict(
        lambda: {"feedbackCount": 0, "sentimentTotal": 0.0, "countries": set()}
    )
    country_map: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "feedbackCount": 0,
            "positiveCount": 0,
            "negativeCount": 0,
            "sentimentTotal": 0.0,
        }
    )

    for row in current_rows:
        bucket = week_bucket(row.feedback_date)
        sentiment_trend[bucket][row.sentiment_label] += 1

        campaign_map[row.campaign_id]["feedbackCount"] += 1
        campaign_map[row.campaign_id]["sentimentTotal"] += row.sentiment_score
        if row.country:
            campaign_map[row.campaign_id]["countries"].add(row.country)
            country_map[row.country]["feedbackCount"] += 1
            country_map[row.country]["sentimentTotal"] += row.sentiment_score
            if row.sentiment_label == "positive":
                country_map[row.country]["positiveCount"] += 1
            if row.sentiment_label == "negative":
                country_map[row.country]["negativeCount"] += 1

    revenue_by_product = defaultdict(float)
    for sale in get_sale_rows(session, filters):
        revenue_by_product[sale.product] += sale.total_amount

    campaign_impact = []
    for campaign_id, values in sorted(
        campaign_map.items(),
        key=lambda item: item[1]["feedbackCount"],
        reverse=True,
    ):
        product = session.get(CampaignProduct, campaign_id)
        product_name = product.product if product else "Unknown"
        avg_sentiment = values["sentimentTotal"] / max(values["feedbackCount"], 1)
        countries = ", ".join(sorted(values["countries"])[:2]) or "multiple markets"
        campaign_impact.append(
            {
                "campaignId": campaign_id,
                "product": product_name,
                "feedbackCount": int(values["feedbackCount"]),
                "avgSentiment": round(avg_sentiment, 4),
                "linkedRevenue": round(revenue_by_product.get(product_name, 0.0), 2),
                "headline": (
                    f"{product_name} is drawing attention in {countries}; "
                    f"sentiment is {'strong' if avg_sentiment >= 0.25 else 'mixed'}."
                ),
            }
        )

    sentiment_by_country = []
    for country, values in sorted(
        country_map.items(),
        key=lambda item: item[1]["feedbackCount"],
        reverse=True,
    ):
        reference = COUNTRY_REFERENCE.get(country, {"region": "Unknown", "lat": 0.0, "lng": 0.0})
        feedback_count = values["feedbackCount"] or 1
        avg_sentiment = values["sentimentTotal"] / feedback_count
        positive_share = values["positiveCount"] / feedback_count
        negative_share = values["negativeCount"] / feedback_count
        sentiment_by_country.append(
            {
                "country": country,
                "region": reference["region"],
                "feedbackCount": int(values["feedbackCount"]),
                "avgSentiment": round(avg_sentiment, 4),
                "positiveShare": round(positive_share, 4),
                "negativeShare": round(negative_share, 4),
                "lat": reference["lat"],
                "lng": reference["lng"],
            }
        )

    map_connections = []
    total_feedback = len(current_rows) or 1
    for row in sentiment_by_country:
        hub = REGION_HUBS.get(row["region"])
        if not hub:
            continue
        map_connections.append(
            {
                "start": hub,
                "end": {
                    "lat": row["lat"],
                    "lng": row["lng"],
                    "label": row["country"],
                },
                "revenue": row["feedbackCount"],
                "orders": row["feedbackCount"],
                "share": round(row["feedbackCount"] / total_feedback, 4),
                "sentiment": row["avgSentiment"],
            }
        )

    recent_feedback = [
        serialize_feedback(row)
        for row in sorted(current_rows, key=lambda row: (row.feedback_date, row.id), reverse=True)[:8]
    ]

    top_country = sentiment_by_country[0]["country"] if sentiment_by_country else "No country"
    top_campaign = campaign_impact[0]["campaignId"] if campaign_impact else "No campaign"

    return {
        "generatedAt": datetime.utcnow().isoformat(),
        "filters": build_filter_options(session),
        "appliedFilters": filters,
        "heroMetrics": [
            {
                "label": "Feedback volume",
                "value": current["total"],
                "delta": percentage_delta(current["total"], previous["total"]),
                "format": "number",
                "caption": "comments received in the selected window",
            },
            {
                "label": "Positive sentiment",
                "value": round(current["positive_share"], 4),
                "delta": percentage_delta(current["positive_share"], previous["positive_share"]),
                "format": "percent",
                "caption": "share of positive feedback",
            },
            {
                "label": "Negative sentiment",
                "value": round(current["negative_share"], 4),
                "delta": percentage_delta(current["negative_share"], previous["negative_share"]),
                "format": "percent",
                "caption": "share of negative feedback",
            },
            {
                "label": "Revenue linked",
                "value": round(sum(revenue_by_product.values()), 2),
                "delta": percentage_delta(sum(revenue_by_product.values()), 0.0),
                "format": "currency",
                "caption": "sales attached to promoted products",
            },
        ],
        "sentimentTrend": [
            {
                "date": bucket,
                "positive": values["positive"],
                "neutral": values["neutral"],
                "negative": values["negative"],
            }
            for bucket, values in sorted(sentiment_trend.items())
        ],
        "campaignImpact": campaign_impact[:6],
        "topicSignals": extract_topics(current_rows),
        "recentFeedback": recent_feedback,
        "sentimentByCountry": sentiment_by_country,
        "mapConnections": map_connections,
        "briefs": [
            f"{top_campaign} is the most discussed campaign in the filtered dataset.",
            f"{top_country} is the country with the densest feedback signal right now.",
            "Operational complaints still cluster around stockouts, checkout clarity, and queue time.",
        ],
    }


def serialize_sale(row: Sale) -> dict[str, object]:
    return {
        "id": row.id,
        "username": row.username,
        "saleDate": row.sale_date.isoformat(),
        "country": row.country,
        "region": row.region,
        "product": row.product,
        "quantity": row.quantity,
        "unitPrice": round(row.unit_price, 2),
        "totalAmount": round(row.total_amount, 2),
    }


def serialize_feedback(row: Feedback) -> dict[str, object]:
    return {
        "id": row.id,
        "username": row.username,
        "feedbackDate": row.feedback_date.isoformat(),
        "campaignId": row.campaign_id,
        "product": row.product or "Unknown",
        "country": row.country or "Unknown",
        "region": row.region or "Unknown",
        "sentimentLabel": row.sentiment_label,
        "sentimentScore": round(row.sentiment_score, 4),
        "comment": row.comment,
    }


def serialize_campaign(row: CampaignProduct) -> dict[str, object]:
    return {
        "campaignId": row.campaign_id,
        "product": row.product,
    }


def build_data_preview(session: Session) -> dict[str, object]:
    sales = session.scalars(select(Sale).order_by(Sale.sale_date.desc(), Sale.id.desc()).limit(40)).all()
    feedback = session.scalars(
        select(Feedback).order_by(Feedback.feedback_date.desc(), Feedback.id.desc()).limit(40)
    ).all()
    campaigns = session.scalars(select(CampaignProduct).order_by(CampaignProduct.campaign_id.asc())).all()

    return {
        "sales": [serialize_sale(row) for row in sales],
        "feedback": [serialize_feedback(row) for row in feedback],
        "campaigns": [serialize_campaign(row) for row in campaigns],
    }


def enrich_feedback_context(session: Session, username: str, campaign_id: str) -> tuple[str | None, str | None, str | None]:
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


def build_feedback_document(row: Feedback) -> str:
    return (
        f"Campaign {row.campaign_id} for {row.product or 'Unknown product'} in "
        f"{row.country or 'Unknown country'} on {row.feedback_date.isoformat()}. "
        f"Sentiment {row.sentiment_label} ({row.sentiment_score}). Comment: {row.comment}"
    )


def cosine_similarity(query_vector: list[float], candidate_vector: list[float]) -> float:
    query = np.array(query_vector)
    candidate = np.array(candidate_vector)
    denominator = np.linalg.norm(query) * np.linalg.norm(candidate)
    if denominator == 0:
        return 0.0
    return float(np.dot(query, candidate) / denominator)


def ensure_feedback_embeddings(session: Session, feedback_rows: list[Feedback], client: OpenAI) -> None:
    missing = [row for row in feedback_rows if not row.embedding]
    if not missing:
        return

    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=[build_feedback_document(row) for row in missing],
    )

    for row, embedding_row in zip(missing, response.data, strict=True):
        row.embedding = embedding_row.embedding

    session.commit()


def lexical_score(query: str, row: Feedback) -> float:
    query_terms = set(re.findall(r"[a-zA-Z']+", query.lower()))
    document_terms = set(re.findall(r"[a-zA-Z']+", build_feedback_document(row).lower()))
    overlap = len(query_terms & document_terms)
    if overlap == 0:
        return 0.0
    return overlap / np.sqrt(len(document_terms))


def answer_without_openai(query: str, citations: list[dict[str, object]]) -> str:
    if not citations:
        return "No relevant feedback matched that query in the current filtered dataset."

    by_campaign = Counter(citation["campaignId"] for citation in citations)
    by_country = Counter(citation["country"] for citation in citations)
    by_sentiment = Counter(citation["sentimentLabel"] for citation in citations)

    top_campaign = by_campaign.most_common(1)[0][0]
    top_country = by_country.most_common(1)[0][0]
    top_sentiment = by_sentiment.most_common(1)[0][0]
    examples = "; ".join(citation["comment"] for citation in citations[:2])

    return (
        f"From the retrieved feedback, the main signal is {top_sentiment} sentiment centered on "
        f"{top_campaign} and concentrated in {top_country}. The strongest supporting examples are: {examples}"
    )


def run_feedback_rag(session: Session, query: str, filters: dict[str, str]) -> dict[str, object]:
    feedback_rows = get_feedback_rows(session, filters)
    if not feedback_rows:
        return {
            "answer": "No feedback is available for the selected filters.",
            "retrievalMode": "empty",
            "citations": [],
        }

    client = get_openai_client()
    scored_rows: list[tuple[float, Feedback]] = []

    if client:
        ensure_feedback_embeddings(session, feedback_rows, client)
        query_embedding = client.embeddings.create(
            model=settings.openai_embedding_model,
            input=query,
        ).data[0].embedding
        scored_rows = [
            (cosine_similarity(query_embedding, row.embedding or []), row)
            for row in feedback_rows
        ]
        retrieval_mode = "openai"
    else:
        scored_rows = [(lexical_score(query, row), row) for row in feedback_rows]
        retrieval_mode = "lexical"

    score_by_feedback_id = {row.id: score for score, row in scored_rows}
    top_rows = [row for score, row in sorted(scored_rows, key=lambda item: item[0], reverse=True)[:5] if score > 0]
    citations = [
        {
            "feedbackId": row.id,
            "campaignId": row.campaign_id,
            "product": row.product or "Unknown",
            "country": row.country or "Unknown",
            "feedbackDate": row.feedback_date.isoformat(),
            "sentimentLabel": row.sentiment_label,
            "score": round(score_by_feedback_id.get(row.id, 0.0), 4),
            "comment": row.comment,
        }
        for row in top_rows
    ]

    if client and citations:
        context = "\n\n".join(
            f"[{index + 1}] {build_feedback_document(row)}"
            for index, row in enumerate(top_rows)
        )
        response = client.responses.create(
            model=settings.openai_rag_model,
            input=(
                "You are a retail analytics assistant. Answer only from the supplied feedback snippets. "
                "Be concise, mention the dominant themes, and do not invent facts.\n\n"
                f"User question: {query}\n\n"
                f"Evidence:\n{context}"
            ),
        )
        answer = response.output_text
    else:
        answer = answer_without_openai(query, citations)

    return {
        "answer": answer,
        "retrievalMode": retrieval_mode,
        "citations": citations,
    }


def seed_database(session: Session) -> dict[str, int]:
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
