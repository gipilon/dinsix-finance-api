from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.budget import LeisureBudget

router = APIRouter(prefix="/budget", tags=["budget"])


@router.get("/leisure", response_model=LeisureBudget)
def get_leisure_budget(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    desired_saving: Decimal = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_date = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    total_income = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == current_user.id,
            Transaction.type == TransactionType.INCOME,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
    )

    total_expense = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == current_user.id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
    )

    total_income = Decimal(total_income)
    total_expense = Decimal(total_expense)

    available_for_leisure = total_income - total_expense - desired_saving

    if available_for_leisure < 0:
        available_for_leisure = Decimal("0.00")

    return LeisureBudget(
        year=year,
        month=month,
        total_income=total_income,
        total_expense=total_expense,
        desired_saving=desired_saving,
        available_for_leisure=available_for_leisure,
    )