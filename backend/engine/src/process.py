
from pydantic import BaseModel, ValidationError
from typing import Dict, Any, List, Optional, Callable
import yaml
import re

from callbacks import ResearchProcessCallback, CallbackManager, StdOutPrintProcessCallback
from models import *
from processors import *
from steps.steps import *


class ResearchProcess:
    output_processors = {
        "default": UpdateOutputProcessor(),
    }

    def __init__(self, workflow_path: str, model_registry: Dict[str, Any], callback: Optional[ResearchProcessCallback] = CallbackManager()):
        """
        Initialize the ResearchProcess with a workflow path, model registry, and optional callback.

        Args:
            workflow_path (str): Path to the YAML file defining the workflow.
            model_registry (Dict[str, Any]): A dictionary mapping model names to pydantic models.
            callback (Optional[ResearchProcessCallback]): An optional callback instance to handle process events.
        """
        self.workflow_path = workflow_path
        self.flow = self._load_workflow()
        
        self.state = {
            "context": {},
            "current_step_index": 0,
            "model_registry": model_registry,
            "information_repository": InformationRepository(persist_directory="./search_data"),
        }
        
        self.inputs = {}
        
        self.outputs = {}
        
        self.callback = callback

    @property
    def current_step_index(self) -> int:
        return self.state['current_step_index']
    
    @current_step_index.setter
    def current_step_index(self, value: int):
        self.state['current_step_index'] = value
        
    @property
    def context(self) -> Dict[str, Any]:
        return self.state['context']
    
    @context.setter
    def context(self, value: Dict[str, Any]):
        self.state['context'] = value

    def _load_workflow(self) -> List[Dict[str, Any]]:
        """
        Load the workflow from the YAML file.

        Returns:
            List[Dict[str, Any]]: A list of workflow steps loaded from the YAML file.
        """
        with open(self.workflow_path, 'r') as file:
            workflow_data = yaml.safe_load(file)
        
        return WorkflowModel(**workflow_data) 

    def _validate_workflow(self) -> None:
        """
        Validate the workflow data to ensure it is properly formatted.
        """
        for step in self.steps:
            if 'step' not in step:
                raise ValueError("Workflow step is missing 'step' key.")
            if 'next_step' not in step and 'exit' not in step:
                raise ValueError("Workflow step is missing 'next_step' or 'exit' key.")

    def _get_current_step(self) -> Dict[str, Any]:
        """
        Get the data for the current workflow step.

        Returns:
            Dict[str, Any]: The current step's data.
        """
        return self.flow.steps[self.current_step_index]

    def register_output_processor(self, name: str, processor: OutputProcessor) -> None:
        """
        Register a custom output processor by name.

        Args:
            name (str): The name of the output processor.
            processor (OutputProcessor): The output processor instance.
        """
        self.output_processors[name] = processor

    def run_step(self) -> Optional[BaseModel]:
        """
        Run the current step of the research process.

        Returns:
            Optional[BaseModel]: The output of the current step, or None if the step failed.
        """
        logger.debug(f"Running step {self.current_step_index}")
        step_data = self._get_current_step()
        # Determine the step implementation to use based on the step type
        try:
            step = workflow_step_factory(step_data, self.state, self.callback)
        except Exception as e:
            self.callback.on_log(f"Failed to create step {step_data['step']} {e}")
            logger.debug(f"Failed to create step {step_data['step']} {e}")
            raise e
        logger.debug(f"Build step {step.step_name}")
        input_data = self.inputs.get(step.step_name, {})

        self.callback.on_step_start(step.step_name, input_data)
        
        output = None
        try:
            output = step.execute(input_data, self.context)
        except Exception as e:
            self.callback.on_log(f"Step {step.step_name} failed to execute. {e}")
            raise e
        
        with open(f".web_cache/{step.step_name}.output.yaml", "w") as f:
            if isinstance(output, BaseModel):
                yaml.dump(output.model_dump(), f)
            elif isinstance(output, dict):
                yaml.dump(output, f)
            else:
                f.write(str(output))
        
        try:    
            
            if output is None:
                self.callback.on_log(f"Step {step.step_name} failed to execute.")
            else:
                if isinstance(output, BaseModel):
                    dumped_output = output.model_dump()
                elif isinstance(output, dict):
                    dumped_output = output
                else:
                    raise ValueError("Output must be a Pydantic model or a dictionary.")
                    
                # Update the context and outputs with the step result
                self.outputs[step.step_name] = dumped_output
                self.context.update(dumped_output)
                self.context[step.step_name] = dumped_output
                self.inputs[step.next_step] = dumped_output
                
        except ValidationError as e:
            # Trigger the validation error callback
            self.callback.on_validation_error(step.step_name, e)
            self.callback.on_log(f"Validation error in step {step.step_name}: {e}")
            return (None, "exit")
        
        try:    
            
            # Trigger the on_step_end callback
            self.callback.on_step_end(step.step_name, output)

            # Determine the next step based on the exit condition
            next_step = step.evaluate_exit_condition(output)

            # Trigger the on_exit_condition_evaluated callback
            self.callback.on_exit_condition_evaluated(step.step_name, next_step)

            

            return (output, next_step)

        except ValidationError as e:
            # Trigger the validation error callback
            self.callback.on_validation_error(step.step_name, e)
            self.callback.on_log(f"Validation error in step {step.step_name}: {e}")
            return None

    def run(self) -> None:
        """
        Run the entire research process from start to finish.
        """
        self.callback.on_process_start()
        logger.debug("Starting research process.")
        while self.current_step_index < len(self.flow.steps):
            step = self.flow.steps[self.current_step_index]
            logger.debug(f"Running Step {self.current_step_index} {step.id}")
            try:
                output, next_step = self.run_step()
            except Exception as e:
                next_step = "exit"
                logger.debug(f"Exiting at {self.current_step_index} {step.id} {e}")

            if next_step == "repeat":
                self.callback.on_log(f"Repeating step: {step.step_name}")
            elif next_step == "exit":
                self.current_step_index = len(self.flow.steps)  # Terminate the process
            else:
                # Move to the specified next step
                self.current_step_index = next(i for i, s in enumerate(self.flow.steps) if s.id == next_step)

        self.callback.on_process_end()

    def set_input(self, step_name: str, input_data: Dict[str, Any]) -> None:
        """
        Set input data for a specific step in the research process.

        Args:
            step_name (str): The name of the step to set input for.
            input_data (Dict[str, Any]): The input data to set.
        """
        self.inputs[step_name] = input_data

    def get_output(self, step_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the output data for a specific step in the research process.

        Args:
            step_name (str): The name of the step to get output from.

        Returns:
            Optional[Dict[str, Any]]: The output data, or None if not available.
        """
        return self.outputs.get(step_name)

    def reset(self) -> None:
        """
        Reset the research process to its initial state.
        """
        self.callback.on_process_reset()

        self.current_step_index = 0
        self.context.clear()
        self.state.clear()
        self.inputs.clear()
        self.outputs.clear()
