from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool

from typing import Type

class QuestionInput(BaseModel):
    question: str = Field(..., description="the question to be added to the research case")

class QuestionTool(BaseTool):
    name = 'QuestionTool'
    description = 'Tool to create research questions to be answered by futher research and analysis.'
    args_schema: Type[BaseModel] = QuestionInput
    return_direct: bool = True
    questions: list = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.questions = kwargs.get('questions', [])

    def _run(self, question:  str) -> str:
        if question in self.questions:
            return f"Question already exists."
        self.questions.append(question)
        return f"question added."