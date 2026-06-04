from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TransactionType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionBase(BaseModel):
    description: str = Field(min_length=2, max_length=120)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    type: TransactionType
    transaction_date: date
    category_id: int = Field(gt=0)


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)