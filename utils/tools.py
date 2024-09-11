from langchain_core.tools import BaseTool

from typing import List, Type, Union

from pydantic import BaseModel, Field


class ThoughtsInput(BaseModel):
    thought: str = Field(title="thought", description="thought to be added to the research case")

class ThoughtsTool(BaseTool):
    name = 'ThoughtsTool'
    description = "Tool to add a new thought to the context, avoid duplication or too similar."
    args_schema: Type[BaseModel] = ThoughtsInput
    thoughts: list = None
    return_direct: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.thoughts = kwargs.get('thoughts', [])

    def _run(self, thought: str, **data) -> dict:
        if thought in self.thoughts:
            return f"Thought already exists: {thought}"
        self.thoughts.append(thought)
        return f"Thought added: {thought}"