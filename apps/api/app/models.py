from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    sale_date: Mapped[date] = mapped_column(Date, index=True)
    country: Mapped[str] = mapped_column(String(64), index=True)
    region: Mapped[str] = mapped_column(String(64), index=True)
    product: Mapped[str] = mapped_column(String(128), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    total_amount: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class CampaignProduct(Base):
    __tablename__ = "campaign_products"

    campaign_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    product: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    feedback_date: Mapped[date] = mapped_column(Date, index=True)
    campaign_id: Mapped[str] = mapped_column(String(32), index=True)
    product: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    comment: Mapped[str] = mapped_column(Text)
    sentiment_label: Mapped[str] = mapped_column(String(16), index=True)
    sentiment_score: Mapped[float] = mapped_column(Float)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
