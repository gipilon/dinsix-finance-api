from app.db.base import Base
from app.db.session import engine
from app.models.category import Category
from app.models.transaction import Transaction


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
