from decimal import Decimal

from pydantic import BaseModel


class LeisureRecommendation(BaseModel):
    leisure_place_id: int
    name: str
    city: str
    category: str
    average_price: Decimal
    is_partner: bool
    event_url: str | None
    affiliate_url: str | None
    reason: str


class LeisureRecommendationResponse(BaseModel):
    city: str
    available_budget: Decimal
    recommendations: list[LeisureRecommendation]

class MonthlyLeisureRecommendationResponse(BaseModel):
    city: str
    year: int
    month: int
    desired_saving: Decimal
    available_for_leisure: Decimal
    recommendations: list[LeisureRecommendation]