from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.goal import Goal
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalMonthlyPlan, GoalProgress, GoalRead

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = Goal(
        name=goal_data.name,
        target_amount=goal_data.target_amount,
        current_amount=goal_data.current_amount,
        target_date=goal_data.target_date,
        user_id=current_user.id,
    )

    db.add(goal)
    db.commit()
    db.refresh(goal)

    return goal


@router.get("", response_model=list[GoalRead])
def list_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(Goal)
        .where(Goal.user_id == current_user.id)
        .order_by(Goal.target_date)
    ).all()


@router.get("/{goal_id}", response_model=GoalRead)
def get_goal(
    goal_id: int,
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

    return goal


@router.put("/{goal_id}", response_model=GoalRead)
def update_goal(
    goal_id: int,
    goal_data: GoalCreate,
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

    goal.name = goal_data.name
    goal.target_amount = goal_data.target_amount
    goal.current_amount = goal_data.current_amount
    goal.target_date = goal_data.target_date

    db.commit()
    db.refresh(goal)

    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
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

    db.delete(goal)
    db.commit()


@router.get("/{goal_id}/progress", response_model=GoalProgress)
def get_goal_progress(
    goal_id: int,
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

    today = date.today()
    remaining_amount = goal.target_amount - goal.current_amount

    if remaining_amount < 0:
        remaining_amount = Decimal("0.00")

    progress_percent = (goal.current_amount / goal.target_amount) * 100

    months_remaining = (
        (goal.target_date.year - today.year) * 12
        + goal.target_date.month
        - today.month
    )

    if goal.target_date.day > today.day:
        months_remaining += 1

    if months_remaining < 1:
        months_remaining = 1

    required_monthly_saving = remaining_amount / months_remaining

    return GoalProgress(
        goal_id=goal.id,
        goal_name=goal.name,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        remaining_amount=remaining_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        progress_percent=progress_percent.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        months_remaining=months_remaining,
        required_monthly_saving=required_monthly_saving.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
    )


@router.get("/{goal_id}/monthly-plan", response_model=GoalMonthlyPlan)
def get_goal_monthly_plan(
    goal_id: int,
    year: int,
    month: int,
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

    is_on_track = monthly_balance >= required_monthly_saving

    if is_on_track:
        adjustment_needed = Decimal("0.00")
        message = (
            "Voce esta no caminho certo para atingir esse objetivo "
            "com base no saldo deste mes."
        )
    else:
        adjustment_needed = required_monthly_saving - monthly_balance
        message = (
            "Voce precisa ajustar seus gastos ou aumentar sua renda "
            f"em R$ {adjustment_needed:.2f} neste mes para manter esse objetivo."
        )

    return GoalMonthlyPlan(
        goal_id=goal.id,
        goal_name=goal.name,
        year=year,
        month=month,
        monthly_balance=monthly_balance,
        required_monthly_saving=required_monthly_saving,
        is_on_track=is_on_track,
        adjustment_needed=adjustment_needed,
        message=message,
    )


def calculate_monthly_balance(
    year: int,
    month: int,
    db: Session,
    user_id: int,
) -> Decimal:
    start_date = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date(year, month, last_day)

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

    if remaining_amount < 0:
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