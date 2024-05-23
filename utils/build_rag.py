from langchain_chroma import Chroma
from langchain.indexes import SQLRecordManager, index
import os
import glob
from extract_knowledge import extract_text_from_pdf, split_text_into_documents

from tqdm import tqdm
tqdm()

def get_records_manager(database, namespace):

    # if the file exists, load the record manager from the file
    if os.path.exists(database):
        record_manager = SQLRecordManager(
            namespace, db_url=f"sqlite:///{database}"
        )
        return record_manager
    else:
        record_manager = SQLRecordManager(
            namespace, db_url=f"sqlite:///{database}"
        )
        record_manager.create_schema()

def get_huggingface_model(model_name):
    from langchain_community.embeddings import HuggingFaceEmbeddings
    model_kwargs =  {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': False}
    hf = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    return hf
    

if not os.path.exists("./.cache"):
    os.makedirs("./.cache")

namespace = f"rags/docs"

model_name = "BAAI/bge-base-en-v1.5"
print(f"Loading Hugging Face model {model_name}")
hf = get_huggingface_model(model_name)

print(f"Getting records manager for namespace {namespace} in db")
record_manager = get_records_manager("./.cache/record_manager_cache.sql", namespace)


chroma = Chroma("docs",  embedding_function=hf, persist_directory="./.cache/chroma/docs")

docs = extract_text_from_pdf("unilever-annual-report-and-accounts-2023.pdf")
docs = split_text_into_documents(docs)

print(f"Indexing {len(docs)} splits of Ollama docs")

indexing = index(
    docs,
    record_manager,
    chroma,
    cleanup='incremental',
    source_id_key="key",
)
print(indexing)