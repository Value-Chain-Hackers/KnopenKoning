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
import glob
import re
import json
from rdflib.store import Store

def load_ontologies() -> Graph:
    g = Graph()
    for file in glob.glob("ontologies\*.ttl"):
        print(file)
        g.parse(source=file, format="turtle")
    for file in glob.glob("./ontologies/*.rdf"):
        print(file)
        g.parse(source=file, format="xml")
    return g

@router.get("/")
async def get_graph(request: Request):
    return templates.TemplateResponse("graph.html", {"request": request})

@router.get("/query")
async def query(request: Request):
    graph = load_ontologies()
    graph.serialize(format="json-ld", context={
    'ui':'http://example.org/ontology#',
    'ai':'http://example.org/ai#',
    'db':'http://example.org/ontology/db#',
    'deo':'http://purl.org/spar/deo/',
    'corp': "https://spec.edmcouncil.org/fibo/ontology/BE/Corporations/Corporations/",
    'doco': "http://purl.org/spar/doco/",
    'owl':"http://www.w3.org/2002/07/owl#",
    'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    'rdfs':"http://www.w3.org/2000/01/rdf-schema#",
    'skos':"http://www.w3.org/2004/02/skos/core#",
    'dct':"http://purl.org/dc/terms/",
    'iof-core':'https://spec.industrialontologies.org/ontology/core/Core/',
    'iof-av':'https://spec.industrialontologies.org/ontology/core/meta/AnnotationVocabulary/',
    "scm":"https://spec.industrialontologies.org/ontology/supplychain/SupplyChain/"
    }, destination="ontologies/combined.jsonld", encoding="utf-8")
    with open("ontologies/combined.jsonld", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse({"nodes": data})
