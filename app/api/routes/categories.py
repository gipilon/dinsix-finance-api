from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(category_data: CategoryCreate, db: Session = Depends(get_db)):
    existing_category = db.scalar(
        select(Category).where(Category.name == category_data.name)
    )

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Categoria ja cadastrada",
        )

    category = Category(
        name=category_data.name,
        description=category_data.description,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.get("", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).order_by(Category.name)).all()

@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.get(Category, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria nao encontrada",
        )

    return category

@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
):
    category = db.get(Category, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria nao encontrada",
        )

    existing_category = db.scalar(
        select(Category).where(
            Category.name == category_data.name,
            Category.id != category_id,
        )
    )

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Categoria ja cadastrada",
        )

    category.name = category_data.name
    category.description = category_data.description

    db.commit()
    db.refresh(category)

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.get(Category, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria nao encontrada",
        )

    db.delete(category)
    db.commit()
