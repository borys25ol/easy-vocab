from fastapi import APIRouter


router = APIRouter()


@router.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Probe target for Kubernetes.

    Deliberately does not touch the database. A readiness probe answers
    "is this process serving requests", not "is the database up". Checking
    the database here would turn a brief database outage into every pod
    being killed at once.
    """
    return {"status": "ok"}
