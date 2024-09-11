from concurrent.futures import ThreadPoolExecutor
import pathlib
from config import EMBEDDING_MODEL
from config import OLLAMA_MODEL, OLLAMA_API_URL
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.callbacks import FileCallbackHandler
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_ollama.chat_models import ChatOllama
from langchain.agents import AgentExecutor,  create_openai_tools_agent
from typing import Dict, List

from utils.extract_knowledge import get_huggingface_model
import json

class RagSearchInput(BaseModel):
    query: str = Field(... , description="Query to search the rag for")

class UIElementsBuilder():
    def __init__(self, host=OLLAMA_API_URL, model_name=OLLAMA_MODEL):
        self.host = host
        self.model_name = model_name
        self.search_results = []
        print(f"UIElementsBuilder initialized with host: {host} and model_name: {model_name}")

    def answer(self, question):
        prompt=  PromptTemplate.from_template("""\
You are a helpfull assitant, helping the user to create dashboards and visualizations of supply chains.
Your task is to answer the following question: {question}
                                              
## Search Results: 
{search_results}
                                              
## Instructions:
The anwser should be a composit of one or more UI elements that will be shown to the user.
Elements might all be of the same type or mixed. Not all types are required to be present.
Only add elements that are relevant to the question.
Only refer to classes and properties that are defined in the SupplyChainMapping (scm) ontology.
Always at least one 'Text' element should be present providing an overall answer and explanation of the other elements, this should be the first element of the list.
As part of there are 'DataGrid', 'Chart', 'Text'.
Exprected output is a JSON array of UI elements.
Each element should have a 'title' field that contains the title of the visualisation. 
Each element should have a 'type' field that can be 'DataGrid', 'Chart',  'Text'.
Each element should have an 'icon' field that contains the name of a fontawesome icon that should be used to represent the element.
If the type is 'DataGrid' or 'Table' the element should have a 'columns' field that contains the columns of the table as an array of strings.
Each element should have a 'description' field that contains the description of what data should be retrieved to display this visualisation this includes entities and potenial relations.
Each element should have a 'data' field that contains an array of dictionaries with a key value pair for each column of data.
Each element should have a 'followup' field that contains a JSON array strings with a maximum 3 questions that can be asked to further explore the data within the element.
The followups should not propose filters or other ways to manipulate the data, but rather other points of interest that can be explored.
 Do not output any other data. The user can't edit your message and it will be parsed as JSON.
DO use the relevant information out of the search results to generate the answer.
Only return a valid JSON array of UI elements.
                                              
## Answer:                                              
""")
        chain = prompt | ChatOllama(model=self.model_name, base_url=self.host, num_ctx=8192) | JsonOutputParser()
        search_results = json.dumps(self.search_results)
        print(search_results)
        elements = chain.invoke({'question': question, 'search_results': search_results})

        for element in elements:
            type = element.get('type')
            if type == 'Text':
                element['content'] = self.create_text_element(question, element.get('title'), element.get('description'), search_results)
        return elements
    
    def create_text_element(self, question,  title, description, search_results):
        prompt=  PromptTemplate.from_template("""\
You are a helpfull assitant, helping the user to describe elements of a supply chains.
Your task is to generate some text regarding the question: {question}
The answer should be text based and should fullfill the following description:
The element is titled '{title}' and is described as '{description}'.
The ouput should be a text string in markdown format.
Only use data from the search results to generate the answer.
Additionally extract all named entities that are mentioned in your answer and provide them as a list of strings.
## Search Results: 
{search_results}
                       
""")
        chain = prompt | ChatOllama(model=self.model_name, base_url=self.host)
        elements = chain.invoke({'question': question, 'title': title, 'description': description, 'search_results': search_results})
        return elements