from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import auth, pages, words


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router, tags=["auth"])
app.include_router(pages.router)
app.include_router(words.router, prefix="/words", tags=["words"])
