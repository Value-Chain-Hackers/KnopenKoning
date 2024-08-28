# main.py
from crewai.tasks.task_output import TaskOutput
from db import Company, Website, Records, Agents, Tasks, Tools, Crews, Document
from db.session import SessionLocal
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_community.chat_models.ollama import ChatOllama
from langchain_core.agents import AgentAction, AgentFinish, AgentStep
from langchain_core.callbacks import BaseCallbackHandler, BaseCallbackManager
from langchain_core.messages import BaseMessage
from langserve import add_routes
from pathlib import Path
from routers import agents, tasks, tools, ai, ui, graph, scheduler, auth
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse
from typing import Any, Dict, List, Optional
from utils.extract_knowledge import get_records_manager
from utils.mongo_process import Process
from utils.ontology_parser import GraphVisitor
from utils.uielements import UIElementsBuilder
import asyncio
import json
import ollama
import os
import uuid
from bson import ObjectId

from duckduckgo_search import DDGS

search = DDGS()

load_dotenv()
app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://ollama:11434/")

# Serve static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(tools.router, prefix="/tools", tags=["tools"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(ui.router, prefix="/ui", tags=["ui"])
app.include_router(graph.router, prefix="/graph", tags=["graph"])
app.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/records_manager")
async def records_manager():
    records_manager = get_records_manager("None")
    return records_manager.list_keys()

graphVisitor = GraphVisitor()
graphVisitor.parse("./data/supplychain.ttl", "text/turtle")


@app.get("/supplychain")
def read_entity_empt(request: Request):
    return templates.TemplateResponse("show_class.html", {"request": request, "class": []})

@app.get("/supplychain/{class_id:str}", response_class=PlainTextResponse)
def read_entity(class_id: str, request: Request):
    print("read entity")
    class_id = graphVisitor.graph.namespace_manager.absolutize(class_id)
    gClass = graphVisitor.build_class(class_id)
    if gClass is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return graphVisitor.rdf_to_markdown()

model = ChatOllama(model="llama3.1:latest", base_url=OLLAMA_API_URL)

@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    print(file.filename)
    with open(file.filename, "wb") as f:
        f.write(contents)
    return {"filename": file.filename}

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

@app.get("/api/crews")
async def get_crews(db: Session = Depends(get_db)):
    crews = db.query(Crews).order_by(Crews.id).all()
    return crews

@app.get("/api/tasks")
async def get_tasks(db: Session = Depends(get_db)):
    agents = db.query(Tasks).order_by(Tasks.id).all()
    return agents

@app.get("/api/tools")
async def get_tools(db: Session = Depends(get_db)):
    tools = db.query(Tools).order_by(Tools.name).all()
    return tools

@app.get("/api/models")
async def get_models():
    client = ollama.Client(OLLAMA_API_URL)
    tools = client.list()["models"]
    return tools


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


builder = UIElementsBuilder()

class customCallbackManager(BaseCallbackManager):
    def __init__(self, handlers: List[BaseCallbackHandler], inheritable_handlers: List[BaseCallbackHandler] | None = None, parent_run_id: uuid.UUID | None = None, *, tags: List[str] | None = None, inheritable_tags: List[str] | None = None, metadata: Dict[str, Any] | None = None, inheritable_metadata: Dict[str, Any] | None = None) -> None:
        
        super().__init__(handlers, inheritable_handlers, parent_run_id, tags=tags, inheritable_tags=inheritable_tags, metadata=metadata, inheritable_metadata=inheritable_metadata)
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, *, run_id: uuid.UUID, parent_run_id: uuid.UUID | None = None, tags: List[str] | None = None, metadata: Dict[str, Any] | None = None, inputs: Dict[str, Any] | None = None, **kwargs: Any) -> Any:
        print("***Tool Start: ", serialized)
        return super().on_tool_start(serialized, input_str, run_id=run_id, parent_run_id=parent_run_id, tags=tags, metadata=metadata, inputs=inputs, **kwargs)
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], *, run_id: uuid.UUID, parent_run_id: uuid.UUID | None = None, tags: List[str] | None = None, metadata: Dict[str, Any] | None = None, **kwargs: Any) -> Any:
        print("***LLM Start: ", serialized)
        return super().on_llm_start(serialized, prompts, run_id=run_id, parent_run_id=parent_run_id, tags=tags, metadata=metadata, **kwargs)
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], *, run_id: uuid.UUID, parent_run_id: uuid.UUID | None = None, tags: List[str] | None = None, metadata: Dict[str, Any] | None = None, **kwargs: Any) -> Any:
        print("***Chain Start: ", serialized)
        return super().on_chain_start(serialized, inputs, run_id=run_id, parent_run_id=parent_run_id, tags=tags, metadata=metadata, **kwargs)

