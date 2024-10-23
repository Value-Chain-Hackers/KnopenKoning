from abc import ABC, abstractmethod
from pydantic import BaseModel, ValidationError
from typing import Dict, Any, List, Optional, Callable, Type
import yaml
import re

from callbacks import ResearchProcessCallback, CallbackManager, StdOutPrintProcessCallback
from steps import *

class OutputProcessor(ABC):
    @abstractmethod
    def process(self, output_data: Dict[str, Any], state_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class InputProcessor(ABC):
    @abstractmethod
    def process(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
class ModelBasedInputProcessor(InputProcessor):
        def __init__(self, model_type: Type[BaseModel]):
            self.model_type = model_type
            
        def process(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
            return self.model_type.model_validate(state_data).model_dump()

class ModelBasedOutputProcessor(OutputProcessor):
    def __init__(self, model_type: Type[BaseModel]):
        self.model_type = model_type
    
    def process(self, output_data: Dict[str, Any], state_data: Dict[str, Any]) -> Dict[str, Any]:
        # Validate and structure the output_data according to the model
        validated_data = self.model_type(**output_data).model_dump()
        
        # Merge validated_data into the state_data
        new_state_data = state_data.copy()
        new_state_data.update(validated_data)
        
        return new_state_data

class FromKeyInputProcessor(InputProcessor):
    def __init__(self, key: str):
        self.key = key
        
    def process(self, state_data: Dict[str, Any]) -> Any:
        return self._get_value(state_data, self.key)
    
    def _get_value(self, data: Any, key: str) -> Any:
        # Split the key by dot notation
        parts = key.split('.')
        
        for part in parts:
            # Handle indexer notation like [0] or [:5]
            index_match = re.match(r'^([a-zA-Z_]\w*)(\[.+\])$', part)
            if index_match:
                # Extract dictionary key and indexer part
                dict_key, indexer = index_match.groups()
                data = data[dict_key]
                
                # Evaluate the indexer (e.g., [0], [:5])
                data = self._evaluate_indexer(data, indexer)
            else:
                # Standard dictionary key access
                data = data[part]
        
        return data
    
    def _evaluate_indexer(self, data: Any, indexer: str) -> Any:
        # Evaluate the indexer using Python's eval (safe because input is controlled)
        return eval(f'data{indexer}')

class CompositeInputProcessor(InputProcessor):
    def __init__(self, processors: List[InputProcessor]):
        self.processors = processors
    
    def process(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        new_state_data = state_data.copy()
        for processor in self.processors:
            new_state_data = processor.process(new_state_data)
        return new_state_data

class CompositeOutputProcessor(OutputProcessor):
    def __init__(self, processors: List[OutputProcessor]):
        self.processors = processors
    
    def process(self, output_data: Dict[str, Any], state_data: Dict[str, Any]) -> Dict[str, Any]:
        new_state_data = state_data.copy()
        for processor in self.processors:
            new_state_data = processor.process(output_data, new_state_data)
        return new_state_data
    
class UpdateOutputProcessor(OutputProcessor):
    def __init__(self, key: str = None):
        self.key = key
    
    def process(self, output_data: Dict[str, Any], state_data: Dict[str, Any]) -> Dict[str, Any]:
        new_state_data = state_data.copy()
        
        if self.key:
            # Ensure that the key exists in the state_data
            if self.key in new_state_data:
                # Update the specific sub-dictionary under the key
                if isinstance(new_state_data[self.key], dict) and isinstance(output_data, dict):
                    new_state_data[self.key] = self._update_dict(new_state_data[self.key], output_data)
                else:
                    # If the existing value is not a dict, just overwrite it with output_data
                    new_state_data[self.key] = output_data
            else:
                # If the key doesn't exist, add output_data as the value for this key
                new_state_data[self.key] = output_data
        else:
            # No specific key is provided, update the entire state_data
            new_state_data = self._update_dict(new_state_data, output_data)
        
        return new_state_data

    def _update_dict(self, base_dict: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively update base_dict with values from updates.
        """
        for key, value in updates.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                base_dict[key] = self._update_dict(base_dict[key], value)
            else:
                base_dict[key] = value
        return base_dict

class ConcatOutputProcessor(OutputProcessor):
    
    def process(self, output_data: Dict[str, Any], state_data: Dict[str, Any]) -> Dict[str, Any]:
        new_state_data = state_data.copy()
        
        for key, value in output_data.items():
            if key in new_state_data:
                if isinstance(new_state_data[key], dict) and isinstance(value, dict):
                    # Recursively process nested dictionaries
                    new_state_data[key] = self.process(value, new_state_data[key])
                elif isinstance(new_state_data[key], list) and isinstance(value, list):
                    # Concatenate lists
                    new_state_data[key] += value
                else:
                    # Convert both to strings and concatenate
                    new_state_data[key] = str(new_state_data[key]) + str(value)
            else:
                # Add new key-value pairs
                new_state_data[key] = value
                
        return new_state_data

class AggregationProcessor(OutputProcessor):
    def __init__(self, aggregate_func: Callable[[List[Any]], Any], keys: List[str], target_key: str):
        self.aggregate_func = aggregate_func
        self.keys = keys
        self.target_key = target_key
    
    def process(self, output_data: Dict[str, Any], state_data: Dict[str, Any]) -> Dict[str, Any]:
        # Collect values from both state_data and output_data
        values = []
        for key in self.keys:
            if key in state_data:
                values.append(state_data[key])
            if key in output_data:
                values.append(output_data[key])

        # Apply the aggregation function to the collected values
        aggregated_value = self.aggregate_func(values)

        # Update state_data with the new aggregated value
        new_state_data = state_data.copy()
        new_state_data[self.target_key] = aggregated_value
        
        return new_state_data

class ChainedProcessingOutputProcessor(OutputProcessor):
    def __init__(self, source_key: str, target_key: str, processors: List[OutputProcessor]):
        self.source_key = source_key
        self.target_key = target_key
        self.processors = processors
    
    def process(self, output_data: Dict[str, Any], state_data: Dict[str, Any]) -> Dict[str, Any]:
        # Extract the data from output_data using the source_key
        data = output_data.get(self.source_key)
        
        # Apply each processor in the list to the data
        for processor in self.processors:
            # Process the data with each processor
            data = processor.process(data, state_data)

        # Store the processed data in the state_data under the target_key
        new_state_data = state_data.copy()
        new_state_data[self.target_key] = data
        
        return new_state_data

class MappingProcessor(OutputProcessor):
    def __init__(self, key_mapping: Optional[Dict[str, str]] = None, value_mapping: Optional[Callable[[Any], Any]] = None):
        self.key_mapping = key_mapping or {}
        self.value_mapping = value_mapping
    
    def process(self, output_data: Dict[str, Any], state_data: Dict[str, Any]) -> Dict[str, Any]:
        new_state_data = state_data.copy()
        for key, value in output_data.items():
            new_key = self.key_mapping.get(key, key)
            new_value = self.value_mapping(value) if self.value_mapping else value
            new_state_data[new_key] = new_value
        return new_state_data

class ConditionalProcessor(OutputProcessor):
    def __init__(self, condition: Callable[[Dict[str, Any], Dict[str, Any]], bool], processor: OutputProcessor):
        self.condition = condition
        self.processor = processor
    
    def process(self, output_data: Dict[str, Any], state_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.condition(output_data, state_data):
            return self.processor.process(output_data, state_data)
        return state_data

class LambdaInputProcessor(InputProcessor):
    def __init__(self, func: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.func = func
    
    def process(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        # Apply the lambda function to the state_data
        return self.func(state_data) 
  
class LambdaOutputProcessor(OutputProcessor):
    def __init__(self, func: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]):
        self.func = func
    
    def process(self, output_data: Dict[str, Any], state_data: Dict[str, Any]) -> Dict[str, Any]:
        # Apply the lambda function to the output_data and state_data
        return self.func(output_data, state_data)  
  