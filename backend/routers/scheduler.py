from pathlib import Path
from typing import Optional
from fastapi import Depends, Request, Body, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRouter 
from sqlalchemy.orm import Session
from db import Tools
from db.session import SessionLocal
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
import time
from fastapi.responses import RedirectResponse, JSONResponse
import os
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
MYSQL_DATABASE_URL = os.getenv("MYSQL_DATABASE_URL",  "mysql+mysqlconnector://vch_user:rQMK5oLIg5i7KBiyk7uhy7uQqVg3cyjx@mysql/vch")

jobstores = {
    'default': SQLAlchemyJobStore(url=MYSQL_DATABASE_URL)
    # 'redis': RedisJobStore(jobs_key='apscheduler.jobs', run_times_key='apscheduler.run_times', host='localhost', port=6379, db=0)
}
def my_job():
    print("Job executed!")



@router.get("/jobs")
async def query(request: Request):
    return JSONResponse({"jobs": jobstores["default"].get_all_jobs()})