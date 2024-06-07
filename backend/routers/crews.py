from pathlib import Path
from typing import Optional
from fastapi import Depends, Request, Body, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRouter 
from sqlalchemy.orm import Session
from db import Crews
from db.session import SessionLocal
from fastapi.templating import Jinja2Templates

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{crew_id:int}")
def read_tool(crew_id: int, request: Request, db: Session = Depends(get_db)):
    task = db.query(Crews).filter(Crews.id == crew_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return templates.TemplateResponse("edit_tool.html", {"request": request, "task": task})

@router.get("/new")
def new_task(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("edit_tool.html", {"request": request})

@router.post("/create")
def create_task(
    request: Request,
    name: str = Body(...),
    process: str = Body(...),
    agents: Optional[list[int]] = Body(...),
    db: Session = Depends(get_db)
):
    new_crew = Crews(
        name=name,
        process=process,
        agents=agents
    )
    db.add(new_crew)
    db.commit()
    db.refresh(new_crew)
    return RedirectResponse(url="../admin", status_code=303)

@router.post("/{crew_id}/edit")
def edit_crew(
    crew_id: int,
    request: Request,
    name: str = Body(...),
    process: str = Body(...),
    agents: Optional[list[int]] = Body(...),
    db: Session = Depends(get_db)
):
    crew = db.query(Crews).filter(Crews.id == crew_id).first()
    if crew is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    crew.name=name,
    crew.process=process,
    crew.agents=agents
    db.commit()
    db.refresh(crew)
    return RedirectResponse(url="../admin", status_code=303)

@router.post("/{crew_id}/delete")
def delete_task(crew_id: int, db: Session = Depends(get_db)):
    crew = db.query(Crews).filter(Crews.id == crew_id).first()
    if crew is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(crew)
    db.commit()
    return RedirectResponse(url="../admin", status_code=303)
