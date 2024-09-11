import os



MODEL_NAME = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://ollama:11434")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama:11434")
OLLAMA_MODEL = MODEL_NAME
#MODEL_NAME = "mistral:latest"
#MODEL_NAME = "mixtral:8x7b"
#MODEL_NAME = "mixtral:8x7b"
#MODEL_NAME = "phi3:14b-medium-128k-instruct-q6_K"
#MODEL_NAME = "command-r:latest"
#MODEL_NAME = "dbrx:latest"
#MODEL_NAME = "command-r-plus"
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
NER_MODEL = "dslim/bert-large-NER"
CUDA_ENABLED = True

RAG_BATCH_SIZE = 32

RECORDS_DATABASE = ".cache/record_manager_cache.db"

KNOWLEDGE_EXRTACTION_MODEL = "solar:latest"