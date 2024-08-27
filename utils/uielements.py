import ollama
import json
from langchain_community.llms.ollama import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class UIElementsBuilder():
    def __init__(self, host="http://ollama:11434"):
        self.host = host

    def answer(self, question):
        prompt=  PromptTemplate.from_template("""\
You are a helpfull assitant, helping the user to create dashboards and visualizations of supply chains.
Your task is to answer the following question: {question}
The anwser should be a composit of one or more UI elements that will be shown to the user.
Elements might all be of the same type or mixed. Not all types are required to be present.
Only add elements that are relevant to the question.
Only refer to classes and properties that are defined in the SupplyChainMapping (scm) ontology.
Always at least one 'Text' element should be present providing an overall answer and explanation of the other elements, this should be the first element of the list.
As part of there are 'DataGrid', 'Chart', 'Graph', 'Text'.
Exprected output is a JSON array of UI elements.
Each element should have a 'title' field that contains the title of the visualisation. 
Each element should have a 'type' field that can be 'DataGrid', 'Chart', 'Graph', 'Text'.
Each element should have an 'icon' field that contains the name of a fontawesome icon that should be used to represent the element.
If the type is 'DataGrid' or 'Table' the element should have a 'columns' field that contains the columns of the table as an array of strings.
Each element should have a 'description' field that contains the description of what data should be retrieved to display this visualisation this includes entities and potenial relations.
Each element should have a 'query' field that contains the rdflib compliant query that should be used to retrieve the data.
Each element should have a 'followup' field that contains a JSON array strings with a maximum 3 questions that can be asked to further explore the data within the element.
The followups should not propose filters or other ways to manipulate the data, but rather other points of interest that can be explored.
Only return a valid JSON array of UI elements. Do not output any other data. The user can't edit your message and it will be parsed as JSON.
""")
        chain = prompt | Ollama(model="llama3.1:70b", base_url=self.host) | JsonOutputParser()
        elements = chain.invoke({'question': question})
        for element in elements:
            type = element.get('type')
            if type == 'Text':
                element['content'] = self.create_text_element(question, element.get('title'), element.get('description'))
        return elements
    
    def create_text_element(self, question,  title, description):
        prompt=  PromptTemplate.from_template("""\
You are a helpfull assitant, helping the user to describe elements of a supply chains.
Your task is to generate some text regarding the question: {question}
The answer should be text based and should fullfill the following description:
The element is titled '{title}' and is described as '{description}'.
The ouput should be a text string in markdown format.
""")
        chain = prompt | Ollama(model="llama3.1:70b", base_url=self.host)
        elements = chain.invoke({'question': question, 'title': title, 'description': description})
        return elements