#MODEL_NAME = "mistral:latest"
MODEL_NAME = "mixtral:8x7b"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
NER_MODEL = "dslim/bert-large-NER"
CUDA_ENABLED = True

RAG_BATCH_SIZE = 32

RECORDS_DATABASE = ".cache/record_manager_cache.db"