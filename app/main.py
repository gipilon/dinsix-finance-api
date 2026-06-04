from fastapi import FastAPI

from app.api.routes.categories import router as categories_router
from app.api.routes.database import router as database_router
from app.api.routes.health import router as health_router
from app.db.init_db import init_db

app = FastAPI(title="Dinsix Finance API")

init_db()

app.include_router(health_router)
app.include_router(database_router)
app.include_router(categories_router)
