from typing import Optional

from fastapi import FastAPI, Request, Header, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from .database import SessionLocal, engine

from . import models
from sqlalchemy.orm import Session

# Normally done with migrations
models.Base.metadata.create_all(bind=engine)
app = FastAPI()

templates = Jinja2Templates(directory="sql_app/templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_populate_db():
    db = SessionLocal()
    num_films = db.query(models.Film).count()
    if num_films == 0:
        films = [
            {'name': 'Blade Runner', 'director': 'Ridley Scott'},
            {'name': 'Pulp Fiction', 'director': 'Quentin Tarantino'},
            {'name': 'Mulholland Drive', 'director': 'David Lynch'},
            {'name': 'Jurassic Park', 'director': 'Steven Spielberg'},
            {'name': 'Tokyo Story', 'director': 'Vasujiro Ozu'},
            {'name': 'Chungking Express', 'director': 'Kar-Wai Wong'},
        ]

        for film in films:
            db.add(models.Film(**film))
        db.commit()
        db.close()
    else:
        print(f"{num_films} films already in DB")

@app.get("/index/", response_class=HTMLResponse)
async def movielist(
        request: Request,
        hx_request: Optional[str] = Header(None),
        db: Session = Depends(get_db),
        page: int = 1,
):
    NUMBER_PER_PAGE = 2
    OFFSET = (page - 1) * NUMBER_PER_PAGE
    films = db.query(models.Film).offset(OFFSET).limit(NUMBER_PER_PAGE)
    context = {"request": request, 'films': films, 'page': page}

    if hx_request:
        return templates.TemplateResponse("table.html", context)

    return templates.TemplateResponse("index.html", context)
