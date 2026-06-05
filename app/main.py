from fastapi import FastAPI

from app.api.routes.categories import router as categories_router
from app.api.routes.database import router as database_router
from app.api.routes.health import router as health_router
from app.api.routes.transactions import router as transactions_router
from app.api.routes.summary import router as summary_router
from app.api.routes.goals import router as goals_router
from app.api.routes.leisure_places import router as leisure_places_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.budget import router as budget_router
from app.api.routes.insights import router as insights_router
from app.api.routes.users import router as users_router
from app.db.init_db import init_db

app = FastAPI(title="Dinsix Finance API")

init_db()

app.include_router(health_router)
app.include_router(database_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(summary_router)
app.include_router(goals_router)
app.include_router(leisure_places_router)
app.include_router(recommendations_router)
app.include_router(budget_router)
app.include_router(insights_router)
app.include_router(users_router)