class customCallback(BaseCallbackHandler):
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], *, run_id: uuid.UUID, parent_run_id: uuid.UUID | None = None, tags: List[str] | None = None, metadata: Dict[str, Any] | None = None, **kwargs: Any) -> Any:
        print("***LLM Start: ", serialized)
        return super().on_llm_start(serialized, prompts, run_id=run_id, parent_run_id=parent_run_id, tags=tags, metadata=metadata, **kwargs)
    
    def on_agent_action(self, action: AgentAction, *, run_id: uuid.UUID, parent_run_id: uuid.UUID | None = None, **kwargs: Any) -> Any:
        print("***Agent Action: ", action)
        return super().on_agent_action(action, run_id=run_id, parent_run_id=parent_run_id, **kwargs)
    

    def on_chat_model_start(self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], *, run_id: uuid.UUID, parent_run_id: uuid.UUID | None = None, tags: List[str] | None = None, metadata: Dict[str, Any] | None = None, **kwargs: Any) -> Any:
        # print("***Chat Model Start: serialized: ", serialized)
        # print("***Chat Model Start: messages: ", messages )
        # print("***Chat Model Start: metadata: ", metadata )
        print("***Chat Model Start: kwargs: ",  kwargs["invocation_params"]["model"])
        return super().on_chat_model_start(serialized, messages, run_id=run_id, parent_run_id=parent_run_id, tags=tags, metadata=metadata, **kwargs)

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, *, run_id: uuid.UUID, parent_run_id: uuid.UUID | None = None, tags: List[str] | None = None, metadata: Dict[str, Any] | None = None, inputs: Dict[str, Any] | None = None, **kwargs: Any) -> Any:
        print("***Tool Start: ", serialized)
        return super().on_tool_start(serialized, input_str, run_id=run_id, parent_run_id=parent_run_id, tags=tags, metadata=metadata, inputs=inputs, **kwargs)
    
    def on_tool_end(self, output: Any, *, run_id: uuid.UUID, parent_run_id: uuid.UUID | None = None, **kwargs: Any) -> Any:
        print("***Tool End: ", output)
        return super().on_tool_end(output, run_id=run_id, parent_run_id=parent_run_id, **kwargs)

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], *, run_id: uuid.UUID, parent_run_id: uuid.UUID | None = None, tags: List[str] | None = None, metadata: Dict[str, Any] | None = None, **kwargs: Any) -> Any:
        print("***Chain Start: ", serialized)
        return super().on_chain_start(serialized, inputs, run_id=run_id, parent_run_id=parent_run_id, tags=tags, metadata=metadata, **kwargs)

    def on_chain_end(self, outputs: Dict[str, Any], *, run_id: uuid.UUID, parent_run_id: uuid.UUID | None = None, **kwargs: Any) -> Any:
        print("***Chain End: ", outputs)
        return super().on_chain_end(outputs, run_id=run_id, parent_run_id=parent_run_id, **kwargs)

    def on_text(self, text: str, *, run_id: uuid.UUID, parent_run_id: uuid.UUID | None = None, **kwargs: Any) -> Any:
        print("***Text: ", text)
        return super().on_text(text, run_id=run_id, parent_run_id=parent_run_id, **kwargs)

