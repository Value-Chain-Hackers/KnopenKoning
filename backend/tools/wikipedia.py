from typing import Any, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool

from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool


class WikipediaQueryRun(BaseTool):
    """Tool that searches the Wikipedia API."""

    name: str = "Wikipedia"
    description: str = (
        "Useful for when you need to answer general questions about "
        "people, places, companies, facts, historical events, or other subjects. "
        "Input should be a search query as a string in the parameter 'query'."
    )
    api_wrapper: WikipediaAPIWrapper

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the Wikipedia tool."""
        return self.api_wrapper.run(query)
