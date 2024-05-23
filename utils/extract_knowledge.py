import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.llms.ollama import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain.indexes import SQLRecordManager, index
import os

knowledge_extraction_prompt = PromptTemplate.from_template("""\
Please proceed to knowledge extraction from the provided text. Focus on the following aspects:
    1. Identify the key suppliers and customers of the company.
    2. Identify the raw materials used by the company and their sources.
    3. Idenitfy the locations of the company's manufacturing plants.
    4. Identify the routes used by the company to distribute its products.
    5. Identify the sustainability practices of the company.
    6. Identify the use of poluants and environmentally impactful materials.
    7. Identify the company's carbon footprint and energy consumption.
    8. Identify the company's waste management practices.
    9. Identify the company's recycling practices.
    10. Identify the company's water usage and management practices.
    11. Identify the company's social responsibility practices.
    12. Identify the company's labor practices.
    13. Identify the company's human rights practices.

If none of the above aspects are present in the text, please respond with "Not relevant".
Keep your answers concise and to the point. 
Do not include any irrelevant information, nor any information that is not present in the text.
-----
Context:
                                      
{chunk}

----- 
""")

knowledge_summary_prompt = PromptTemplate.from_template("""\
Please proceed to summarizing the knowledge extracted from the text.
Remove all duplicate information and keep the summary concise.
Make sure you retain all the key information.
-----
Context:
                                      
{chunk}

-----                                                     
""")

knowledge_build_prompt = PromptTemplate.from_template("""\
Given the knowledge extracted from the text, please proceed to build a knowledge graph.
The knowledge graph should include all the key information extracted from the text.
Create triples in the following format:
    1. Entity1 -> Relation -> Entity2
    2. Entity1 -> Relation -> Value
    3. Entity1 -> Attribute -> Value
DO NOT include any irrelevant information, nor any information that is not present in the text.
DO ONLY use json-ld format as output.
------
Context:
                                    
{chunk}

------
""")

def split_text_into_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size=4000,
        chunk_overlap=256,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_text(text)

def split_text_into_documents(text, chunk_size=512, chunk_overlap=64):
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    doc = Document(text)
    doc.metadata["key"] = "doc1"
    all_docs = text_splitter.split_documents([doc])
    splitcount = 0
    for sdoc in all_docs:
        sdoc.metadata["key"] = doc.metadata["key"] + f"-split{splitcount}"
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

def extract_all_knowledge_from_pdf(pdf_path, output_path):
    text = extract_text_from_pdf(pdf_path)
    chunks = split_text_into_chunks(text)
    llm = Ollama(model="phi3:latest", num_ctx=4096, num_predict=2048, temperature=0.1)
    chain = knowledge_extraction_prompt | llm | StrOutputParser()
    knowledge = []
    with open(output_path, "a", encoding='utf-8') as f:
        for chunk in chunks:
            response = chain.invoke({"chunk": chunk})
            knowledge.append(response)
            f.write(response + "\n")
            f.write("-----\n")

    return knowledge

def summarize_all_text(text, output_path):
    chunks = split_text_into_chunks(text)
    llm = Ollama(model="phi3:latest", num_ctx=4096, num_predict=2048, temperature=0.1)
    chain = knowledge_summary_prompt | llm | StrOutputParser()
    knowledge = []
    with open(output_path, "a", encoding='utf-8') as f:
        for chunk in chunks:
            response = chain.invoke({"chunk": chunk})
            knowledge.append(response)
    
    return knowledge

def extract_knowledge_graph(text, output_path):
    chunks = split_text_into_chunks(text)
    llm = Ollama(model="phi3:latest", num_ctx=4096, num_predict=2048, temperature=0.1)
    chain = knowledge_build_prompt | llm | StrOutputParser()
    knowledge = []
    with open(output_path, "a", encoding='utf-8') as f:
        for chunk in chunks:
            response = chain.invoke({"chunk": chunk})
            knowledge.append(response)
    return knowledge


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
    