from pathlib import Path
from typing import Optional
from fastapi import Depends, Request, Body, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRouter 
from requests import Session
from db import Agents
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



@router.get("/{agent_id:int}")
def read_agent(agent_id: int, request: Request, db: Session = Depends(get_db)):
    agent = db.query(Agents).filter(Agents.id == agent_id).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return templates.TemplateResponse("edit_agent.html", {"request": request, "agent": agent})

@router.get("/new")
def new_agent(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("edit_agent.html", {"request": request})

@router.post("/create")
def create_agent(
    request: Request,
    role: str = Body(...),
    goal: str = Body(...),
    backstory: str = Body(...),
    tools: str = Body(...),
    llm: str = Body(...),
    llm_functions: str = Body(...),
    max_iter: int = Body(...),
    max_rpm: Optional[int] = Body(None),
    max_time: Optional[int] = Body(None),
    verbose: int = Body(0),
    allow_delegation: int = Body(0),
    cache: int = Body(1),
    db: Session = Depends(get_db)
):
    new_agent = Agents(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools,
        llm=llm,
        llm_functions=llm_functions,
        max_iter=max_iter,
        max_rpm=max_rpm,
        max_time=max_time,
        verbose=verbose,
        allow_delegation=allow_delegation,
        cache=cache
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return RedirectResponse(url="../admin", status_code=303)

@router.post("/{agent_id}/edit")
def edit_agent(
    agent_id: int,
    request: Request,
    role: str = Form(...),
    goal: str = Form(...),
    backstory: str = Form(...),
    tools: str = Form(...),
    llm: str = Form(...),
    llm_functions: str = Form(...),
    max_iter: int = Form(...),
    max_rpm: Optional[int] = Form(None),
    max_time: Optional[int] = Form(None),
    verbose: int = Form(0),
    allow_delegation: int = Form(0),
    cache: int = Form(1),
    db: Session = Depends(get_db)
):
    agent = db.query(Agents).filter(Agents.id == agent_id).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.role = role
    agent.goal = goal
    agent.backstory = backstory
    agent.tools = tools
    agent.llm = llm
    agent.llm_functions = llm_functions
    agent.max_iter = max_iter
    agent.max_rpm = max_rpm
    agent.max_time = max_time
    agent.verbose = verbose
    agent.allow_delegation = allow_delegation
    agent.cache = cache

    db.commit()
    db.refresh(agent)
    return RedirectResponse(url="/", status_code=303)

@router.post("/{agent_id}/delete")
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agents).filter(Agents.id == agent_id).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(agent)
    db.commit()
    return RedirectResponse(url="/", status_code=303)