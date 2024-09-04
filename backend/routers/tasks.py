from pathlib import Path
from typing import Optional
from fastapi import Depends, Request, Body, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.routing import APIRouter 
from sqlalchemy.orm import Session
from db import Tasks
from fastapi.templating import Jinja2Templates

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

from db.session import SessionLocal

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{task_id:int}")
def read_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    task = db.query(Tasks).filter(Tasks.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return templates.TemplateResponse("edit_task.html", {"request": request, "task": task})

@router.get("/new")
def new_task(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("edit_task.html", {"request": request})

@router.post("/create")
def create_task(
    request: Request,
    description: str = Body(...),
    expected_output: str = Body(...),
    tools: Optional[str] = Body(...),
    asynchronious: Optional[int] = Body(...),
    context: Optional[str] = Body(...),
    config: Optional[str] = Body(...),
    output_json: Optional[str] = Body(...),
    output_pydantic: Optional[str] = Body(...),
    output_file: Optional[str] = Body(...),
    human_input: Optional[int] = Body(...),
    db: Session = Depends(get_db)
):
    new_task = Tasks(
        description=description,
        expected_output=expected_output,
        tools=tools,
        asynchronious=asynchronious,
        context=context,
        config=config,
        output_json=output_json,
        output_pydantic=output_pydantic,
        output_file=output_file,
        human_input=human_input
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return RedirectResponse(url="../admin", status_code=303)

@router.post("/{task_id}/edit")
def edit_task(
    task_id: int,
    request: Request,
    description: str = Form(...),
    backstory: str = Form(...),
    expected_output: str = Form(...),
    tools: str = Form(...),
    asynchronious: str = Form(...),
    context: str = Form(...),
    config: str = Form(...),
    output_json: str = Form(...),
    output_pydantic: str = Form(...),
    output_file: Optional[str] = Form(...),
    human_input: Optional[int] = Form(...),
    db: Session = Depends(get_db)
):
    task = db.query(Tasks).filter(Tasks.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.description = description
    task.expected_output = expected_output
    task.tools = tools
    task.asynchronious = asynchronious
    task.context = context
    task.config = config
    task.output_json = output_json
    task.output_pydantic = output_pydantic
    task.output_file = output_file
    task.human_input = human_input

    db.commit()
    db.refresh(task)
    return RedirectResponse(url="/tasks", status_code=303)

@router.post("/{task_id}/delete")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Tasks).filter(Tasks.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return RedirectResponse(url="/tasks", status_code=303)
