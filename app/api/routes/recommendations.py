from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.leisure_place import LeisurePlace
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.recommendation import (
    LeisureRecommendation,
    LeisureRecommendationResponse,
    MonthlyLeisureRecommendationResponse,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/leisure", response_model=LeisureRecommendationResponse)
def recommend_leisure_places(
    city: str,
    available_budget: Decimal = Query(ge=0),
    db: Session = Depends(get_db),
):
    query = (
        select(LeisurePlace)
        .where(LeisurePlace.city.ilike(f"%{city}%"))
        .where(LeisurePlace.average_price <= available_budget)
        .order_by(LeisurePlace.is_partner.desc(), LeisurePlace.average_price)
        .limit(5)
    )

    leisure_places = db.scalars(query).all()

    recommendations = [
        LeisureRecommendation(
            leisure_place_id=place.id,
            name=place.name,
            city=place.city,
            category=place.category,
            average_price=place.average_price,
            is_partner=place.is_partner,
            event_url=place.event_url,
            affiliate_url=place.affiliate_url,
            reason=build_recommendation_reason(place, available_budget),
        )
        for place in leisure_places
    ]

    return LeisureRecommendationResponse(
        city=city,
        available_budget=available_budget,
        recommendations=recommendations,
    )


@router.get("/monthly-leisure", response_model=MonthlyLeisureRecommendationResponse)
def recommend_monthly_leisure_places(
    city: str,
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    desired_saving: Decimal = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    available_for_leisure = calculate_available_for_leisure(
        year=year,
        month=month,
        desired_saving=desired_saving,
        db=db,
        user_id=current_user.id,
    )

    query = (
        select(LeisurePlace)
        .where(LeisurePlace.city.ilike(f"%{city}%"))
        .where(LeisurePlace.average_price <= available_for_leisure)
        .order_by(LeisurePlace.is_partner.desc(), LeisurePlace.average_price)
        .limit(5)
    )

    leisure_places = db.scalars(query).all()

    recommendations = [
        LeisureRecommendation(
            leisure_place_id=place.id,
            name=place.name,
            city=place.city,
            category=place.category,
            average_price=place.average_price,
            is_partner=place.is_partner,
            event_url=place.event_url,
            affiliate_url=place.affiliate_url,
            reason=build_recommendation_reason(place, available_for_leisure),
        )
        for place in leisure_places
    ]

    return MonthlyLeisureRecommendationResponse(
        city=city,
        year=year,
        month=month,
        desired_saving=desired_saving,
        available_for_leisure=available_for_leisure,
        recommendations=recommendations,
    )


def calculate_available_for_leisure(
    year: int,
    month: int,
    desired_saving: Decimal,
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

    available_for_leisure = Decimal(total_income) - Decimal(total_expense) - desired_saving

    if available_for_leisure < 0:
        return Decimal("0.00")

    return available_for_leisure


def build_recommendation_reason(
    leisure_place: LeisurePlace,
    available_budget: Decimal,
) -> str:
    remaining_budget = available_budget - leisure_place.average_price

    if leisure_place.is_partner and leisure_place.affiliate_url:
        return (
            f"Cabe no seu orcamento e possui parceria. "
            f"Depois dessa escolha, ainda sobram R$ {remaining_budget:.2f}."
        )

    return (
        f"Cabe no seu orcamento. "
        f"Depois dessa escolha, ainda sobram R$ {remaining_budget:.2f}."
    )