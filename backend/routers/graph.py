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

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.plugins.stores.memory import SimpleMemory
from rdflib.plugins.sparql import prepareQuery
import glob
import re
import json
from rdflib.store import Store

def load_ontologies() -> Graph:
    g = Graph()
    for file in glob.glob("ontologies\*.ttl"):
        print(file)
        g.parse(source=file, format="turtle")
    for file in glob.glob("ontologies\*.rdf"):
        print(file)
        g.parse(source=file, format="xml")
    return g

@router.get("/")
async def get_graph(request: Request):

    return templates.TemplateResponse("graph.html", {"request": request})

@router.post("/query")
async def query(request: Request):
    query = await request.json()
    query = query['query']
    print(query)
    graph = load_ontologies()
    result = graph.query(prepareQuery(query))
    data = [
            {str(var): str(value) for var, value in row.items()}
            for row in result
        ]
    return JSONResponse({"data": data})
