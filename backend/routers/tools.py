from pathlib import Path
from typing import Optional
from fastapi import Depends, Request, Body, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRouter 
from sqlalchemy.orm import Session
from db import Tools
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

@router.get("/{tool_id:int}")
def read_tool(tool_id: int, request: Request, db: Session = Depends(get_db)):
    task = db.query(Tools).filter(Tools.id == tool_id).first()
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
    description: str = Body(...),
    output: str = Body(...),
    enabled: Optional[int] = Body(...),
    db: Session = Depends(get_db)
):
    new_tool = Tools(
        name=name,
        description=description,
        output=output,
        enabled=enabled
    )
    db.add(new_tool)
    db.commit()
    db.refresh(new_tool)
    return RedirectResponse(url="../admin", status_code=303)

@router.post("/{tool_id}/edit")
def edit_tool(
    tool_id: int,
    request: Request,
    name: str = Body(...),
    description: str = Body(...),
    output: str = Body(...),
    enabled: Optional[int] = Body(...),
    db: Session = Depends(get_db)
):
    tool = db.query(Tools).filter(Tools.id == tool_id).first()
    if tool is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    tool.name=name,
    tool.description=description,
    tool.output=output,
    tool.enabled=enabled

    db.commit()
    db.refresh(tool)
    return RedirectResponse(url="../admin", status_code=303)

@router.post("/{tool_id}/delete")
def delete_task(tool_id: int, db: Session = Depends(get_db)):
    tool = db.query(Tools).filter(Tools.id == tool_id).first()
    if tool is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(tool)
    db.commit()
    return RedirectResponse(url="../admin", status_code=303)
