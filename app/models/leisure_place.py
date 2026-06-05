from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LeisurePlace(Base):
    __tablename__ = "leisure_places"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    average_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    event_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    affiliate_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_partner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)