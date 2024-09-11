from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import pathlib
import shutil
from typing import Type
from langchain_core.tools import BaseTool
from langchain_core.pydantic_v1 import BaseModel, Field
import requests
from langchain_community.tools.tavily_search import TavilySearchResults 

class WebSearchInput(BaseModel):
    query: str = Field(description="query to search the web for")

class ResearchWebSearchTool(BaseTool):
    name = 'WebSearchTool'
    description = '''Tool to search the web for relevant information to be used in the research case.
    Always provide a query to search for.'''
    args_schema: Type[BaseModel] = WebSearchInput
    working_dir:str = None
    search_queries: list = None
    downloaded: dict = None


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_queries = kwargs.get('search_queries', [])
        self.downloaded = kwargs.get('downloaded', {})
        self.working_dir = kwargs.get('working_dir', ".cache/tmp_case")

    def getUrlHash(url):
        return hashlib.md5(url.encode()).hexdigest()    

    def download(url, hash):
            response = requests.get(url, timeout=15, stream=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome"})
            mimetype = response.headers.get('Content-Type').split(";")[0]
            if response.status_code == 200:
                if mimetype == "text/html":
                    with open(f".cache/tmp_case/{hash}", "w", encoding="utf-8") as out_file:
                        out_file.write(response.text)
                else:
                    with open(f".cache/tmp_case/{hash}", "wb") as out_file:
                        shutil.copyfileobj(response.raw, out_file)
            else:
                print(f"Error downloading file: {response.status_code}")
            return {"url": url, "hash": hash, "mimetype": mimetype, "filename": f".cache/tmp_case/{hash}", "status_code": response.status_code}

    def downloadResults(self, results):
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for result in results[1]["results"]:
                urlHash = ResearchWebSearchTool.getUrlHash(result["url"])
                if urlHash in self.downloaded.keys():
                    print("Already downloaded", result["url"])
                    continue
                else:
                    future = executor.submit(ResearchWebSearchTool.download, result["url"], urlHash)
                    futures.append(future)
                    self.downloaded[urlHash] = future
class WebSearchInput(BaseModel):
    query: str = Field(description="query to search the web for")

class ResearchWebSearchTool(BaseTool):
    name = 'WebSearchTool'
    description = '''Tool to search the web for relevant information to be used in the research case.
    Always provide a query to search for.'''
    args_schema: Type[BaseModel] = WebSearchInput
    search_queries: list = None
    working_dir:str = None
    search_results: list = None
    downloaded: dict = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_queries = kwargs.get('search_queries', [])
        self.working_dir = kwargs.get('working_dir', ".cache/tmp_case") 
        self.search_results = kwargs.get('search_results', [])
        self.downloaded = kwargs.get('downloaded', {})

    def getUrlHash(url):
        return hashlib.md5(url.encode()).hexdigest()    

    def download(url, hash):
            response = requests.get(url, timeout=15, stream=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome"})
            mimetype = response.headers.get('Content-Type').split(";")[0]
            if response.status_code == 200:
                if mimetype == "text/html":
                    with open(f".cache/tmp_case/{hash}", "w", encoding="utf-8") as out_file:
                        out_file.write(response.text)
                else:
                    with open(f".cache/tmp_case/{hash}", "wb") as out_file:
                        shutil.copyfileobj(response.raw, out_file)
            else:
                print(f"Error downloading file: {response.status_code}")
            return {"url": url, "hash": hash, "mimetype": mimetype, "filename": f".cache/tmp_case/{hash}", "status_code": response.status_code}

    def downloadResults(self, results):
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for result in results[1]["results"]:
                urlHash = ResearchWebSearchTool.getUrlHash(result["url"])
                if urlHash in self.downloaded.keys():
                    print("Already downloaded", result["url"])
                    continue
                else:
                    future = executor.submit(ResearchWebSearchTool.download, result["url"], urlHash)
                    futures.append(future)
                    self.downloaded[urlHash] = future
                    
            # Collect results
            for future in futures:
                try:
                    result = future.result()
                    self.downloaded[result["hash"]] = result
                    print(f"Downloaded: {result['url']} with MIME type: {result['mimetype']}")
                except Exception as e:
                    print(f"Error downloading file: {e}")


    def _run(self, query:str) -> str:
        self.search_queries.append(query)
        if pathlib.Path(f"{self.working_dir}/search_results.json").exists():
            with open(f"{self.working_dir}/search_results.json", "r") as f:
                results = json.load(f)
                print("Loaded search results from file: ", f"{self.working_dir}/search_results.json")
        else:
            try: 
                search = TavilySearchResults(max_results=10)
                results = search._run(query)
                with open(f"{self.working_dir}/search_results.json", "w") as f:
                    json.dump(results, f, indent=4)
            except Exception as e:
                return f"Error occured while searching the web. {e}"
            
        self.search_results.append({
            'question': query,
            'results': results,
        })
        self.downloadResults(results)
        return "results added to ragtool ready for search !"

        # future = executor.submit(ResearchWebSearchTool.download, result["url"], urlHash)
        # futures.append(future)
        # self.caseBuilder.downloaded[urlHash] = future
            
        # # Collect results
        # for future in futures:
        #     try:
        #         result = future.result()
        #         self.caseBuilder.downloaded[result["hash"]] = result
        #         print(f"Downloaded: {result['url']} with MIME type: {result['mimetype']}")
        #     except Exception as e:
        #         print(f"Error downloading file: {e}")


    def _run(self, query:str) -> str:
        self.search_queries.append(query)
        if pathlib.Path(f"{self.working_dir}/search_results.json").exists():
            with open(f"{self.working_dir}/search_results.json", "r") as f:
                results = json.load(f)
                print("Loaded search results from file: ", f"{self.working_dir}/search_results.json")
        else:
            try: 
                search = TavilySearchResults(max_results=10)
                results = search._run(query)
                with open(f"{self.working_dir}/search_results.json", "w") as f:
                    json.dump(results, f, indent=4)
            except Exception as e:
                return f"Error occured while searching the web. {e}"
            
        self.search_results.append({
            'question': query,
            'results': results,
        })
        self.downloadResults(results)
        return "results added to ragtool ready for search !"
