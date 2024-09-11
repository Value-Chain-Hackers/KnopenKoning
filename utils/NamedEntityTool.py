
from langchain_core.tools import BaseTool
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import MessagesPlaceholder, PromptTemplate

from typing import List, Type

class EntityRelationshipDeclaration(BaseModel):
    subjectEntityType: str = Field(..., description="the first EntityType in the relationship")
    predicate: str = Field(..., description="the relationship between the two entities")
    objectEntityType: str = Field(..., description="the second EntityType in the relationship")
    description: str = Field(..., description="a brief description of the relationship")

class EntityRelationshipTool(BaseTool):
    name = 'EntityRelationshipTool'
    description = 'Tool to declare relationships between named entities.'
    args_schema: Type[BaseModel] = EntityRelationshipDeclaration
    named_entities_relations: list = None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.named_entities_relations = kwargs.get('named_entities_relations', [])

    def _run(self, subjectEntityType: str, predicate: str, objectEntityType: str, description: str) -> str:
        self.named_entities_relations.append({
            'subjectEntityType': subjectEntityType,
            'predicate': predicate,
            'objectEntityType': objectEntityType,
            'description': description,
        })
        return f"Relationship added: {subjectEntityType} {predicate} {objectEntityType}"

class NamedEntityDeclaration(BaseModel):
    entityType: str = Field(..., description="the type of the named entity")
    description: str = Field(..., description="a brief description of the named entity")

class NamedEntityTool(BaseTool):
    name = 'NamedEntityTool'
    description = 'Tool to declare named entities types.'
    args_schema: Type[BaseModel] = NamedEntityDeclaration
    named_entities: list = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.named_entities = kwargs.get('named_entities', [])

    def _run(self, entityType: str, description: str) -> str:
        self.named_entities.append({
            'entityType': entityType,
            'description': description,
        })
        return f"Named entity added: {entityType}"