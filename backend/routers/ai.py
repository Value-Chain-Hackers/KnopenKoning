from pathlib import Path
from typing import Optional
from bson import ObjectId
from fastapi import Depends, Request, Body, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRouter 
from sqlalchemy.orm import Session
from backend.routers import auth
from db import Tools
from db.session import SessionLocal
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
import time
import os
from fastapi.responses import RedirectResponse, JSONResponse
from langchain_community.llms.ollama import Ollama
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.prompts import PromptTemplate
import ollama
from config import OLLAMA_MODEL, OLLAMA_API_URL, OLLAMA_HOST
from utils.mongo_process import Process

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

client = ollama.Client(host=OLLAMA_API_URL)

@router.get("/models")
async def list_models(request: Request):
    return JSONResponse(client.list()["models"])

@router.get("/models/loaded")
async def loaded_models(request: Request):
    models = []
    for model in client.ps()["models"]:
        models.append({
            **model,
            "gpu" : model["size_vram"] / model["size"]
        })

    return JSONResponse(models)


@router.post("/ask")
async def ask(request: Request, user = Depends(auth.get_current_user)):
    data = await request.json()
    question = data.get("message")
    sessionId = data.get("sessionId")
    process = Process.get(ObjectId(sessionId))
    print(question, sessionId)

    prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """\
         You are a helpfull assitant, helping the user with questions relative to supply chains and their ontology.\
         The user has asked this initial question: "{initial_question}"\
         And currently has received the following elements to display: {elements}\
         """),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

    llm = Ollama(model=OLLAMA_MODEL, base_url=OLLAMA_API_URL, keep_alive="-1m")
    chain = prompt | llm
    chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string="mongodb://root:kpnBCdiAFamV5InlXPvaq7X2M5TsDOEd@localhost:27017",
        database_name="vch",
        collection_name="chat_histories",
    ),
    input_messages_key="question",
    history_messages_key="history",
    )
    config = {"configurable": {"session_id": sessionId}}
    currentElements = []
    for element in process.elements:
        currentElements.append(f"{element['title']} ({element['type']})")
    result = chain_with_history.invoke(
        {
            "question": question,
            "initial_question": process.question,
            "elements": currentElements,
        },
        config=config,
    )
    return JSONResponse(result)
