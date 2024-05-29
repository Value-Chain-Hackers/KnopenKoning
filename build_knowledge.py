import warnings
warnings.filterwarnings("ignore")

from config import MODEL_NAME, EMBEDDING_MODEL
from langchain_chroma import Chroma
from langchain.indexes import SQLRecordManager, index
import os
from tqdm import tqdm
from langchain_core.prompts import PromptTemplate
from utils.build_knowledge import cikLookup
from utils.extract_knowledge import extract_text_from_pdf, get_huggingface_model, get_records_manager, split_text_into_documents
from db.session import engine, SessionLocal, Base
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
import json
from langchain_community.llms.ollama import Ollama
knowledge_build_prompt = PromptTemplate.from_template("""\
You are a **Knowledge Extraction Agent**

Your task is to build a comprehensive knowledge graph from the provided text. The knowledge graph should capture all relevant information based on the specified question. Adhere strictly to the following guidelines:

1. **Extraction Format**: Use the specified JSON format for each extracted triplet. Each triplet should include:
    - `subject`: The entity that performs or owns an action.
    - `predicate`: The relationship or action, chosen from the predefined list.
    - `object`: The entity that is affected by the action or relationship.
    - `object-type`: The type of the entity, chosen from the predefined list.
    - `more-info`: Additional details about the object. Include information like city, country, and descriptions, full addresses, links, or any other relevant details.
    DO NOT include any additional fields or change the field names.
    DO ALWAYS include the `more-info` field, even if it is empty.
                                                          
2. **Predicates and Object Types**:
    - **Predicates**: 'uses', 'is-a', 'is-located-in', 'is-part-of', 'contains', 'makes', 'sells', 'supplies', 'produces', 'operates-in', 'has', 'owns', 'acquires', 'partners-with', 'collaborates-with', 'employs', 'manufactures', 'distributes'.
    - **Object Types**: 'raw-material', 'subsidiary', 'product', 'supplier', 'customer', 'plant', 'warehouse', 'store', 'office', 'factory', 'equipment', 'service', 'brand', 'partner', 'competitor', 'material', 'ingredient', 'component', 'product-line', 'division', 'department', 'team', 'group', 'organization',  'authority', 'regulator', 'industry', 'sector', 'segment', 'region', 'country', 'continent', 'world'.
    DO ONLY use the provided predicates and object types.
                                                          
3. **Relevance**: Extract only the information relevant to the question. 
    DO NOT add irrelevant details and ensure that all extracted information is directly present in the text.

4. **Object Details**: Keep the object field concise (2-3 words). 
    DO USE the `more-info` field for additional descriptions or specifics.

5. **Accuracy and Completeness**: Ensure that all extracted information is accurate and complete. 
    DO double-check for any missing relevant details.

6. **Output**: The output should be valid JSON format, as specified.
    DO NOT include additional explanations or notes outside the JSON structure.

---

### Example Template:
```json
[
  {{
    "subject": "...",
    "predicate": "...", 
    "object": "...",
    "object-type": "...", 
    "more-info": "..."
  }},
  ...
]
```

### Task:

**Context**:
```
{context}
```

**Question**:
```
{question}
```

---

DO follow these instructions meticulously to extract and construct the knowledge graph. 
DO verify the accuracy and relevance of your extractions are critical to the success of this task.
    """)

model_name = EMBEDDING_MODEL
print(f"Loading Hugging Face model {model_name}")
hf = get_huggingface_model(model_name)

def get_chain(namespace, pdf_file):
    llm = Ollama(model=MODEL_NAME, num_ctx=4096, num_predict=2048, temperature=0.1)
    chain = (
        {"context": get_retriever(namespace, pdf_file), "question": RunnablePassthrough()}
        | knowledge_build_prompt
        | llm
        | JsonOutputParser()
    )
    return chain

def get_retriever(namespace, pdf_file):
    chroma = Chroma(namespace,  embedding_function=hf, persist_directory=f"./.cache/chroma/docs/{pdf_file}")
    retriever = chroma.as_retriever(search_kwargs= {"k": 15})
    return retriever

def build_knowledge(pdf_file):
    if not os.path.exists("./.cache"):
        os.makedirs("./.cache")
    print(f"Building knowledge for {pdf_file}")
    namespace = f"rags/docs/{pdf_file}".replace("/","").replace(".","")
    chain = get_chain( namespace, pdf_file)

    print(f"Getting records manager for namespace {namespace} in db")
    topics = json.load(open("./data/questions.json", "r"))
    # Hack to only use the suppliers questions
    topics = {"suppliers": topics["suppliers"]}
    print(f"Loaded {len(topics)} topics")
    print(f"Extracting text from {pdf_file}")
    
    relationships = []
    for topic in tqdm(topics):
        for question in topics[topic]:
            print(f"Question: {question}")
            result = chain.invoke(question)
            relationships.extend(result)
    
        with open(f"{pdf_file.replace('.pdf','.json')}","w") as out:
            json.dump(relationships, out, indent=4)

if __name__ == "__main__":
    #cik = cikLookup("Nestle")
    #print(cik)
    if not os.path.exists("./.cache"):
        os.makedirs("./.cache")
    hf = get_huggingface_model(EMBEDDING_MODEL)
    companies = SessionLocal().query(Company).all()
    for company in tqdm(companies, desc="Building RAG Indexes", unit="RAG", leave=False, position=0):
        pdf_files = [
            "./data/alcoa.pdf",
            "./data/cocacola.pdf",
            "./data/danone.pdf",
            "./data/unilever.pdf", 
            "./data/ikea.pdf", 
            "./data/nestle.pdf",
            "./data/albertheijn.pdf",
            "./data/scania.pdf"
            ]
        for file in pdf_files:
            build_knowledge(file)