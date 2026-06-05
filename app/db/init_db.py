from app.db.base import Base
from app.db.session import engine
from app.models.category import Category
from app.models.goal import Goal
from app.models.leisure_place import LeisurePlace
from app.models.transaction import Transaction
from app.models.user import User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
