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

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.post("/connect")
async def connect(request: Request):
    data = await request.json()
    def generate(result):
        try:
            while(True):
                time.sleep(1)
                yield "{}"
        except Exception as e:
            print(e)
            return '{"status": "error"}'
        
    return StreamingResponse(generate(data), media_type="application/json")
