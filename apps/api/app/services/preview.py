"""Data preview for UI sample display."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CampaignProduct, Feedback, Sale
from app.services.serializers import serialize_campaign, serialize_feedback, serialize_sale


def build_data_preview(session: Session) -> dict[str, object]:
    """Return sample sales, feedback, and campaigns for preview."""
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
