"""FastAPI application factory: configures logging and mounts routers."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, households, recipes, tags
from app.config import get_settings
from app.logging_config import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(title="Recipe Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(recipes.router)
app.include_router(tags.router)
app.include_router(households.router)
