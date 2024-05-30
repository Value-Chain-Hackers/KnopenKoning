import warnings
warnings.filterwarnings("ignore")

from logging import getLogger
log = getLogger(__name__)

from config import MODEL_NAME, EMBEDDING_MODEL
from langchain_chroma import Chroma
from langchain.indexes import SQLRecordManager, index
import os
import glob
from tqdm import tqdm
from langchain_core.prompts import PromptTemplate
from utils.build_knowledge import cikLookup
from utils.extract_knowledge import extract_text_from_pdf, get_huggingface_model, get_records_manager, split_text_into_documents

from db.session import engine, SessionLocal, Base
from db import Company
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
import json
from langchain_community.llms.ollama import Ollama
from jobs.information_gathering import collect_base_information
if __name__ == "__main__":
    #cik = cikLookup("Nestle")
    #print(cik)
    if not os.path.exists("./.cache"):
        os.makedirs("./.cache")
    db = SessionLocal()
    companies = db.query(Company).all()
    for company in tqdm(companies, desc="Building Knowledge Base", unit="company", leave=False, position=0):
        collect_base_information(company.company_name, db)