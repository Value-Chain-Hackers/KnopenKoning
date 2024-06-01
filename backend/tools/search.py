from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchResults
from typing import Any, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool

from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper


from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
import json
class DuckSearch(BaseTool):
    name: str = "DuckSearch"
    description: str = (
        "Useful for when you need to answer general questions about "
        "people, places, companies, facts, historical events, or other subjects. "
        "Input should be a search query as a string in the parameter 'query'."
    )
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        wrapper = DuckDuckGoSearchAPIWrapper()
        results = wrapper.results(query,max_results=5)
        return '```json\n' + json.dumps(results, indent=4) + '\n```'