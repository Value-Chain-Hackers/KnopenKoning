import concurrent.futures
from config import MODEL_NAME, EMBEDDING_MODEL, OLLAMA_API_URL
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.llms.ollama import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain.indexes import SQLRecordManager, index
import os
import re
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from config import MODEL_NAME, EMBEDDING_MODEL, CUDA_ENABLED, RECORDS_DATABASE

def split_text_into_chunks(text, chunk_size=512, chunk_overlap=64):
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_text(text)

def extract_documents_from_pdf(pdf_path, chunk_size=512, chunk_overlap=64):
    document = fitz.open(pdf_path)
    basename = os.path.basename(pdf_path).replace(".pdf", "")
    all_docs = []
    # Iterate through each page
    for page_num in range(len(document)):
        page = document.load_page(page_num)  # Load the page
        text = page.get_text()  # Extract text from the page
        docs = split_text_into_documents(text, key=basename, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for doc in docs:
            doc.metadata["source"] = pdf_path
            doc.metadata["page"] = page_num
        all_docs.extend(docs)
    return all_docs

def split_text_into_documents(text, key, chunk_size=512, chunk_overlap=64):
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    doc = Document(text)
    doc.metadata["key"] = key
    all_docs = text_splitter.split_documents([doc])
    splitcount = 0
    for sdoc in all_docs:
        sdoc.metadata["key"] = doc.metadata["key"] + f"-split{splitcount}"
        sdoc.metadata["parent_key"] = doc.metadata["key"]
        sdoc.metadata["start"] = splitcount * chunk_size
        sdoc.metadata["end"] = (splitcount + 1) * chunk_size
        sdoc.metadata["length"] = len(sdoc.text)
        sdoc.metadata["split"] = splitcount
        splitcount += 1
    return all_docs

def extract_text_from_pdf(pdf_path):
    # Open the PDF file
    document = fitz.open(pdf_path)
    text = ""
    
    # Iterate through each page
    for page_num in range(len(document)):
        page = document.load_page(page_num)  # Load the page
        text += page.get_text()  # Extract text from the page
    
    return text


def get_records_manager(namespace, database_filename = RECORDS_DATABASE) -> SQLRecordManager:

    # if the file exists, load the record manager from the file
    if os.path.exists(database_filename):
        record_manager = SQLRecordManager(
            namespace, db_url=f"sqlite:///{database_filename}"
        )
        return record_manager
    else:
        record_manager = SQLRecordManager(
            namespace, db_url=f"sqlite:///{database_filename}"
        )
        try:
            record_manager.create_schema()
        except:
            pass
        return record_manager

def get_huggingface_model(model_name):
    from langchain_huggingface import HuggingFaceEmbeddings
    if CUDA_ENABLED:
        model_kwargs =  {'device': 'cuda'}
    else:
        model_kwargs =  {'device': 'cpu'}
    print(f"Loading Hugging Face model {model_name}")
    encode_kwargs = {'normalize_embeddings': False}
    hf = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    return hf
    

from abc import ABC, abstractmethod

class CallbackManager(ABC):
    @abstractmethod
    def on_start(self):
        """Called when the process starts."""
        pass

    @abstractmethod
    def on_finish(self):
        """Called when the process finishes."""
        pass

    @abstractmethod
    def on_error(self, error):
        """Called when an error occurs.
        
        Args:
            error (Exception): The exception that was raised.
        """
        pass

    @abstractmethod
    def on_progress(self, progress):
        """Called to report progress.
        
        Args:
            progress (float): The current progress as a percentage.
        """
        pass

    @abstractmethod
    def on_step_starting(self, phase, step, chunk_id, data):
        """Called once a preprocess step has been completed.
        
        Args:
            phase (str): PreProcess, Extract, Validate
            step (int): The number of the step/pass.
            chunk_id: The Id if the chunk being processed.
            data (str): The actual text resulting from this stp.
        """
        pass

    @abstractmethod
    def on_step_completed(self, phase, step, chunk_id, data):
        """Called once a preprocess step has been completed.
        
        Args:
            phase (str): PreProcess, Extract, Validate
            step (int): The number of the step/pass.
            chunk_id: The Id if the chunk being processed.
            data (str): The actual text resulting from this stp.
        """
       
        pass

    @abstractmethod
    def on_tuple_created(self, tuple):
        """Called once a node is ready to integrate the graph"""
        pass

class NullCallbackManager(CallbackManager):
    def __init__(self):
        super().__init__()
    def on_start(self):
        pass

    def on_finish(self):
        pass

    def on_error(self, error):
        pass

    def on_progress(self, progress):
        pass

    def on_step_starting(self, phase, step, chunk_id, data):
        pass

    def on_step_completed(self, phase, step, chunk_id, data):
        pass

    def on_tuple_created(self, tuple):
        pass
class FileDumpCallbackManager(NullCallbackManager):
    def __init__(self, workdir):
        super().__init__()
        self.workdir = workdir
        if not os.path.exists(workdir):
            os.makedirs(workdir)
  
    def on_step_completed(self, phase, step, chunk_id, data):
        """Called once a preprocess step has been completed.
        
        Args:
            phase (str): PreProcess, Extract, Validate
            step (int): The number of the step/pass.
            chunk_id: The Id if the chunk being processed.
            data (str): The actual text resulting from this stp.
        """
        with open(f"{self.workdir}/tmp_{phase}_{step}.dump", "w", encoding="utf-8") as file:
            print(phase, step, len(data))
            file.write(data)
        pass

    def on_tuple_created(self, tuple):
        """Called once a node is ready to integrate the graph"""
        pass


prompt = PromptTemplate.from_template("""\

## Input:
                                                      
{context}

""")

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import ConversationChain
from langchain_community.memory.kg import ConversationKGMemory
from langchain_community.callbacks.labelstudio_callback import (
    LabelStudioCallbackHandler,
)
from rdflib import Graph
import pathlib
import json
class KnowledgeExtractor():
    _ontology_graph = Graph()
    _raw_chunks: list[str] = []
    _pre_processed_chunks: list[str] = []
    _pre_process_chain = None
    _prompts = {}
    _llms = {}
    _extraction_callbacks: CallbackManager
    _num_workers = 1
    _progressbars = True
    _ontology :str = None
    _code_block_pattern = r"```(RDF|rdf|turtle|ttl|xml)\s+([\s\S]+?)\s+```"
    _workdir: str = None

    def __init__(self, model, num_workers = 6, chunk_size = 512, chunk_size_overlap = 64, work_dir = None, extraction_callbacks: CallbackManager = NullCallbackManager()) -> None:
        self._workdir = work_dir   

        if(work_dir and not pathlib.Path(work_dir).exists()):
            pathlib.Path(work_dir).mkdir(parents=True, exist_ok=True)
    
        self.chunk_size = chunk_size
        self.chunk_size_overlap = chunk_size_overlap
        self._extraction_callbacks = extraction_callbacks

        self._num_workers = num_workers
        self.model = model
        self.load_ontology("./data/supplychain.ttl")

        self.load_prompts()
        from langfuse.callback import CallbackHandler
        langfuse_handler = CallbackHandler( secret_key="sk-lf-fe133c9a-1387-4680-920c-ab01879f8e45",
        public_key="pk-lf-d5dec24a-00a7-4006-adb8-27ab0b749ac9",
        host="http://localhost:3000")

        self.store  = {}

        self.llm_preprocess = Ollama(model=self.model, base_url=OLLAMA_API_URL, 
            temperature=0.2, num_ctx=chunk_size, num_predict=chunk_size, system=self._prompts["preprocess"], 
            callbacks=[langfuse_handler], tags=["preprocess"])#, callbacks=[LabelStudioCallbackHandler(project_name="xpreprocess")])
        
        self.llm_extract = Ollama(model="llama3:8b", base_url=OLLAMA_API_URL, 
            temperature=0.2, num_ctx=chunk_size, num_predict=chunk_size, system=self._prompts["extraction"], 
            callbacks=[langfuse_handler], tags=["extraction"])#, callbacks=[LabelStudioCallbackHandler(project_name="xextraction")])
        
        self.llm_validate = Ollama(model=self.model, base_url=OLLAMA_API_URL, 
            temperature=0.2, num_ctx=chunk_size, num_predict=chunk_size, system=self._prompts["validation"], 
            callbacks=[langfuse_handler], tags=["validation"])#, callbacks=[LabelStudioCallbackHandler(project_name="xvalidation")])
        
        self._pre_process_chain = prompt | self.llm_preprocess
        
        self.embeddings = get_huggingface_model(EMBEDDING_MODEL)
      

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def __progress(self, iterable, **kwargs):
        if(self._progressbars):
            from tqdm import tqdm 
            return iter(tqdm(iterable, **kwargs))
        else:
            return iter(iterable)

    def load_prompts(self):
        knowledge_preprocess = ""
        with open("prompts\\knowledge_preprocess.md","r", encoding="utf-8") as f:
            knowledge_preprocess = f.read()
        self._prompts["preprocess"] = knowledge_preprocess

        knowledge_extraction = ""
        with open("prompts\\knowledge_extraction.md","r", encoding="utf-8") as f:
            knowledge_extraction = f.read()
        self._prompts["extraction"] = knowledge_extraction

        knowledge_validation = ""
        with open("prompts\\knowledge_validate.md","r", encoding="utf-8") as f:
            knowledge_validation = f.read()
        self._prompts["validation"] = knowledge_validation

        return self._prompts

    def load_ontology(self, file_path):
        with open(file_path,"r", encoding="utf-8") as f:
            self._ontology = f.read()
        self._ontology_graph.parse(data=self._ontology)

    def chunkify(self, large_text, chunk_size = 512, chunk_size_overlap = 64):
        return split_text_into_chunks(large_text, chunk_size=chunk_size, chunk_overlap=chunk_size_overlap)[0:20]

    def _do_preprocess(self, id, text):
        return self._pre_process_chain.invoke({"context": text},config={"tags":[str(id)]})
    
    def preprocess(self, large_text):
        print(f'Initial text length {len(large_text)}')
        self._raw_chunks = self.chunkify(large_text, self.chunk_size, self.chunk_size_overlap)
        print(f'Initial Raw Chunks {len(self._raw_chunks)} using chunk size:{self.chunk_size} with overlap {self.chunk_size_overlap}.')
        pre_processed_chunks = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self._num_workers) as executor:
            futures = []

            for id, text in enumerate(self._raw_chunks):
                futures.append(executor.submit(self._do_preprocess, id, text))
            
            for future in self.__progress(concurrent.futures.as_completed(futures), desc=f"Processing raw chunks.", unit=" chunk", total=len(futures)):
                pre_processed_chunks.append(future.result())

        executor.shutdown()

        self._pre_processed_chunks = pre_processed_chunks

        all_preprocess = "\n".join(self._pre_processed_chunks)
        print(f'Pre-processed text size {len(all_preprocess)} reduction {len(all_preprocess)/len(large_text)}')

        self._pre_processed_chunks = self.chunkify(all_preprocess, self.chunk_size, self.chunk_size_overlap)
        print(f'Pre-processed chunks {len(self._pre_processed_chunks)} using chunk size:{self.chunk_size} with overlap {self.chunk_size_overlap}.')

        self._extraction_callbacks.on_step_completed("preprocess", 1, None, "\n".join(self._pre_processed_chunks))

        new_chunks = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self._num_workers) as executor:
            futures = []

            for id, text in enumerate(self._raw_chunks):
                futures.append(executor.submit(self._do_preprocess, id, text))
            
            for future in self.__progress(concurrent.futures.as_completed(futures), desc=f"Fusion pre-processed chunks", unit=" chunk", total=len(futures)):
                new_chunks.append(future.result())
        
        executor.shutdown()

        all_preprocess = "\n".join(new_chunks)

        self._pre_processed_chunks = new_chunks

        print(f'Final preprocessed text length {len(all_preprocess)} reduction {len(all_preprocess)/len(large_text)}')
        
        self._extraction_callbacks.on_step_completed("preprocess", 2, None, all_preprocess)

        
        splitter = MarkdownHeaderTextSplitter([
            ('#', "Top"),
            ('##', "Section"),
            ('###', "SubSection"),
        ])

        self.splits = splitter.split_text(all_preprocess)

    def extract(self):
        vector_database = Chroma(embedding_function=self.embeddings)
        for index in self.__progress(range(0, len(self._raw_chunks), 16), desc="Adding document batches to vectorstore"):
            vector_database.add_texts(self._raw_chunks[index:index + 16])
        retriever = vector_database.as_retriever()
        prompt = PromptTemplate.from_template("""\
## Documents:
{documents}

## Context:
{context}

""")
        def format_docs(docs):
            return [doc.page_content + '\n\n' for doc in docs]

        self._extract_chain = {"documents": retriever | format_docs, "context": RunnablePassthrough()} | prompt | self.llm_extract 

        all_extracted = []
        self.all_extracted_nodes = []
        for id, split in enumerate(self.splits):
            output = self._extract_chain.invoke(split.page_content)
            print(output)
            self.all_extracted_nodes.append(output)
          
            # matches = re.findall(self._code_block_pattern, output)
            # if not matches or len(matches) == 0:
            #     print("No codeblock found")
            #     print(output[0:250])
            #     print(output[-250:])

            # self._extraction_callbacks.on_step_completed("extraction", 1, id, output)
            # new_entities = []
            # for match in matches:
            #     language, code = match
            #     # remove all prefixes from the extracted data
            #     all_extracted.append(code)
            #     code = re.sub(r"@prefix.*\n", "", code)
            #     entities = code.strip('`').split("\n\n")
            #     if isinstance(entities, str):
            #         entities = [entities]
            #     new_entities.extend(entities)
            #     self.all_extracted_nodes.extend(entities)

        with open(f"{self._workdir}/extracted_nodes.txt", "w", encoding="utf-8") as file:
            json.dump(self.all_extracted_nodes, file)   

        print(F"Finished Extracting {len(self.all_extracted_nodes)} nodes")

