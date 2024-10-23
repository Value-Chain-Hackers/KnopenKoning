import json
from pydantic import BaseModel, ValidationError
import functools
import sys 

from abc import ABC, abstractmethod
from typing import Any, Dict, List

class ResearchProcessCallback(ABC):
    @abstractmethod
    def on_step_start(self, step_name: str, input_data: Dict[str, Any]) -> None:
        """
        Called before the execution of a step.

        Args:
            step_name (str): The name of the step being executed.
            input_data (Dict[str, Any]): The input data for the step.
        """
        pass

    @abstractmethod
    def on_step_end(self, step_name: str, output_data: BaseModel) -> None:
        """
        Called after the execution of a step.

        Args:
            step_name (str): The name of the step that was executed.
            output_data (BaseModel): The output data from the step.
        """
        pass

    @abstractmethod
    def on_exit_condition_evaluated(self, step_name: str, next_step: str) -> None:
        """
        Called after the exit condition is evaluated.

        Args:
            step_name (str): The name of the step for which the exit condition was evaluated.
            next_step (str): The determined next step based on the exit condition.
        """
        pass

    @abstractmethod
    def on_process_reset(self) -> None:
        """
        Called when the research process is reset.
        """
        pass

    @abstractmethod
    def on_process_start(self) -> None:
        """
        Called when the research process starts.
        """
        pass

    @abstractmethod
    def on_process_end(self) -> None:
        """
        Called when the research process ends.
        """
        pass

    @abstractmethod
    def on_log(self, message: str) -> None:
        """
        Called to log a message during the process.

        Args:
            message (str): The log message.
        """
        pass

    @abstractmethod
    def on_error(self, step_name: str, error: Exception) -> None:
        """
        Called when an error occurs during the process.

        Args:
            step_name (str): The name of the step where the error occurred.
            error (Exception): The exception that was raised.
        """
        pass

    @abstractmethod
    def on_validation_error(self, step_name: str, validation_error: ValidationError) -> None:
        """
        Called when a validation error occurs during the process.

        Args:
            step_name (str): The name of the step where the validation error occurred.
            validation_error (ValidationError): The validation error raised.
        """
        pass

class StdOutPrintProcessCallback(ResearchProcessCallback):
    def on_step_start(self, step_name: str, input_data: Dict[str, Any]) -> None:
        print(f"Starting step: {step_name} with input:\n {json.dumps(input_data, indent=4)}", end="\n****************\n")

    def on_step_end(self, step_name: str, output_data: BaseModel) -> None:
        try:
            output_json = output_data.json(indent=4)
        except Exception as e:
            output_json = str(output_data)        
        print(f"Finished step: {step_name} with output:\n {output_json}", end="\n****************\n")

    def on_exit_condition_evaluated(self, step_name: str, next_step: str) -> None:
        print(f"Exit condition evaluated for step: {step_name}, next step: {next_step}", end="\n****************\n")

    def on_process_reset(self) -> None:
        print("Process has been reset.", end="\n****************\n")

    def on_process_start(self) -> None:
        print("Process has started.", end="\n****************\n")

    def on_process_end(self) -> None:
        print("Process has ended.", end="\n****************\n")
    
    def on_log(self, message: str) -> None:
        print(f"Log message: {message}", end="\n****************\n")
    
    def on_error(self, step_name: str, error: Exception) -> None:
        print(f"Error in step: {step_name}, error: {error}", end="\n****************\n")
    
    def on_validation_error(self, step_name: str, validation_error: ValidationError) -> None:
        print(f"Validation error in step: {step_name}, error: {validation_error}", end="\n****************\n")

def handle_exceptions(exception_type=Exception, default_return_value=None):
    """
    A decorator that catches exceptions of a specified type
    and returns a default value if an exception is raised.

    Parameters:
    exception_type (Exception or tuple of Exceptions): The exception type(s) to catch.
    default_return_value: The value to return if an exception is caught.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_type as e:
                print(f"An exception occurred in {func.__name__}: {e}")
                return default_return_value
        return wrapper
    return decorator

class CallbackManager(ResearchProcessCallback):
    def __init__(self, callbacks: List[ResearchProcessCallback] = None):
        """
        Initialize the CallbackManager with a list of callbacks.

        Args:
            callbacks (List[ResearchProcessCallback]): A list of callback instances to manage.
        """
        self.callbacks = callbacks if callbacks is not None else []

    def add_callback(self, callback: ResearchProcessCallback) -> None:
        """
        Add a callback to the manager.

        Args:
            callback (ResearchProcessCallback): The callback instance to add.
        """
        self.callbacks.append(callback)

    def remove_callback(self, callback: ResearchProcessCallback) -> None:
        """
        Remove a callback from the manager.

        Args:
            callback (ResearchProcessCallback): The callback instance to remove.
        """
        self.callbacks.remove(callback)

    def run_callbacks(self, method_name, *args, **kwargs) -> None:
        """
        Run a specified method on all registered callbacks.

        Args:
            callback_method (str): The name of the method to run.
            *args: Positional arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.
        """
        for callback in self.callbacks:
            try:
                method = getattr(callback, method_name)
                method(*args, **kwargs)
            except Exception as e:
                print(f"Error running callback method {method_name}: {e}")
                
    def on_step_start(self, step_name: str, input_data: Dict[str, Any]) -> None:
        """
        Invoke on_step_start on all registered callbacks.

        Args:
            step_name (str): The name of the step being executed.
            input_data (Dict[str, Any]): The input data for the step.
        """
        self.run_callbacks('on_step_start', step_name, input_data)
            
    def on_step_end(self, step_name: str, output_data: BaseModel) -> None:
        """
        Invoke on_step_end on all registered callbacks.

        Args:
            step_name (str): The name of the step that was executed.
            output_data (BaseModel): The output data from the step.
        """
        self.run_callbacks('on_step_end', step_name, output_data)

    def on_exit_condition_evaluated(self, step_name: str, next_step: str) -> None:
        """
        Invoke on_exit_condition_evaluated on all registered callbacks.

        Args:
            step_name (str): The name of the step for which the exit condition was evaluated.
            next_step (str): The determined next step based on the exit condition.
        """
        self.run_callbacks('on_exit_condition_evaluated', step_name, next_step)

    def on_process_reset(self) -> None:
        """
        Invoke on_process_reset on all registered callbacks.
        """
        self.run_callbacks('on_process_reset')

    def on_process_start(self) -> None:
        """
        Invoke on_process_start on all registered callbacks.
        """
        self.run_callbacks('on_process_start')

    def on_process_end(self) -> None:
        """
        Invoke on_process_end on all registered callbacks.
        """
        self.run_callbacks('on_process_end')

    def on_log(self, message: str) -> None:
        """
        Invoke on_log on all registered callbacks.

        Args:
            message (str): The log message.
        """
        self.run_callbacks('on_log', message)

    def on_error(self, step_name: str, error: Exception) -> None:
        """
        Invoke on_error on all registered callbacks.

        Args:
            step_name (str): The name of the step where the error occurred.
            error (Exception): The exception that was raised.
        """
        self.run_callbacks('on_error', step_name, error)

    def on_validation_error(self, step_name: str, validation_error: ValidationError) -> None:
        """
        Invoke on_validation_error on all registered callbacks.

        Args:
            step_name (str): The name of the step where the validation error occurred.
            validation_error (ValidationError): The validation error raised.
        """
        self.run_callbacks('on_validation_error', step_name, validation_error)
