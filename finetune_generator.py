from utils.ontology_parser import GraphVisitor
from dotenv import load_dotenv
import os
import json
import pandas as pd

load_dotenv()

if __name__ == "__main__":
    from tqdm import tqdm
    import pandas as pd
    from langchain_community.llms.ollama import Ollama
    from langchain_openai.chat_models import ChatOpenAI
    from langchain.prompts import PromptTemplate
    from langchain_core.output_parsers.json import JsonOutputParser
    from langchain.output_parsers.retry import RetryWithErrorOutputParser
    import os
    model = "command-r:latest"
    #llm = ChatOpenAI(temperature=0, model_name="gpt-4")
    llm = Ollama(model=model, num_ctx=4096, num_predict=4096, temperature=0.1)
    prompt = PromptTemplate.from_template("""\
### Instructions:

Given the provided part ontology part above please generate a set of triplets of (instruction, input, output) to create a fine-tuning dataset about the given ontology.
Make sure to refer to the name of the ontology as the 'Supply Chain Mapping' ontology and/or the prefix scm.
                                          

**Expected Ouput**:

DO output a JSON array of dictionaries each, dict should have a (instruction, input, output) key/value pair.
DO ONLY output the (instruction, input, output) pairs dicts in an array. DO NOT add any additional content.
DO ONLY output valid json object, respecting quoting and escaping of special chars. 
Make sure to make very diversified (instruction, input, output) covering all aspects of the ontology. 
DO include questions that ask for an examples and produce a valid example in a turtle code block in the answer.
DD generate at least 5 question/answer pairs. When the answer contains rdf or turtle code, make sure to wrap it in a ``` code block.
DO make instructions and examples that are clear and easy to understand.
Do not make questions that only ask for a definition of a term.
DO make questions that foster reasoning about the ontology.
Do direct the questions to the tasks of knowledge graph creation and ontology mapping.
Make sure to include a variety of question types and examples.
Make sure your output is valid JSON in a ```json``` code block.
Make sure that instructions contains the instruction an input contains the specific question or task and output contains the answer to the question or task.
Instructions should be like : 'You are a helpful AI assistant, that helps users with the ontology. Please provide a [concise, complete, clear, and correct] answer to the users input question. (This is an example make sure you variate the instructions prompt too)
Do not add the input to the instrurctions make sure the question is in the input.
Make sure to include a variety of instructions and examples.
DO ONLY OUTPUT THE JSON ARRAY OF DICTIONARIES. MAKE SURE TO ESCAPE SPECIAL CHARACTERS IN THE JSON OUTPUT.

### Input:

{ontology}     

""")
    chain = prompt | llm | JsonOutputParser()
    allQuestions = []
    import glob
    files = glob.glob("docs/ontology/*.md")
    allResults = [] 
    import pandas as pd
    for file in tqdm(files):
        try:
            ontology = ""
            with open(file, "r", encoding="utf-8") as f:
                ontology = f.read()
            result = chain.invoke({"ontology": ontology})
            for r in result:
                r["ontology"] = os.path.basename(file).replace('.md', '')
                r["model"] = model
            allResults.append(result)
            file = f"docs/ontology/{os.path.basename(file).replace('.md', '.parquet')}"
            if os.path.exists(file):
                dataFrame = pd.read_parquet(file)
                dataFrame = pd.concat([dataFrame, pd.DataFrame(result)])
                dataFrame.to_parquet(file)
            else:
                dataFrame = pd.DataFrame(result)
                dataFrame.to_parquet(file)
        except Exception as e:
            print(file, e)
    dataFrame = pd.concat(allResults)
    dataFrame.to_parquet("docs/ontology/all.parquet")

   
