from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.leisure_place import LeisurePlace
from app.schemas.leisure_place import LeisurePlaceCreate, LeisurePlaceRead

router = APIRouter(prefix="/leisure-places", tags=["leisure places"])


@router.post("", response_model=LeisurePlaceRead, status_code=status.HTTP_201_CREATED)
def create_leisure_place(
    leisure_place_data: LeisurePlaceCreate,
    db: Session = Depends(get_db),
):
    leisure_place = LeisurePlace(
        name=leisure_place_data.name,
        description=leisure_place_data.description,
        city=leisure_place_data.city,
        category=leisure_place_data.category,
        average_price=leisure_place_data.average_price,
        provider=leisure_place_data.provider,
        event_url=leisure_place_data.event_url,
        affiliate_url=leisure_place_data.affiliate_url,
        is_partner=leisure_place_data.is_partner,
    )

    db.add(leisure_place)
    db.commit()
    db.refresh(leisure_place)

    return leisure_place


@router.get("", response_model=list[LeisurePlaceRead])
def list_leisure_places(
    city: str | None = None,
    category: str | None = None,
    max_price: Decimal | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    query = select(LeisurePlace)

    if city:
        query = query.where(LeisurePlace.city.ilike(f"%{city}%"))

    if category:
        query = query.where(LeisurePlace.category.ilike(f"%{category}%"))

    if max_price is not None:
        query = query.where(LeisurePlace.average_price <= max_price)

    query = query.order_by(LeisurePlace.is_partner.desc(), LeisurePlace.average_price)

    return db.scalars(query).all()


@router.get("/{leisure_place_id}", response_model=LeisurePlaceRead)
def get_leisure_place(leisure_place_id: int, db: Session = Depends(get_db)):
    leisure_place = db.get(LeisurePlace, leisure_place_id)

    if not leisure_place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lugar de lazer nao encontrado",
        )

    return leisure_place


@router.put("/{leisure_place_id}", response_model=LeisurePlaceRead)
def update_leisure_place(
    leisure_place_id: int,
    leisure_place_data: LeisurePlaceCreate,
    db: Session = Depends(get_db),
):
    leisure_place = db.get(LeisurePlace, leisure_place_id)

    if not leisure_place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lugar de lazer nao encontrado",
        )

    leisure_place.name = leisure_place_data.name
    leisure_place.description = leisure_place_data.description
    leisure_place.city = leisure_place_data.city
    leisure_place.category = leisure_place_data.category
    leisure_place.average_price = leisure_place_data.average_price
    leisure_place.provider = leisure_place_data.provider
    leisure_place.event_url = leisure_place_data.event_url
    leisure_place.affiliate_url = leisure_place_data.affiliate_url
    leisure_place.is_partner = leisure_place_data.is_partner

    db.commit()
    db.refresh(leisure_place)

    return leisure_place


@router.delete("/{leisure_place_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leisure_place(leisure_place_id: int, db: Session = Depends(get_db)):
    leisure_place = db.get(LeisurePlace, leisure_place_id)

    if not leisure_place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lugar de lazer nao encontrado",
        )

    db.delete(leisure_place)
    db.commit()