from config import MODEL_NAME, EMBEDDING_MODEL
from langchain_chroma import Chroma
from langchain.indexes import SQLRecordManager, index
import os
from tqdm import tqdm
from langchain_core.prompts import PromptTemplate
from utils.extract_knowledge import extract_text_from_pdf, get_huggingface_model, get_records_manager, split_text_into_documents

from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
import json
from langchain_community.llms.ollama import Ollama

def build_knowledge(pdf_file):
    if not os.path.exists("./.cache"):
        os.makedirs("./.cache")
    namespace = f"rags/docs/{pdf_file}".replace("/","").replace(".","")

    model_name = EMBEDDING_MODEL
    print(f"Loading Hugging Face model {model_name}")
    hf = get_huggingface_model(model_name)

    print(f"Getting records manager for namespace {namespace} in db")
    record_manager = get_records_manager("./.cache/record_manager_cache.sql", namespace)
    chroma = Chroma(namespace,  embedding_function=hf, persist_directory=f"./.cache/chroma/docs/{pdf_file}")
    retriever = chroma.as_retriever(search_kwargs= {"k": 15})
    topics = json.load(open("./data/questions.json", "r"))
    knowledge_build_prompt = PromptTemplate.from_template("""\
    You are a helpful AI assistant that has been tasked with building a knowledge graph from the text provided below.  
    Given the knowledge extracted from the text, please proceed to build a knowledge graph.
    The knowledge graph should include all the key information extracted from the text.
    DO NOT include any irrelevant information, nor any information that is not present in the text.
    ONLY extract information that is relevant to the question : {question}
    DO EXTRACT all the information and do not expect the user to complete blanks.
       DO NOT mention the documents or the source of the information, just extract the triplets, using this format:
    ```json
    [{{
    "subject": "...",
    "predicate": "...", // one of 'uses', 'owns', 'distributes', 'sources', 'contains', 'part-off', 'achieves', 'requires', 'depends', 'acquired', 'headquarters'
    "object": "..."
    "object-type": "..." // one of 'raw-material', 'offices', 'rearch-center', 'country', 'subsidiary', 'product', 'supplier', 'customer', 'plant'
    "more-info": "..."  // any additional information about the object
    }},
    ...
    ]
    ```
    DO keep object limited to 2-3 words, explain the object more in detail in the more-info field, do not include full addesses in the object field but set them in more-info.
    DO USE valid json format as specified above for the triplets. Do only specify city and or country when question are about locations do not include full addresses.
    DO ONLY use the above mentioned fields and values to express relations.
    Your mission is crtical to my company and the trust and credidibily, make sure you ansers are 100% truthful. If you fail to the task kittens will die in horrible manners.  
    ------
    Context:
                                        
    {context}

    ------
    """)


    llm = Ollama(model=MODEL_NAME, num_ctx=4096, num_predict=2048, temperature=0.1)
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | knowledge_build_prompt
        | llm
        | JsonOutputParser()
    )
    relationships = []
    for topic in topics:
        for question in topics[topic]:
            print(f"Question: {question}")
            result = chain.invoke(question)
            print(result)
            relationships.extend(result)
    
        with open(f"{pdf_file.replace('.pdf','.json')}","w") as out:
            json.dump(relationships, out, indent=4)

if __name__ == "__main__":
    
    pdf_files = ["./data/cocacola.pdf", "./data/unilever.pdf", "./data/ikea.pdf", "./data/albertheijn.pdf"]
    for file in pdf_files:
        build_knowledge(file)