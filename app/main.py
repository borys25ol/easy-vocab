from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import auth, health, pages, words
from app.core.csrf import CSRFTokenMiddleware


app = FastAPI()
# ty reads add_middleware through a ParamSpec protocol that BaseHTTPMiddleware
# subclasses do not satisfy. The call is correct at runtime; tests/test_csrf.py
# exercises it.
app.add_middleware(CSRFTokenMiddleware)  # ty: ignore[invalid-argument-type]
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, tags=["auth"])
app.include_router(pages.router)
app.include_router(words.router, prefix="/words", tags=["words"])
