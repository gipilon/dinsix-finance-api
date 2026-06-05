from decimal import Decimal

from pydantic import BaseModel


class CategoryAdjustmentSuggestion(BaseModel):
    category_id: int
    category_name: str
    current_spending: Decimal
    suggested_reduction: Decimal


class MonthlyAdjustmentInsight(BaseModel):
    goal_id: int
    goal_name: str
    year: int
    month: int
    monthly_balance: Decimal
    required_monthly_saving: Decimal
    adjustment_needed: Decimal
    is_on_track: bool
    message: str
    suggestions: list[CategoryAdjustmentSuggestion]