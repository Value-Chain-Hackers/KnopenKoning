import warnings
warnings.filterwarnings("ignore")

from logging import getLogger
log = getLogger(__name__)

from config import MODEL_NAME, EMBEDDING_MODEL
from langchain_chroma import Chroma
from langchain.indexes import SQLRecordManager, index
import os
import glob
from tqdm import tqdm
from langchain_core.prompts import PromptTemplate
from utils.build_knowledge import cikLookup
from utils.extract_knowledge import extract_text_from_pdf, get_huggingface_model, get_records_manager, split_text_into_documents

from db.session import engine, SessionLocal, Base
from db import Company
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
import json
from langchain_community.llms.ollama import Ollama

object_types = [
    "raw-material", "supplier", "customer", "manufacting plant",
    "warehouse", "distribution center", "store", "office", "factory",
    "equipment", "service",
    "product-line", "product", "brand",
    "partner", "competitor", "subsidiary", 
    "material", "ingredient", "component", "commodity", 
#     "division", "department", "team", "group", "organization", 
#    "authority", "regulator", "industry", "sector", "segment",
    "location" ,"city", "region", "country", "continent"
]
predicates = [
    'uses', 'has', 'owns', 'produces', 'makes', 'sells', 'supplies',
    'is-a', 'is-located-in', 'is-part-of', 'contains', 'partners-with', 'collaborates-with',
    'operates-in',
    #'acquires',
    #'employs', 'manufactures', 'distributes'
]

knowledge_build_prompt = PromptTemplate.from_template(f"""\
You are a **Knowledge Extraction Agent**

Your task is to build a comprehensive knowledge graph from the provided text. 
The knowledge graph should capture all relevant information based on the specified question : {{question}} 
Adhere strictly to the following guidelines:

1. **Extraction Format**: Use the specified JSON format for each extracted triplet. Each triplet should include:
    - `subject`: The entity that is the source of a relationship.
    - `predicate`: The relationship type: {', '.join(predicates)}.
    - `object`: The entity that is the target of the relationship.
    - `object-type`: The type of the entity, chosen from the predefined list: {', '.join(object_types)}.
    - `more-info`: Additional details about the object. Include information like descriptions, full addresses, links, or any other relevant details.
    DO NOT include any additional fields or change the field names.
    DO ALWAYS include the `more-info` field, even if it is empty.
                                                          
2. **Predicates and Object Types**:
    - **Predicates**: {', '.join(predicates)}.
    - **Object Types**: {', '.join(object_types)}.
    DO ONLY use the provided predicates and object types.
                                                          
3. **Relevance**: Extract only the information relevant to the question. 
    DO NOT add irrelevant details and ensure that all extracted information is directly present in the text.

4. **Object Details**: Keep the object field concise (2-3 words). 
    DO USE the `more-info` field for additional descriptions or specifics.

5. **Accuracy and Completeness**: Ensure that all extracted information is accurate and complete. 
    DO double-check for any missing relevant details.

6. **Output**: The output should be valid JSON format, as specified.
    DO NOT invert relation directions (e.g: a plant, office, warehous is 'is-located-in' the object)
    DO NOT include additional explanations or notes outside the JSON structure.
    DO NOT group several relations nodes into one, make individual nodes for each object(e.g: each country, commodity, supplier).
    DO Normalize entity names. DO NOT use designations such as 'The Company', DO replace them with the real company name.
---

### Example Template:
```json
[
  {{{{
    "subject": "...",       // the source node of the relationship
    "predicate": "...",     // one of {', '.join(predicates)}
    "object": "...",        // the target node of the relationship
    "object-type": "...",   // one of {', '.join(object_types)}
    "more-info": "..."
  }}}},
  ...
]
```

### Task:

**Context**:
```
{{context}}
```

**Question**:
```
{{question}}
```

---

DO follow these instructions meticulously to extract and construct the knowledge graph. 
DO verify the accuracy and relevance of your extractions are critical to the success of this task.
    """)

hf = get_huggingface_model(EMBEDDING_MODEL)

def get_chain(namespace, rag_folder):
    llm = Ollama(model=MODEL_NAME, num_ctx=4096, num_predict=2048, temperature=.5)
    chain = (
        {"context": get_retriever(namespace, rag_folder), "question": RunnablePassthrough()}
        | knowledge_build_prompt
        | llm
        | JsonOutputParser()
    )
    return chain

def get_retriever(namespace, rag_folder):
    chroma = Chroma(namespace,  embedding_function=hf, persist_directory=rag_folder)
    retriever = chroma.as_retriever(search_kwargs={"k": 5})
    return retriever

def build_knowledge(company):
    if not os.path.exists("./.cache"):
        os.makedirs("./.cache")
    #print(f"Building knowledge for {pdf_file}")
    namespace = f"rags-docs-{company.company_name}".replace(" ","").replace("-","")
    rag_folder = f"./.cache/{company.company_name}/chroma/docs/"
    chain = get_chain(namespace, rag_folder)

    #print(f"Getting records manager for namespace {namespace} in db")
    topics = json.load(open("./data/questions.json", "r"))
    # Hack to only use the suppliers questions
    #topics = {"suppliers": topics["suppliers"]}
    #print(f"Loaded {len(topics)} topics")
    #print(f"Extracting text from {pdf_file}")
    

    for topic in tqdm(topics, desc=f"Processing Topics for {company.company_name}", unit="topic", leave=False, position=1):
        relationships = []
        rejected = []
        for question in tqdm(topics[topic], desc=f"Processing questions in {topic}", unit="question", leave=False, position=2):
            #print(f"Question: {question}")
            try:
                result = chain.invoke(question)
            except Exception as e:
                print('error', e)
                continue

            for r in result:
                if r.get("object-type", None) is None:
                    rejected.append(r)
                    continue

                # if the object type is not in the list of object types, skip it
                if r["object-type"] not in object_types:
                    rejected.append(r)
                    continue

                # if "," in r["object"]:
                #     objects = r["object"].split(",")
                #     for obj in objects:
                #         relationships.append({"subject": r["subject"], "predicate": r["predicate"], "object": obj, "object-type": r["object-type"], "more-info": r.get("more-info","")})
                # else:
                relationships.append(r)
    
            with open(f"./data/{company.company_name}/knowledge_{topic}.json","w") as out:
                json.dump(relationships, out, indent=4)
        with open(f"./data/{company.company_name}/knowledge_{topic}_rejected.json","w") as out:
            json.dump(rejected, out, indent=4)

if __name__ == "__main__":
    #cik = cikLookup("Nestle")
    #print(cik)
    if not os.path.exists("./.cache"):
        os.makedirs("./.cache")
    companies = SessionLocal().query(Company).all()
    for company in tqdm(companies, desc="Building Knowledge Base", unit="RAG", leave=False, position=0):
        build_knowledge(company)