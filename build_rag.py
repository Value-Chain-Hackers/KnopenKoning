from langchain_chroma import Chroma
from langchain.indexes import SQLRecordManager, index
import os
from tqdm import tqdm

from utils.extract_knowledge import extract_text_from_pdf, get_huggingface_model, get_records_manager, split_text_into_documents, extract_documents_from_pdf

def build_rag():
    if not os.path.exists("./.cache"):
        os.makedirs("./.cache")

    namespace = f"rags/docs"

    model_name = "BAAI/bge-base-en-v1.5"
    print(f"Loading Hugging Face model {model_name}")
    hf = get_huggingface_model(model_name)


    pdf_files = ["./data/cocacola.pdf", "./data/unilever.pdf", "./data/ikea.pdf", "./data/albertheijn.pdf"]
    for pdf_file in pdf_files:
        docs = []
        namespace = f"rags/docs/{pdf_file}".replace("/","").replace(".","")
        print(f"Getting records manager for namespace {namespace} in db")
        record_manager = get_records_manager("./.cache/record_manager_cache.sql", namespace + pdf_file)
        chroma = Chroma(namespace,  embedding_function=hf, persist_directory="./.cache/chroma/docs/"+ pdf_file+"/")

        parts = extract_documents_from_pdf(pdf_file)
        print(f"Extracted {len(parts)} splits of pdf docs from {pdf_file}")
        docs.extend(parts)
        print(parts[0].metadata)
        print(f"Extracted {len(docs)} splits of pdf docs")

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