@app.get("/crews/{name:str}/kickoff")
async def kickoff(name: str, db: Session = Depends(get_db)):
    from crewai import Crew, Agent, Task
    from crewai.tools.agent_tools import AgentTools
    from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchResults

    from backend.tools.wikipedia import WikipediaQueryRun
    from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
    from backend.tools.search import DuckSearch

    llm = ChatOllama(model="mistral:latest", num_ctx=4096, num_predict=2048, temperature=1, base_url="http://ollama:11434/")
    crew = db.query(Crews).filter(Crews.name == name).first()
    agents = db.query(Agents).all()
    tasks = db.query(Tasks).all()
    all_agents = []
    for agent in agents:
        print(agent)
        a = Agent(
            role=agent.role, 
            backstory=agent.backstory, 
            goal=agent.goal,
            allow_delegation=agent.allow_delegation,
            verbose=agent.verbose,
            cache=agent.cache,
            llm=llm,
            memory=True,
            tools = [DuckSearch(), WikipediaQueryRun(verbose=True, api_wrapper=WikipediaAPIWrapper())],
            )
        all_agents.append(a)
    all_tasks = []
    for task in tasks:
        print(task)
        t = Task(
            description=task.description,
            expected_output=task.expected_output,
            agent=all_agents[0],
            
        )
        all_tasks.append(t)
    
    all_results = []
    
        
    def task_callback(args):
        if isinstance(args, TaskOutput):
            print("--- TASK OUTPUT ---", args.json(),"\n----\n")
            all_results.append(args.model_dump_json())
        else:
            with open("./crew_output.json", "a", encoding="utf-8") as f:
                f.write(args.json())
            all_results.append(args)
            print("\n\nTASK ::: ",args, end="\n---------------------\n")

    def step_callback(args):
        # if args is list:
        if isinstance(args, list):
            for arg in args:
                # if arg is tuple:
                if isinstance(arg, tuple):
                    for a in arg:
                        if isinstance(a, AgentAction):
                            print("--- AGENT ACTION ---", a.json(),"\n----\n")
                            all_results.append(a.json())
                        elif isinstance(a, AgentFinish):
                            print("--- AGENT FINISH ---", a.json(),"\n----\n")
                            all_results.append(a.json())
                        elif isinstance(a, AgentStep):
                            print("--- AGENT STEP ---", a.json(),"\n----\n")
                            all_results.append(a.json())
                        else:
                            print("--- UNK AGENT STEP ---", type(a),"\n----\n")
                            with open("./crew_output.json", "a", encoding="utf-8") as f:
                                f.write(a)
                            all_results.append(json.dumps({"data": a , "type": "AgentStepData"}, ensure_ascii=False))
                else:
                    with open("./crew_output.json", "a") as f:
                        f.write(arg.json())
                    all_results.append(arg.json())
                    print("\n\nSTEPq ::: ",arg, end="\n---------------------\n")
        elif isinstance(args, AgentAction):
            all_results.append(args.json())
            print("--- AGENT ACTION1 ---", args.json(),"\n----\n")
        elif isinstance(args, AgentFinish):
            all_results.append(args.json())
            print("--- AGENT FINISH1 ---", args.json(),"\n----\n")
        elif isinstance(args, AgentStep):
            all_results.append(args.json())
            print("--- AGENT STEP1 ---", args.json(),"\n----\n")
        else: 
            all_results.append(args.json())
            with open("./crew_output.json", "a", encoding="utf-8") as f:
                f.write(args.json())
            print("\n\nSTEPw ::: ",args, end="\n---------------------")


    
    c = Crew(
        tasks=all_tasks,
        agents=all_agents,
        full_output=True,
        verbose=True,
        output_log_file="./crew_output.log",
        task_callback=task_callback,
        step_callback=step_callback,
        
        manager_llm=llm
        
    )
   
    async def event_generator(c):
        # Run kickoff in non-blocking mode and yield elements from task_callback and step_callback
        from concurrent.futures import ThreadPoolExecutor
        import threading
        yield {"event": "message", "id": str(1), "data": f'{{"step": 1, "detail": "Starting the crew.", "type": "CrewStart"}}'}
        def kickoff_thread():
        
            with open("./data/supplychain.rdf", "r") as f:
                data = f.read()
        
            try:    
                c.kickoff(inputs={'company': 'Coca-Cola', 'ontology': data})
            except Exception as e:
                print("Error: ", e)
        # Using a thread to run the blocking kickoff method
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(kickoff_thread)
        # Continuously check if the kickoff call is complete
        msgCount = 1
        while not future.done():
           # pop the first element from the results list
            if all_results and len(all_results) > 0:
                msgCount += 1
                yield {"event": "message", "id": str(msgCount), "data": all_results.pop(0) }
            else:
                await asyncio.sleep(3   )
        msgCount += 1
        yield {"event": "message", "id": str(msgCount), "data": f'{{"step": 1, "detail": "Crew Completed."}}'}
        # Close the executor
        executor.shutdown()

    return EventSourceResponse(event_generator(c))

@app.get("/progress/{process_id:str}")
async def progress(process_id: str, db: Session = Depends(get_db)):
    process_id = ObjectId(process_id)
    async def event_generator(db: Session, process_id: ObjectId):
        process = Process.get(process_id)
        question = process.question

        yield {
            "event": "message",
            "id": str(1),
            "data": f'{{"step": 1, "detail": "Collecting base."}}'
        }
        await asyncio.sleep(2)
        records = []

        ddg_results = search.text(question)
        builder.search_results.extend(ddg_results)
        process.search_results.extend(ddg_results)
        process.save()
        yield {
            "event": "message",
            "id": str(2),
            "data": f'{{"step": 2, "detail": "Search Results {len(ddg_results)}."}}'
        }
        await asyncio.sleep(2)

        # collect from vectorstore


        yield {
            "event": "message",
            "id": str(3),
            "data": f'{{"step": 3, "detail": "Collecting {len(records)}."}}'
        }
        elements = builder.answer(question)
        process.elements.extend(elements)
        process.save()
        await asyncio.sleep(2)
        yield {
            "event": "message",
            "id": str(4),
            "data": f'{{"step": 4, "detail": "Produced {len(elements)}."}}'
        }
        await asyncio.sleep(2)
        yield {
            "event": "message",
            "id": str(5),
            "data": f'{{"step": 5, "detail": "Collected {len(records)}."}}'
        }
        await asyncio.sleep(2)
        yield {
            "event": "message",
            "id": str(6),
            "data": f'{{"step": 6, "detail": "Collected {len(records)}."}}'
        }
        print("Done")
    
    return EventSourceResponse(event_generator(db, process_id))

@app.post("/process")
async def process(request: Request):
    data = await request.json()
    question = data.get("question")
    uid = ObjectId()
    new_process = Process(uid, question)
    new_process.save()
    return {"process_id": str(uid), "question": question, "elements": []}

@app.get("/view/{process_id:str}")
async def read_root(request: Request, process_id: str, db: Session = Depends(get_db)):
    initial = Process.get(ObjectId(process_id))
    return initial.to_dict()


# @app.get("/")
# async def read_root(request: Request, db: Session = Depends(get_db)):
#     companies = await get_companies(db)
#     context = {
#         "request": request,  # Required for Jinja2 to work with FastAPI
#         "title": "ChainWise",
#         "companies": companies
#     }
#     return templates.TemplateResponse("index.html", context)
