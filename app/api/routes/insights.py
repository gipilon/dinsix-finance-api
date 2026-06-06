from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.category import Category
from app.models.goal import Goal
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.insight import CategoryAdjustmentSuggestion, MonthlyAdjustmentInsight

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/monthly-adjustments", response_model=MonthlyAdjustmentInsight)
def get_monthly_adjustments(
    goal_id: int,
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = db.scalar(
        select(Goal).where(
            Goal.id == goal_id,
            Goal.user_id == current_user.id,
        )
    )

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objetivo nao encontrado",
        )

    monthly_balance = calculate_monthly_balance(
        year=year,
        month=month,
        db=db,
        user_id=current_user.id,
    )
    required_monthly_saving = calculate_required_monthly_saving(goal)

    adjustment_needed = required_monthly_saving - monthly_balance

    if adjustment_needed <= 0:
        return MonthlyAdjustmentInsight(
            goal_id=goal.id,
            goal_name=goal.name,
            year=year,
            month=month,
            monthly_balance=round_money(monthly_balance),
            required_monthly_saving=round_money(required_monthly_saving),
            adjustment_needed=Decimal("0.00"),
            is_on_track=True,
            message="Voce esta no caminho certo para atingir esse objetivo.",
            suggestions=[],
        )

    suggestions = build_category_suggestions(
        year=year,
        month=month,
        adjustment_needed=adjustment_needed,
        db=db,
        user_id=current_user.id,
    )

    return MonthlyAdjustmentInsight(
        goal_id=goal.id,
        goal_name=goal.name,
        year=year,
        month=month,
        monthly_balance=round_money(monthly_balance),
        required_monthly_saving=round_money(required_monthly_saving),
        adjustment_needed=round_money(adjustment_needed),
        is_on_track=False,
        message=(
            f"Voce precisa ajustar R$ {round_money(adjustment_needed):.2f} "
            "para manter esse objetivo no ritmo esperado."
        ),
        suggestions=suggestions,
    )


def calculate_monthly_balance(
    year: int,
    month: int,
    db: Session,
    user_id: int,
) -> Decimal:
    start_date, end_date = get_month_period(year, month)

    total_income = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.INCOME,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
    )

    total_expense = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
    )

    return Decimal(total_income) - Decimal(total_expense)


def calculate_required_monthly_saving(goal: Goal) -> Decimal:
    today = date.today()
    remaining_amount = goal.target_amount - goal.current_amount

    if remaining_amount <= 0:
        return Decimal("0.00")

    months_remaining = (
        (goal.target_date.year - today.year) * 12
        + goal.target_date.month
        - today.month
    )

    if goal.target_date.day > today.day:
        months_remaining += 1

    if months_remaining < 1:
        months_remaining = 1

    return remaining_amount / months_remaining


def build_category_suggestions(
    year: int,
    month: int,
    adjustment_needed: Decimal,
    db: Session,
    user_id: int,
) -> list[CategoryAdjustmentSuggestion]:
    start_date, end_date = get_month_period(year, month)

    rows = db.execute(
        select(
            Category.id,
            Category.name,
            func.coalesce(func.sum(Transaction.amount), 0),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Category.user_id == user_id,
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(3)
    ).all()

    suggestions = []
    remaining_adjustment = adjustment_needed

    for category_id, category_name, current_spending in rows:
        current_spending = Decimal(current_spending)

        if remaining_adjustment <= 0:
            break

        suggested_reduction = min(
            current_spending * Decimal("0.20"),
            remaining_adjustment,
        )

        suggestions.append(
            CategoryAdjustmentSuggestion(
                category_id=category_id,
                category_name=category_name,
                current_spending=round_money(current_spending),
                suggested_reduction=round_money(suggested_reduction),
            )
        )

        remaining_adjustment -= suggested_reduction

    return suggestions


def get_month_period(year: int, month: int) -> tuple[date, date]:
    start_date = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    return start_date, end_date


def round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)