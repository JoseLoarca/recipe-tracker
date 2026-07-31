from fastapi import FastAPI

from app.api.routes import health
from app.logging_config import configure_logging

configure_logging()

app = FastAPI(title="Recipe Tracker API")

app.include_router(health.router)
