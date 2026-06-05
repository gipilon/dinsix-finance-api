from decimal import Decimal

from pydantic import BaseModel


class LeisureBudget(BaseModel):
    year: int
    month: int
    total_income: Decimal
    total_expense: Decimal
    desired_saving: Decimal
    available_for_leisure: Decimal