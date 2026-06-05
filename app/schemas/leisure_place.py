from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LeisurePlaceBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=500)
    city: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=80)
    average_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    provider: str | None = Field(default=None, max_length=80)
    event_url: str | None = Field(default=None, max_length=500)
    affiliate_url: str | None = Field(default=None, max_length=500)
    is_partner: bool = False


class LeisurePlaceCreate(LeisurePlaceBase):
    pass


class LeisurePlaceRead(LeisurePlaceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)