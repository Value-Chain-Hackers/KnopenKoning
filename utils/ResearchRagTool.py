from langchain_chroma import Chroma
from config import EMBEDDING_MODEL
from utils.extract_knowledge import get_huggingface_model
from utils.uielements import RagSearchInput


from langchain_core.pydantic_v1 import BaseModel
from langchain_core.tools import BaseTool


from typing import Type


class ResearchRagTool(BaseTool):
    name = 'ResearchRagTool'
    description = 'Tool to search relevant information already in the research case.'
    args_schema: Type[BaseModel] = RagSearchInput
    working_dir: str = ".cache/tmp_case"
    chroma: Chroma = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chroma: Chroma = Chroma("search_results",  embedding_function=get_huggingface_model(EMBEDDING_MODEL), 
                persist_directory=self.working_dir)

    def _run(self, query:str) -> list[dict[str, any]] | str:
        results = self.chroma.similarity_search_with_score(query, k=5)
        final_results = []
        for res, score in results:
            final_results.append({
                    'score': score,
                    'content': res.page_content,
                    'metadata': res.metadata,
            })
        if final_results:
            return final_results
        return "No relevant information found in the research case."