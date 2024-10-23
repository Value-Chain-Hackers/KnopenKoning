from logging import getLogger
from steps.base import WorkflowStep
from steps.llm import PromptFormattingMixin

logger = getLogger(__name__)

from textwrap import dedent
from typing import Dict, Any, List, Optional, Type, Union, get_args, get_origin
from pydantic import BaseModel, ValidationError

from langchain.prompts import PromptTemplate
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain.output_parsers.retry import RetryWithErrorOutputParser
from langchain_core.language_models import BaseChatModel
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_ollama.chat_models import ChatOllama

from callbacks import ResearchProcessCallback
from models import *
from steps.base import WorkflowStep

from langchain.prompts import PromptTemplate
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain.output_parsers.retry import RetryWithErrorOutputParser
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_ollama.chat_models import ChatOllama
from langchain.agents import AgentExecutor,  create_openai_tools_agent
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_community.tools import TavilySearchResults
import os

class AgentWorkflowStep(WorkflowStep, PromptFormattingMixin):
    def __init__(self, state_data: Dict[str, Any], step_data: StepModel, callback: Optional[ResearchProcessCallback] = None, **kwargs):
        super().__init__(state_data, step_data, callback, **kwargs)
        
        os.environ["TAVILY_API_KEY"] = "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"
        tool = TavilySearchResults(
            max_results=5,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True,
            include_images=True,
            
            # include_domains=[...],
            # exclude_domains=[...],
            # name="...",            # overwrite default tool name
            # description="...",     # overwrite default tool description
            # args_schema=...,       # overwrite default args_schema: BaseModel
        )
        
        self.tools = [ tool ]
        self.ollama_host = kwargs.get("ollama_host", step_data.args.get("ollama_host", "http://localhost:11434"))
        self.ollama_num_ctx = kwargs.get("ollama_num_ctx", step_data.args.get("ollama_num_ctx", 8000))
        self.model_name = kwargs.get("model_name", step_data.args.get("model_name", "llama3.1:8b"))
        self.prompt_instructions = kwargs.get("prompt", step_data.args.get("prompt", "You  are a helpful AI assistant."))
        self.verbose = kwargs.get("verbose", step_data.args.get("verbose", False))
        self.llm = ChatOllama(model=self.model_name, base_url=self.ollama_host, num_ctx=self.ollama_num_ctx, verbose=self.verbose)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful assistant."),
                MessagesPlaceholder(variable_name="history", optional=True),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )
        self.agent = create_openai_tools_agent(llm=self.llm, prompt=self.prompt, tools=self.tools)
        self.chat_history = SQLChatMessageHistory(
            session_id="test_session_id", connection_string="sqlite:///history.db"
        )
        self.config = {"configurable": {"session_id": step_data.id}}
        self.logCallback = lambda message: print(message)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=self.verbose, 
            return_intermediate_steps=False,handle_parsing_errors=True)
        self.with_history = RunnableWithMessageHistory(
            self.agent_executor,
            lambda session_id: self.chat_history,
            input_messages_key="input",
            history_messages_key="history", 
            output_messages_key="output",
        )
        
    def _execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        merged_data = {
            **context_data, **input_data
        }
        
        formatted_instructions = PromptTemplate.from_template(dedent(self.prompt_instructions)).format(**merged_data)
        
        formatted_input_data = self.generate_prompt_input(input_data)
        
        expected_output_format = self.generate_prompt_output_description()
        
        prompt_template = PromptTemplate.from_template(dedent("""\
            ## Instructions:
            {instructions}
            
            ## Inputs:
            {inputs}
            
            ## Expected Output:
            The output should be a JSON object with the following structure:
            ```json	
            {output_format}
            ```
            Make sure your response respects the output format defined in Expected Output.
            DO not refer to the data formats nor the models used in the input data.
            DO NOT use any commenting style in the output, the output should be a valid JSON object.
            ONLY output the data requested in the output format. Do not include any additional information.
            """))
        data = {"instructions": formatted_instructions, "inputs": formatted_input_data, "output_format": expected_output_format}
        formatted_prompt = prompt_template.format(**data)
        ai_response = self.with_history.invoke({"input": formatted_prompt}, self.config)
        retry_parser = RetryWithErrorOutputParser.from_llm(parser=SimpleJsonOutputParser(pydantic_object=self.output_model_cls), llm=self.llm)
        try:
            ai_response = retry_parser.parse_with_prompt(ai_response["output"], prompt_template.format(**data))
        except ValidationError as e:
            raise ValueError(f"Output data validation failed: {e}")
        return ai_response
