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
import os
from fastapi.responses import RedirectResponse, JSONResponse
from langchain_community.llms.ollama import Ollama
from langchain.prompts import PromptTemplate
import ollama


router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/")
client = ollama.Client(host=OLLAMA_API_URL)

print(f"🤖 Ollama API URL: {OLLAMA_API_URL}")
print(f"🤖 Ollama Host: {OLLAMA_HOST}")
print(f"🤖 Ollama Model: {OLLAMA_MODEL}")

@router.get("/models")
async def query(request: Request):
    return JSONResponse(client.list()["models"])

@router.get("/models/loaded")
async def query(request: Request):
    models = []
    for model in client.ps()["models"]:
        models.append({
            **model,
            "gpu" : model["size_vram"] / model["size"]
        })

    return JSONResponse(models)


@router.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("message")
    prompt_template = PromptTemplate.from_template("You are a helpfull assitant, helping the user with questions relative to supply chains and their ontology.\nQuestion: {question}")
    llm = Ollama(model=OLLAMA_MODEL, base_url=OLLAMA_API_URL)
    chain = prompt_template | llm
    result = chain.invoke(
        {
            "question": question,
        }
    )
    return JSONResponse(result)
