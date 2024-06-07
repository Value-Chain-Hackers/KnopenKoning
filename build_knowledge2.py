import concurrent.futures
import json
from tqdm import tqdm
from glob import glob
import warnings
warnings.filterwarnings("ignore")

from langchain_community.llms.ollama import Ollama
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain.output_parsers.retry import RetryWithErrorOutputParser
from logging import getLogger
log = getLogger(__name__)
from utils.ollamapool import OllamaPool


from rdflib import Graph, Literal, BNode, Namespace, RDF, RDFS, OWL, ORG, URIRef

from config import EMBEDDING_MODEL
from utils.extract_knowledge import extract_text_from_pdf, split_text_into_chunks, split_text_into_documents, get_huggingface_model, KnowledgeExtractor, FileDumpCallbackManager

from langchain_chroma import Chroma
            
import re
import random
regex_json_codeblock = re.compile(r"```\n([^`]*)```", re.DOTALL)

from dotenv import load_dotenv
load_dotenv()

g = Graph()
with open("./data/supplychain.ttl","r", encoding="utf-8") as f:
    g.parse(f, format="turtle")

from config import KNOWLEDGE_EXRTACTION_MODEL
import os
# def process_chunk(pdfChunk, company_name, index, urls, model) -> Graph:
#     if not os.path.exists(f"./data/{company_name}/{model.replace(':','_')}"):
#         os.makedirs(f"./data/{company_name}/{model.replace(':','_')}")
#     dumpSteps = True
#     results = None

#     if dumpSteps:
#         with open(f"./data/{company_name}/{model.replace(':','_')}/chunk_{index}.txt", "w", encoding="utf-8") as out:
#             out.write(pdfChunk)

#     try:
#         url = random.choice(urls)
#         llm_preprocess = Ollama(model="llama3:8b", temperature=0, num_ctx=3000, num_predict=3000, 
#                 num_thread=4, base_url=url, system=knowledge_preprocess_system)
#         llm_extract = Ollama(model=model, temperature=0, num_ctx=3000, num_predict=3000, 
#                 num_thread=4, base_url=url, system=knowledge_extraction_system)
#         llm_validate = Ollama(model=model, temperature=0, num_ctx=3000, num_predict=3000, 
#                 num_thread=4, base_url=url, system=knowledge_validation_system)
        

#         pass1chain = prompt     | llm_preprocess 
#         kbChain = prompt        | llm_extract
#         validateChain = prompt  | llm_validate
        
#         output = pass1chain.invoke({
#             "context": pdfChunk
#         })
#         if dumpSteps:
#             with open(f"./data/{company_name}/{model.replace(':','_')}/preprocess_{index}.txt", "w", encoding="utf-8") as out:
#                 out.write(output)


#         output = kbChain.invoke({
#             "context": output,
#             "company_name": company_name
#         })

#         if dumpSteps:
#             with open(f"./data/{company_name}/{model.replace(':','_')}/extract_{index}.txt", "w", encoding="utf-8") as out:
#                 out.write(output)


#         output = validateChain.invoke({
#             "context": output,
#             "company_name": company_name
#         })

#         if dumpSteps:
#             with open(f"./data/{company_name}/{model.replace(':','_')}/validate_{index}.txt", "w", encoding="utf-8") as out:
#                 out.write(output)

#         if not output:
#             return None
        
#         match = regex_json_codeblock.search(output)
#         if match:
#             results = match.group(1).strip('`').strip()
#         else:
#             results = output.strip().strip('`').strip()

#         try:
#             prefixes = ""
#             for prefix, uri in g.namespaces():
#                 prefixes += f"@prefix {prefix}: <{uri}> .\n"

#             # if the first line starts with 'turle\n' remove it
#             results = re.sub(r"^(```)?turtle\n", "", results)

#             # remove all prefixes from the extracted data
#             results = re.sub(r"@prefix.*\n", "", results)

#             entities = results.strip('`').split("\n\n")
#             #print(f"Importing {len(entities)} entities from chunk {index} for {company_name}")

