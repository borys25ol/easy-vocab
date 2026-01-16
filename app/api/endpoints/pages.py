from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("quiz.html", {"request": request})


@router.get("/quiz_translate", response_class=HTMLResponse)
async def quiz_translate_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("quiz_translate.html", {"request": request})


@router.get("/flashcards", response_class=HTMLResponse)
async def flashcards_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("flashcards.html", {"request": request})


@router.get("/phrasal", response_class=HTMLResponse)
async def phrasal_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("phrasal_verbs.html", {"request": request})


@router.get("/idioms", response_class=HTMLResponse)
async def idioms_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("idioms.html", {"request": request})
