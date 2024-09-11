from config import OLLAMA_API_URL, OLLAMA_MODEL


from langchain_core.callbacks import FileCallbackHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama


class SummarizerTool(BaseTool):
    name = 'SummarizerTool'
    description = 'Tool to summarize the research case.'
    return_direct: bool = True
    host: str = None
    model_name: str = None
    llm: ChatOllama = None
    summary_prompt: ChatPromptTemplate = None
    summary_chain: ChatPromptTemplate = None

    def __init__(self, host=OLLAMA_API_URL, model_name=OLLAMA_MODEL, **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self.model_name = model_name
        self.llm = ChatOllama(model=self.model_name,
                            base_url=self.host,
                            num_ctx=8192,
                            verbose=self.verbose, callbacks=[FileCallbackHandler("./logs/SummarizerTool.log")])
        self.summary_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are helpful and very precise document sumarrizer. You kket al factual and technical detaisk but remove the overhead from any document."),
                ("human", "{input}")]
            )
        self.summary_chain = self.summary_prompt | self.llm | StrOutputParser()

    def _run(self, **data) -> dict:
        return {
            'output': self.summary_chain.invoke(**data)
        }
    