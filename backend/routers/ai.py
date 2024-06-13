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
import ollama

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.get("")
async def query(request: Request):
    return templates.TemplateResponse("ai.html", {"request": request, "class": []})



@router.get("/models")
async def query(request: Request):
    
    return JSONResponse(ollama.list())


@router.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question")
    context = data.get("context")
    result = ollama.generate(model="phi3:latest", prompt=question, system="You are a helpfull assitant, helping the user to create dashboards and visualizations of supply chains.", stream=True)
    def generate(toStream):
        for r in toStream:
            yield r["response"]
  
    
    return StreamingResponse(generate(result), media_type="plain/text")


@router.get("/answer")
async def answer(request: Request):
    from utils.uielements import UIElementsBuilder
    data = await request.json()
    question = data.get("question")
    builder = UIElementsBuilder()
    elements = builder.answer(question)
    return JSONResponse(elements)