from dotenv import load_dotenv
import os
import glob
import pandas as pd
from tqdm import tqdm
from langchain_community.llms.ollama import Ollama
from langchain_openai.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser
from langchain.output_parsers.retry import RetryWithErrorOutputParser
import concurrent.futures
import argparse
import signal
import sys

load_dotenv(".env")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost:11434")

if not os.path.exists(".cache"):
    os.makedirs(".cache")
if not os.path.exists(".cache/ontology"):
    os.makedirs(".cache/ontology")

def process_file(file, chain, model, max_examples):
    try:
        with open(file, "r", encoding="utf-8") as f:
            ontology = f.read()

        ontology_uri = ontology.split("\n")[1].split(":")[1].strip()
        ontologyClass = os.path.basename(file).replace('.md', '')

        result = chain.invoke({
            "ontology": ontology,
            "ontology_class": ontologyClass,
            "ontology_name": "Supply Chain Mapping",
            "max_examples": max_examples,
            "ontology_uri": ontology_uri
        })

        for r in result:
            r["ontology"] = os.path.basename(file).replace('.md', '')
            r["model"] = model

        file_path = f".cache/ontology/{os.path.basename(file).replace('.md', '.parquet')}"
        if os.path.exists(file_path):
            dataFrame = pd.read_parquet(file_path)
            dataFrame = pd.concat([dataFrame, pd.DataFrame(result)])
            dataFrame.to_parquet(file_path)
        else:
            dataFrame = pd.DataFrame(result)
            dataFrame.to_parquet(file_path)

        return result

    except Exception as e:
        print(file, e)
        return []

def signal_handler(sig, frame):
    print("Processing interrupted. Exiting gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    argsparser = argparse.ArgumentParser()
    argsparser.add_argument("--model", type=str, default="gemma2")
    argsparser.add_argument("--max_examples", type=int, default=20)
    argsparser.add_argument("--temperature", type=float, default=0.5)
    argsparser.add_argument("--max_workers", type=int, default=4)
    args = argsparser.parse_args()
    
    model = args.model
    max_examples = args.max_examples
    temperature = args.temperature
    max_workers = args.max_workers

    llm = Ollama(model=model, num_ctx=4096*2, num_predict=4096*2, temperature=temperature, base_url=f"http://{OLLAMA_HOST}")
    prompt = PromptTemplate.from_file("prompts/ontology_finetune.md")
    chain = prompt | llm | JsonOutputParser()

    files = glob.glob(".cache/docs/ontology/*.md")
    filteredFiles = [file for file in files if not os.path.basename(file).startswith("n") or os.path.basename(file) == "name.md"]

    allResults = []

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_file, file, chain, model, max_examples): file for file in filteredFiles}
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(filteredFiles)):
                try:
                    result = future.result()
                    allResults.append(result)
                except KeyboardInterrupt:
                    print("Processing interrupted. Exiting gracefully...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise

    except KeyboardInterrupt:
        print("Processing interrupted. Exiting gracefully...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if allResults:
            allResults = [item for sublist in allResults for item in sublist]  # Flatten the list of lists
            dataFrame = pd.DataFrame(allResults)
            dataFrame.to_parquet(".cache/docs/ontology/all.parquet")
