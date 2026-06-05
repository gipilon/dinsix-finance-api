from decimal import Decimal

from pydantic import BaseModel


class CategorySummary(BaseModel):
    category_id: int
    category_name: str
    total: Decimal


class MonthlySummary(BaseModel):
    year: int
    month: int
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    expenses_by_category: list[CategorySummary]