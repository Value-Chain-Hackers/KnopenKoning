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
import mlflow
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("Chainwise-Chatbot")

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
OLLAMA_URL = os.getenv("OLLAMA_URL", "localhost:11434")
client = ollama.Client(host=OLLAMA_URL)
mlflow.langchain.autolog(log_models=True, log_input_examples=True)


@router.get("")
async def query(request: Request):
    return templates.TemplateResponse("ai.html", {"request": request, "class": []})

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
    llm = Ollama(model="phi3")
    chain = prompt_template | llm
    result = chain.invoke(
        {
            "question": "Why should we colonize Mars instead of Venus?",
        }
    )
    return JSONResponse(result)


@router.get("/answer")
async def answer(request: Request):
    from utils.uielements import UIElementsBuilder
    data = await request.json()
    question = data.get("question")
    builder = UIElementsBuilder(OLLAMA_URL)
    elements = builder.answer(question)
    return JSONResponse(elements)