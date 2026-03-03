"""Model-to-dict serialization for API responses."""

from app.models import CampaignProduct, Feedback, Sale


def serialize_sale(row: Sale) -> dict[str, object]:
    """Serialize Sale to API response dict."""
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
    """Serialize Feedback to API response dict."""
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
    """Serialize CampaignProduct to API response dict."""
    return {
        "campaignId": row.campaign_id,
        "product": row.product,
    }
