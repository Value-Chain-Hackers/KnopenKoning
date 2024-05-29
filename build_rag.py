import warnings
warnings.filterwarnings("ignore")
import os
import glob

from logging import getLogger
log = getLogger(__name__)

from langchain_chroma import Chroma
from langchain.indexes import SQLRecordManager, index
from db.session import engine, SessionLocal, Base
from db import Company
from tqdm import tqdm
from config import EMBEDDING_MODEL, RAG_BATCH_SIZE
from utils.extract_knowledge import extract_text_from_pdf, get_huggingface_model, get_records_manager, split_text_into_documents, extract_documents_from_pdf

def build_rag():
    if not os.path.exists("./.cache"):
        os.makedirs("./.cache")
    hf = get_huggingface_model(EMBEDDING_MODEL)
    companies = SessionLocal().query(Company).all()
    for company in tqdm(companies, desc="Building RAG Indexes", unit="RAG", leave=False, position=0):
        namespace = f"rags-docs-{company.company_name}".replace(" ","").replace("-","")
        rag_folder = f"./.cache/{company.company_name}/chroma/docs/"
        if not os.path.exists(rag_folder):
            os.makedirs(rag_folder)

        pdf_files = glob.glob(f"./data/{company.company_name}/**/*.pdf", recursive=True)
        log.info(f"Found {len(pdf_files)} pdf files for {company.company_name}") 
        
        all_docs = []       
        for pdf_file in tqdm(pdf_files, desc=f"Extracting Text from PDF's of {company.company_name}", unit="pdf file", leave=False, position=1):
            pdf_file = pdf_file.replace("\\", "/")
            parts = extract_documents_from_pdf(pdf_file)
            log.info(f"Extracted {len(parts)} splits of pdf docs from {pdf_file}")
            all_docs.extend(parts)
        
        record_manager = get_records_manager(namespace)
        chroma = Chroma(namespace,  embedding_function=hf, persist_directory=rag_folder)
        log.info(f"Indexing {len(all_docs)} splits of {len(pdf_files)} pdf about {company.company_name}")

        # index the documents by chunking them into smaller parts
        for i in tqdm(range(0, len(all_docs), RAG_BATCH_SIZE), desc=f"Indexing {company.company_name} documents", unit="Batch", leave=False, position=1):
            log.info(f"Indexing Batch {i} to {i+RAG_BATCH_SIZE} documents")
            docs = all_docs[i:i+RAG_BATCH_SIZE]
            indexing = index(
                docs,
                record_manager,
                chroma,
                cleanup='incremental',
                source_id_key="key",
            )
            log.info(f"Indexed {indexing} documents for {company.company_name}")

if __name__ == "__main__":
    build_rag()