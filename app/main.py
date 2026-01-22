from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import auth, pages, words


app = FastAPI()
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(auth.router, tags=["auth"])
app.include_router(pages.router)
app.include_router(words.router, prefix="/words", tags=["words"])
