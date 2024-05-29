# main.py
import os
import sys
import time
import asyncio

import ollama

from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import sqlite3
import uuid
import time
import json
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from utils.extract_knowledge import get_records_manager
from jobs.information_gathering import collect_base_information
from routers import agents, tasks, tools
from config import EMBEDDING_MODEL
app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
scheduler = BackgroundScheduler()


# Define a simple job
def my_job():
    print("Job executed!", datetime.now())

# Serve static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(tools.router, prefix="/tools", tags=["tools"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question")
    context = data.get("context")
    result = ollama.generate(model="phi3:latest", prompt=question, system="You are a helpfull assitant, helping the user to create dashboards and visualizations of supply chains.", stream=True)
    def generate(toStream):
        for r in toStream:
            yield r["response"]
  
    
    return StreamingResponse(generate(result), media_type="plain/text")



@app.get("/api/records_manager")
async def records_manager():
    records_manager = get_records_manager("None")
    return records_manager.list_keys()



# # Schedule jobs
# scheduler.add_job(my_job, IntervalTrigger(minutes=1), id='interval_job')
# scheduler.add_job(my_job, CronTrigger(day_of_week='mon-fri', hour=22, minute=30), id='cron_job')

# # Start the scheduler
# scheduler.start()

# # Function to list jobs
# @app.get("/list_jobs")
# def list_jobs():
#     jobs = [job.id for job in scheduler.get_jobs()]
#     return jobs

# # Function to start a job manually
# def start_job_manually(job_id):
#     job = scheduler.get_job(job_id)
#     if job:
#         job.func()
#     else:
#         print(f"No job found with ID: {job_id}")



@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    print(file.filename)
    with open(file.filename, "wb") as f:
        f.write(contents)
    return {"filename": file.filename}

from db import Company, Website, Records, Agents, Tasks, Tools
from db.session import SessionLocal
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/companies")
async def get_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.company_name).all()
    return companies

@app.get("/api/agents")
async def get_agents(db: Session = Depends(get_db)):
    agents = db.query(Agents).order_by(Agents.id).all()
    return agents

@app.get("/api/tasks")
async def get_tasks(db: Session = Depends(get_db)):
    agents = db.query(Tasks).order_by(Tasks.id).all()
    return agents

@app.get("/api/tools")
async def get_tools(db: Session = Depends(get_db)):
    tools = db.query(Tools).order_by(Tools.name).all()
    return tools

@app.get("/{company:str}/")
async def read_company(request: Request, company: str):
    context = {
        "request": request,  # Required for Jinja2 to work with FastAPI
        "title": company,
        "company": company
    }
    return templates.TemplateResponse("view.html", context)

@app.get("/admin")
async def read_admin(request: Request, db: Session = Depends(get_db)):
    agents = await get_agents(db)
    tasks = await get_tasks(db)
    tools = await get_tools(db)
    context = {
        "request": request,  # Required for Jinja2 to work with FastAPI
        "title": "Admininstration",
        "agents": agents,
        "tasks": tasks,
        "tools": tools
    }
    return templates.TemplateResponse("admin.html", context)


processes = {}

@app.get("/progress/{id:str}")
async def progress(id: str, db: Session = Depends(get_db)):
    async def event_generator(db: Session):
        if id in processes:
            company = processes[id]["company"]
            yield {
                "event": "message",
                "id": str(1),
                "data": f'{{"step": 1, "detail": "Collecting base information about {company}."}}'
            }
            await asyncio.sleep(1)
            question = processes[id]["question"]
            records = collect_base_information(company, db)
            print(records)
            yield {
                "event": "message",
                "id": str(1),
                "data": f'{{"step": 1, "detail": "Collected {len(records)} for {company}."}}'
            }
            await asyncio.sleep(2)

        for step in range(2, 7):
            await asyncio.sleep(2)
            yield {
                "event": "message",
                "id": str(step),
                "data": f'{{"step": {step}, "detail": "Step {step} done."}}'
            }
    
    return EventSourceResponse(event_generator(db))

@app.post("/process")
async def process(request: Request):
    data = await request.json()
    company = data.get("company")
    question = data.get("question")
    uid = uuid.uuid4()
    processes[str(uid)] = {"company": company, "question": question}
    return {"company": company, "question": question, "uid": str(uid)}

@app.get("/view/{company:str}")
async def read_root(request: Request, company: str, db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.company_name).filter(Company.company_name == company).first()
    context = {
        "request": request,  # Required for Jinja2 to work with FastAPI
        "title": "ChainWise",
        "company": companies
    }
    return templates.TemplateResponse("view.html", context)

@app.get("/")
async def read_root(request: Request, db: Session = Depends(get_db)):
    companies = await get_companies(db)
    context = {
        "request": request,  # Required for Jinja2 to work with FastAPI
        "title": "ChainWise",
        "companies": companies
    }
    return templates.TemplateResponse("index.html", context)


from sse_starlette.sse import EventSourceResponse
