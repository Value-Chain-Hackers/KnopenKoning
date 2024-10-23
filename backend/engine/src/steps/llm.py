from logging import getLogger
logger = getLogger(__name__)

from textwrap import dedent
from typing import Dict, Any, List, Optional, Type, Union, get_args, get_origin
from pydantic import BaseModel, ValidationError

from langchain.prompts import PromptTemplate
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain.output_parsers.retry import RetryWithErrorOutputParser
from langchain_core.language_models import BaseChatModel
from langchain_ollama.chat_models import ChatOllama

from callbacks import ResearchProcessCallback
from models import *
from steps.base import WorkflowStep

class PromptFormattingMixin():
        
    def generate_prompt_input(self, input_data: Dict[str, Any]) -> Any:
        """
        Generate the input for the prompt template.

        Args:
            input_data (Dict[str, Any]): The input data for the step.

        Returns:
            Any: The input for the prompt template.
        """
        return self.input_model_cls(**input_data).model_dump_json(indent=4)
    
    def generate_prompt_output_description(self) -> Any:
        """
        Generate the expected output format.

        Args:
            format string: The expected output format (json, text, etc).

        Returns:
            Any: The input for the prompt template.
        """
        lines = []
        indent = 4
        indentation = " " * indent

        def process_model(model_type: Type[BaseModel], indent_level: int):
            current_indent = " " * indent_level
            lines.append(f"{current_indent}{{")
            for field_name, field in model_type.model_fields.items():
                field_type = field.annotation
                field_required = "required" if field.is_required() else "optional"
                
                if get_origin(field_type) is list:  # Handling list/array of BaseModel
                    item_type = get_args(field_type)[0]
                    if isinstance(item_type, type) and issubclass(item_type, BaseModel):
                        lines.append(f'{current_indent}{indentation}"{field_name}": [')
                        process_model(item_type, indent_level + indent)
                        lines.append(f"{current_indent}{indentation}], # type: List[{item_type.__name__}],{field_required} {field.description}")
                    else:
                        lines.append(f'{current_indent}{indentation}"{field_name}": [...], # type: List[{item_type.__name__}],{field_required}, {field.description}')
                elif isinstance(field_type, type) and issubclass(field_type, BaseModel):  # Handling BaseModel field
                    lines.append(f'{current_indent}{indentation}"{field_name}": ')
                    process_model(field_type, indent_level + indent)
                    lines.append(f"{current_indent}{indentation}, # type: {field_type.__name__},{field_required}, {field.description}")
                else:
                    # If the field type is optional, mark it as such
                    if get_origin(field_type) is Union and type(None) in get_args(field_type):
                        actual_type = [arg for arg in get_args(field_type) if arg is not type(None)][0]
                        field_required = "optional"
                    else:
                        actual_type = field_type
                        field_required = "required" if field.is_required() else "rptional"

                    lines.append(f'{current_indent}{indentation}"{field_name}": ..., # type:{actual_type.__name__}, {field_required}, {field.description}')
            lines.append(f"{current_indent}}}")

        process_model(self.output_model_cls, indent)
        return "\n".join(lines)

class LangChainMixin(PromptFormattingMixin):
    llm: BaseChatModel = None
    
    def __init__(self, state_data: Dict[str, Any], step_data: StepModel, callback: Optional[ResearchProcessCallback] = None, **kwargs):
        super().__init__(state_data, step_data, callback, **kwargs)
        self.ollama_host = kwargs.get("ollama_host", step_data.args.get("ollama_host", "http://localhost:11434"))
        self.ollama_num_ctx = kwargs.get("ollama_num_ctx", step_data.args.get("ollama_num_ctx", 8000))
        self.num_predict = kwargs.get("num_predict", step_data.args.get("num_predict", 4096))
        self.model_name = kwargs.get("model", step_data.args.get("model", "llama3.1:70b"))
        self.temperature = kwargs.get("temperature", step_data.args.get("temperature", 0.5))
        self.llm = ChatOllama(model=self.model_name, base_url=self.ollama_host, temperature=self.temperature, num_predict=self.num_predict)

        
    def get_chain(self):
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
        chain = prompt_template | self.llm
        return chain, prompt_template
    
    def prepare_prompt_data(self, input_data, context_data):
        merged_data = {
            **context_data, **input_data
        }
        formatted_instructions = PromptTemplate.from_template(dedent(self.prompt)).format(**merged_data)
        formatted_input_data = self.generate_prompt_input(input_data)
        expected_output_format = self.generate_prompt_output_description()
        data = {
            "instructions": formatted_instructions,
            "inputs": formatted_input_data,
            "output_format": expected_output_format
        }
        return data

class DefaultWorkflowStep(LangChainMixin, WorkflowStep):
    llm: BaseChatModel = None
    
    def __init__(self, state_data: Dict[str, Any], step_data: StepModel, callback: Optional[ResearchProcessCallback] = None, **kwargs):
        super().__init__(state_data, step_data, callback, **kwargs)
        self.prompt = kwargs.get("prompt", step_data.args.get("prompt", "You  are a helpful AI assistant."))

    def _execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        chain, prompt_template = self.get_chain()
        data = self.prepare_prompt_data(input_data, context_data)
        ai_response = chain.invoke(data)
        logger.warn(ai_response.response_metadata)
        retry_parser = RetryWithErrorOutputParser.from_llm(parser=SimpleJsonOutputParser(pydantic_object=self.output_model_cls), llm=self.llm)
        try:
            ai_response = retry_parser.parse_with_prompt(ai_response.content, prompt_template.format(**data))
        except ValidationError as e:
            raise ValueError(f"Output data validation failed: {e}")
        return ai_response

   