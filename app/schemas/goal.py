from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GoalBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    target_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    current_amount: Decimal = Field(default=0, ge=0, max_digits=12, decimal_places=2)
    target_date: date


class GoalCreate(GoalBase):
    pass


class GoalRead(GoalBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class GoalProgress(BaseModel):
    goal_id: int
    goal_name: str
    target_amount: Decimal
    current_amount: Decimal
    remaining_amount: Decimal
    progress_percent: Decimal
    months_remaining: int
    required_monthly_saving: Decimal

class GoalMonthlyPlan(BaseModel):
    goal_id: int
    goal_name: str
    year: int
    month: int
    monthly_balance: Decimal
    required_monthly_saving: Decimal
    is_on_track: bool
    adjustment_needed: Decimal
    message: str