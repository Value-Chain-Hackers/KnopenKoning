from utils.ontology_parser import GraphVisitor


if __name__ == "__main__":
    ontology = ""
    with open("./data/supplychain.ttl", "r", encoding='utf-8') as file:
        ontology = file.read()
    gv = GraphVisitor()
    gv.parse("./data/supplychain.ttl","text/turtle")
    md = gv.rdf_to_markdown()
    with open(f"./data/supplychain.md", "w", encoding="utf-8") as out:
        out.write(md)
    from tqdm import tqdm
    import pandas as pd
    from langchain_community.llms.ollama import Ollama
    from langchain_openai.chat_models import ChatOpenAI
    from langchain.prompts import PromptTemplate
    from langchain_core.output_parsers.json import JsonOutputParser
    from langchain.output_parsers.retry import RetryWithErrorOutputParser
    import os
    #llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
    llm = Ollama(model="llama3:70b", num_ctx=8192, num_predict=4096)
    prompt = PromptTemplate.from_template("""\
### Instructions:

{ontology}                                          
                              
Given the above ontology please generate a set of questions and answers to create a fine-tuning dataset about the given ontology.
Make sure to refer to the name of the ontology as the 'supply chain mapping' ontology and/or prefix scm.

### Expected Ouput:

DO output a JSON array of dictionaries each, dict should have a 'question' and 'answer' key/value pair.
DO ONLY output the Question and Answer pairs dicts in an array. DO NOT add any additional content.
DO ONLY output valid json object, respecting quoting and escaping of special chars. 
DO generate questions where the answers also include negations like Question : 'is the Ball class part of the ontology' Answer : 'No there is no Ball class in the suppy chain ontology'
Make sure to make very diversified questions covering all aspects of the ontology. DO include questions that ask for an example and produce a valid example in a turtle code block in the answer.
DD generate at least 30 question/answer pairs. When the answer contains rdf or turtle code, make sure to wrap it in a code block.
                                          
""")
    chain = prompt | llm | JsonOutputParser()
    allQuestions = []

    for i in tqdm(range(20)):
        try:
            questions = chain.invoke({"ontology": ontology})
        except Exception as e:
            print(e)
            continue
        allQuestions.extend(questions)
        df= pd.DataFrame(allQuestions)
        df.to_json(f"./q_a__{i}.json", orient="records")
        df.to_parquet("./q_a__.parquet")
