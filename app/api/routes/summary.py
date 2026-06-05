from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.schemas.summary import CategorySummary, MonthlySummary

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/monthly", response_model=MonthlySummary)
def get_monthly_summary(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
):
    start_date = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    total_income = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.type == TransactionType.INCOME,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
    )

    total_expense = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
    )

    expenses_by_category_rows = db.execute(
        select(
            Category.id,
            Category.name,
            func.coalesce(func.sum(Transaction.amount), 0),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    ).all()

    expenses_by_category = [
        CategorySummary(
            category_id=row[0],
            category_name=row[1],
            total=row[2],
        )
        for row in expenses_by_category_rows
    ]

    total_income = Decimal(total_income)
    total_expense = Decimal(total_expense)

    return MonthlySummary(
        year=year,
        month=month,
        total_income=total_income,
        total_expense=total_expense,
        balance=total_income - total_expense,
        expenses_by_category=expenses_by_category,
    )