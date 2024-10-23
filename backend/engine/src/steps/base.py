from abc import ABC, abstractmethod
import json
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, ValidationError

from callbacks import ResearchProcessCallback
from models import *

from logging import getLogger
logger = getLogger(__name__)


class WorkflowStep(ABC):
    """
    Abstract base class for a workflow step. 
    Users can extend this class to implement custom workflow steps.
    """

    def __init__(self, state_data: Dict[str, Any], step_data: StepModel, callback: Optional[ResearchProcessCallback] = None, **kwargs):
        """
        Initialize the WorkflowStep with step data and a model registry.

        Args:
            state_data (Dict[str, Any]): The state data for the workflow process.
            step_data (Dict[str, Any]): Data for the step from the YAML file.
            model_registry (Dict[str, Type[BaseModel]]): A dictionary mapping model names to pydantic models.
            callback (Optional[ResearchProcessCallback]): An optional callback instance to handle process events.
            **kwargs: Additional keyword arguments.
            
        """
        self.step_name = step_data.id
        self.description = step_data.description
        self.input_model_name = step_data.input_model
        self.output_model_name = step_data.output_model
        self.next_step = step_data.next_step
        
        
        self.model_registry = state_data['model_registry']
        
        self.callback = callback
        self.state = state_data
        self.additional_arguments = kwargs
        
        self.input_model_cls = self.get_input_model()
        self.output_model_cls = self.get_output_model()

    def get_input_model(self) -> Type[BaseModel]:
        """
        Get the pydantic model class for the input.

        Returns:
            Type[BaseModel]: The pydantic model class for the input.
        """
        if self.input_model_name == "None":
            return None
        return self.model_registry[self.input_model_name]

    def get_output_model(self) -> Type[BaseModel]:
        """
        Get the pydantic model class for the output.

        Returns:
            Type[BaseModel]: The pydantic model class for the output.
        """
        if self.output_model_name == "None":
            return None
        if self.output_model_name not in self.model_registry:
            raise str
        return self.model_registry[self.output_model_name]
    
    def evaluate_exit_condition(self, output: BaseModel) -> str:
        """
        Evaluate the exit condition of the step and return the next step.

        Args:
            output (BaseModel): The output of the step.

        Returns:
            str: The name of the next step.
        """
        return self.next_step

    @abstractmethod
    def _execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        pass
    
    def execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        """
        Execute the workflow step: generate the prompt, make the AI call, and return the output model instance.

        Args:
            input_data (Dict[str, Any]): The input data for the step.

        Returns:
            BaseModel: An instance of the output model populated with the results of the AI call.
        """
        try:
            validated_input = self.input_model_cls(**input_data)
        except ValidationError as e:
            raise ValueError(f"Input data validation failed: {e}")

        try:
            result = self._execute(validated_input.model_dump(), context_data)
        except Exception as e:
            logger.error(f"Failed to execute step {self.step_name}. {e}")
            raise e
        
        try:
            validated_output = self.output_model_cls(**result)
        except ValidationError as e:
            logger.warn(json.dumps(result, indent=4))
            raise ValueError(f"Output data validation failed: {e}")
        
        return validated_output

    def __str__(self):
        return f"""Workflow Step: {self.step_name}
        Description: {self.description}
        Input Model: {self.input_model_name}
        Output Model: {self.output_model_name}
        Prompt: {self.prompt_template}
        Next Step: {self.next_step}
        """
    def __repr__(self):
        return str(self)

class NoopWorkflowStep(WorkflowStep):
    def execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        return None
    def _execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        return None
