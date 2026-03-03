"""Dashboard builders for sales and feedback analytics."""

import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import CampaignProduct, Feedback, Sale
from app.reference import COUNTRY_REFERENCE, REGION_HUBS, STOPWORDS, TOPIC_KEYWORDS
from app.services.aggregation import (
    aggregate_feedback_period,
    aggregate_sales_period,
    percentage_delta,
    week_bucket,
)
from app.services.filters import build_filter_options
from app.services.repositories import get_feedback_rows, get_sale_rows
from app.services.serializers import serialize_feedback


def extract_topics(feedback_rows: list[Feedback]) -> list[dict[str, object]]:
    """Extract topic signals from feedback comments."""
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


def build_sales_dashboard(session: Session, filters: dict[str, str]) -> dict[str, object]:
    """Build sales dashboard payload."""
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


def build_feedback_dashboard(session: Session, filters: dict[str, str]) -> dict[str, object]:
    """Build feedback dashboard payload."""
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
