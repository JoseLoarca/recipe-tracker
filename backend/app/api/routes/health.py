"""Liveness/readiness endpoint for the Docker Compose healthcheck."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Report that the API process is up.

    Returns:
        A simple status payload.
    """
    return {"status": "ok"}
