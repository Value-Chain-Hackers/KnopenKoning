# main.py
import asyncio
from typing import Any, Dict, List, Optional
import uuid
import time
from langchain_core.messages import BaseMessage
import ollama
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
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
from langserve import add_routes
from langchain_community.chat_models.ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate

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

model = ChatOllama(model="phi3:latest")
prompt = ChatPromptTemplate.from_template("tell me a joke about {topic}")
add_routes(
    app,
    prompt | model,
    path="/joke",
    playground_type="default"
)



@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    print(file.filename)
    with open(file.filename, "wb") as f:
        f.write(contents)
    return {"filename": file.filename}

from db import Company, Website, Records, Agents, Tasks, Tools, Crews
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

@app.get("/view/{company:str}/")
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

from langchain_core.agents import AgentAction, AgentFinish, AgentStep
from crewai.tasks.task_output import TaskOutput
from langchain_core.callbacks import BaseCallbackHandler, BaseCallbackManager


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

    llm = ChatOllama(model="mistral:latest", num_ctx=4096, num_predict=2048, temperature=1)
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
