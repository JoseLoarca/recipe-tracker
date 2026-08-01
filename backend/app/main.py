"""FastAPI application factory: configures logging and mounts routers."""

from fastapi import FastAPI

from app.api.routes import auth, health, households, recipes, tags
from app.logging_config import configure_logging

configure_logging()

app = FastAPI(title="Recipe Tracker API")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(recipes.router)
app.include_router(tags.router)
app.include_router(households.router)