#             for i, entity in enumerate(entities):
#                 if not entity:
#                     continue
#                 try:
#                     g.parse(data=f"{prefixes}\n\n{entity.strip('`')}", format="turtle")
#                 except Exception as e:
#                     #print(f"Error parsing entity {i} in chunk {index}", e)
#                     with open(f"./data/{company_name}/{model.replace(':','_')}/error_{index}_{i}.ttl", "w", encoding="utf-8") as out:
#                         out.write(entity)
#                         out.write("\n\n")
#                         out.write(f"# Error parsing entity {i} in chunk {index}\n\n")
#                         out.write(f"# Error: {e}\n\n")
#                         out.write("\n\n")
#                     return None
#         except Exception as e:
#             with open(f"./data/{company_name}/{model.replace(':','_')}/error_{index}.ttl", "w", encoding="utf-8") as out:
#                 out.write(results)
#             #print(f"Error parsing chunk {index}", e)
#             return None
#         return g

#     except Exception as e:
#         print("---------------------------")
#         print(f"Error processing chuck: {index}",e)
#         print("---------------------------")
#     print(f"Processed {index} chunk, extracted {len(g.all_nodes())} lines of knowledge.")
#     return g


# def remove_duplicates(graph):
#     unique_triples = set(graph)
#     new_graph = Graph()
#     for triple in unique_triples:
#         new_graph.add(triple)
#     return new_graph

# def import_file_for_company(company, document, model):
#     import pandas as pd
#     from db import Company
#     import fitz
#     from db.session import SessionLocal

#     pool = OllamaPool()
#     pool.start(1,1)

#     db = SessionLocal()
#     company = db.query(Company).filter(Company.company_name == company).first()
#     file = fitz.open(document)
#     text = extract_text_from_pdf(file)
#     chunk_size = 7000
#     text_files = split_text_into_chunks(text, chunk_size, 256)
#     print(f"Processing {len(text_files)} chunks")
#     with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
#         futures = []

#         for i, pdfChunk in tqdm(enumerate(text_files), desc=f"Processing {company.company_name}", unit=" chunk", total=len(futures), leave=False, position=1):
#             futures.append(executor.submit(process_chunk, pdfChunk, company.company_name, i, pool.urls, model))
        
#         print(f"Processing chunks {len(futures)}")
#         try:
#             all_graphs = Graph()
#             for future in tqdm(concurrent.futures.as_completed(futures), desc=f"Processing for {company.company_name}", unit=" chunk", total=len(futures), leave=False, position=1):
#                 r: Graph = future.result()
#                 if r is None or isinstance(r, list):
#                     continue

#                 # loop through all the nodes and add only if it doesn't exist yet
#                 for s, p, o in r:
#                     if (s, p, o) not in all_graphs:
#                         all_graphs.add((s, p, o))

#             all_graphs.serialize(f"./data/{company.company_name}/extracted.ttl", format="turtle", encoding="utf-8")           
#         except KeyboardInterrupt:
#             print("Process interrupted by user. Exiting gracefully...")
#             for future in futures:
#                 future.cancel()  # Cancel any pending futures
#             executor.shutdown(wait=False)  # Shutdown the executor immediately
#             exit(0)
        
        
#     print(f"Stopping pool")
#     pool.stop()


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--model", type=str, help="Model to use for knowledge extraction", default=KNOWLEDGE_EXRTACTION_MODEL)
    parser.add_argument("--company", type=str, help="Company name to build knowledge for", required=True)
    parser.add_argument("--document",  help="Document to build knowledge from", type= str, required=True)
    args = parser.parse_args()


    pdfText = extract_text_from_pdf(args.document)
    # get filename 
    baseName = os.path.basename(args.document)

    kbextract = KnowledgeExtractor(model=args.model, chunk_size=1024, chunk_size_overlap=128, work_dir=f"./.cache/{baseName}", extraction_callbacks=FileDumpCallbackManager(workdir=f"./.cache/{baseName}"))
    kbextract.preprocess(pdfText)
    kbextract.extract()
