from langchain_chroma import Chroma
from langchain.indexes import SQLRecordManager, index
import os
from tqdm import tqdm

from utils.extract_knowledge import extract_text_from_pdf, get_huggingface_model, get_records_manager, split_text_into_documents

def build_rag():
    if not os.path.exists("./.cache"):
        os.makedirs("./.cache")

    namespace = f"rags/docs"

    model_name = "BAAI/bge-base-en-v1.5"
    print(f"Loading Hugging Face model {model_name}")
    hf = get_huggingface_model(model_name)

    print(f"Getting records manager for namespace {namespace} in db")
    record_manager = get_records_manager("./.cache/record_manager_cache.sql", namespace)


    chroma = Chroma("docs",  embedding_function=hf, persist_directory="./.cache/chroma/docs")

    docs = extract_text_from_pdf("./data/unilever-annual-report-and-accounts-2023.pdf")
    print(f"Extracted {len(docs)} splits of pdf docs")
    docs = split_text_into_documents(docs)

    print(f"Indexing {len(docs)} splits of pdf docs")

    indexing = index(
        docs,
        record_manager,
        chroma,
        cleanup='incremental',
        source_id_key="key",
    )
    print(indexing)

if __name__ == "__main__":
    build_rag()