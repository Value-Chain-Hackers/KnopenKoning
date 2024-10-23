from abc import ABC, abstractmethod
import hashlib
import json
from operator import itemgetter
import os
from textwrap import dedent
import traceback
from typing import Dict, Any, List, Optional, Type, Union, get_args, get_origin
from pydantic import BaseModel, ValidationError

from langchain.prompts import PromptTemplate
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain.output_parsers.retry import RetryWithErrorOutputParser
from langchain_ollama.chat_models import ChatOllama
from langchain_core.runnables import RunnableParallel
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_ollama.chat_models import ChatOllama
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import hashlib

import torch
import yaml

from callbacks import ResearchProcessCallback
from models import *
import wikipedia

from logging import getLogger

from steps.agents import AgentWorkflowStep
from steps.base import WorkflowStep, NoopWorkflowStep
from steps.llm import PromptFormattingMixin, DefaultWorkflowStep

from utils import WebCache, WebDownloader
logger = getLogger(__name__)

from langchain.indexes import SQLRecordManager, index
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_transformers import BeautifulSoupTransformer


class InformationRepository:
    vectorstore: Chroma
    def __init__(self, persist_directory: str):
        self.documents = {}
        encode_kwargs = {'normalize_embeddings': False}
        self.hf = HuggingFaceEmbeddings(
            model_name= "BAAI/bge-large-en-v1.5",
            model_kwargs={
                "device": "cuda" if torch.cuda.is_available() else "cpu"
            },
            encode_kwargs=encode_kwargs
        )
        self.vectorstore = Chroma(persist_directory=persist_directory, embedding_function=self.hf)
        database_filename = os.path.join(persist_directory, "records.db")
        if os.path.exists(database_filename):
            self.record_manager = SQLRecordManager(
                "namespace", db_url=f"sqlite:///{database_filename}"
            )
        else:
            self.record_manager = SQLRecordManager(
                "namespace", db_url=f"sqlite:///{database_filename}"
            )
            try:
                self.record_manager.create_schema()
            except:
                pass
            
            
    def index(self, data: List[Dict[str, Any]]):
        logger.debug(f"Indexing {len(data)} documents")
        all_content = [item.get("content", "Unknown") for item in data]
        all_metadata = [{"source_name": item.get("source_name", "Unknown"), "url": item.get("url", "Unknown"), "source_id": hashlib.md5(item.get("url", "Unknown").encode()).hexdigest()} for item in data]
        splitter = RecursiveCharacterTextSplitter(
            # Set a really small chunk size, just to show.
            chunk_size=768,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )
        all_docs = splitter.create_documents(all_content, all_metadata)
        result = index(all_docs, self.record_manager, self.vectorstore, batch_size=20, source_id_key="source_id")
        logger.error(f"Added {len(all_content)} with ids: {result}")

class BeamerWorkflowStep(WorkflowStep, PromptFormattingMixin):
    llms: List[ChatOllama] = None
    
    def __init__(self, state_data: Dict[str, Any], step_data: StepModel, callback: Optional[ResearchProcessCallback] = None, **kwargs):
        super().__init__(state_data, step_data, callback, **kwargs)
        self.ollama_host = kwargs.get("ollama_host", step_data.args.get("ollama_host", "http://localhost:11434"))
        self.ollama_num_ctx = kwargs.get("ollama_num_ctx", step_data.args.get("ollama_num_ctx", 8000))
        
        self.evaluation_model_name = kwargs.get("evaluation_model_name", step_data.get("evaluation_model_name", "llama3.1:8b"))
        self.model_names = kwargs.get("model_names", step_data.args.get("model_names", []))
        
        self.prompt = kwargs.get("prompt", step_data.args.get("prompt", "You  are a helpful AI assistant."))
        
        self.prompt_template = PromptTemplate.from_template(dedent("""\
            ## Instructions:
            {instructions}
            
            ## Inputs:
            {inputs}
            
            ## Expected Output:
            The output should be a JSON object with the following structure:
            {output_format}
            DO only provide the data requested in the output format. Do not include any additional information.
            Make sure your response respects the output format defined in Expected Output.
            DO not refer to the data formats nor the models used in the input data.
            DO NOT use any commenting style in the output, the output should be a valid JSON object.
            
            """))
    
        self.evaluation_prompt_template = PromptTemplate.from_template(dedent("""\
            ## Instructions:
            Below are the results from differentlanguage models. You need to evaluate the Inputs and combine them into a single output.
            Please refer to the task description and the input data and evaluate the outputs accordingly.
            You can merge/select/combine any elements from the Inputs in any way you see fit.
            Make sure your response respects the output format defined in Expected Output.
            DO not refer to the data formats nor the models used in the input data.
            
            ## Task Description:
            {instructions}
            
            ## Inputs:
            {inputs}
            
            ## Expected Output:
            The output should be a JSON object with the following structure:
            ```json
            {output_format}
            ```
            DO only provide the data requested in the output format. Do not include any additional information.
            """))

        chains= {}
        for model_name in self.model_names:
            chains[model_name] = self.prompt_template | ChatOllama(model=model_name, base_url=self.ollama_host) | SimpleJsonOutputParser(pydantic_object=self.output_model_cls)
        self.chain = RunnableParallel(chains)
        self.evaluation_llm = ChatOllama(model=self.evaluation_model_name, base_url=self.ollama_host)
        self.evalutaion_chain = self.evaluation_prompt_template | self.evaluation_llm
        
    def _execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        merged_data = {
            **context_data, **input_data
        }
        
        formatted_instructions = PromptTemplate.from_template(dedent(self.prompt)).format(**merged_data)
        formatted_input_data = self.generate_prompt_input(input_data)
        expected_output_format = self.generate_prompt_output_description()

        prompt_data = {"instructions": formatted_instructions, "inputs": formatted_input_data, "output_format": expected_output_format}
        ai_response = self.chain.invoke(prompt_data)
        
        formatted_input_data = []
        for model_name, response in ai_response.items():
            formatted_input_data.append(f"### {model_name} Output:")
            formatted_input_data.append(json.dumps(response, indent=4))
            formatted_input_data.append("\n")   

        eval_prompt_data = {"instructions": formatted_instructions, "inputs": "\n".join(formatted_input_data), "output_format": expected_output_format}
        ai_response = self.evalutaion_chain.invoke(eval_prompt_data)
        retry_parser = RetryWithErrorOutputParser.from_llm(parser=SimpleJsonOutputParser(pydantic_object=self.output_model_cls), llm=self.evaluation_llm, max_retries=3)
        try:
            ai_response = retry_parser.parse_with_prompt(ai_response.content, self.evaluation_prompt_template.format(**eval_prompt_data))
        except Exception as e:
            raise ValueError(f"Output data validation failed:")
        return ai_response

class IterateWorkflowStep(WorkflowStep):
    def __init__(self, state_data: Dict[str, Any], step_data: Dict[str, Any], callback: Optional[ResearchProcessCallback] = None, **kwargs):
        super().__init__(state_data, step_data, callback, **kwargs)
        self.input_key = kwargs.get("input_key", step_data.get("input_key", "None"))
        self.child_step = step_data.get("steps", None)[0]

    def _execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        pass



    def execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        child_data = input_data.get(self.input_key, None)
        if child_data is None:
            raise ValueError(f"Selected field {self.input_key} not found in input data.")

        child_step = workflow_step_factory(self.child_step, self.state, self.callback)
        child_results = []
        for data in child_data:
            result = child_step.execute(data, context_data)
            if result is not None:
                child_results.append(result)
        if len(child_results) == 0:
            return None
        return child_results

class GatherInformation(DefaultWorkflowStep):
    def __init__(self, state_data: Dict[str, Any], step_data: StepModel, callback: Optional[ResearchProcessCallback] = None, **kwargs):
        super().__init__(state_data, step_data, callback, **kwargs)
        self.info_repo: InformationRepository = state_data.get("information_repository", None)
    
    def _execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        input_data:RefinedObjective = RefinedObjective(**input_data)
        retriever = self.info_repo.vectorstore.as_retriever()
        template = dedent("""You are a helpful assistant that generates multiple search queries based on a single input query. \n
Generate multiple search queries related to the question {question} \n
Only provide the search queries one per line, without any additional information or text. \n
Do not number the queries. \n
Output (4 queries):""")
        prompt_rag_fusion = ChatPromptTemplate.from_template(template)
        answer_parser = JsonOutputParser(pydantic_object=QuestionAnswered)
        outut_format = answer_parser.get_format_instructions()
        template_rag_answer = dedent("""\
            ## Instructions:            
            Answer the following question using only the documents in the context.
            DO ALWAYS mention the document id that you used to answer the question.
            
            If there is no explicit answer in the context, reply with "No Answer". without any additional information or text.
            Make sure you output the initial question in the answer.

            Question: {question}    
            
            ## Context:
            {context}
            
            ## Format of answer:
            
            {answer_output_format}
            
            DO ONLY output the data requested in the output format. Do not include any additional information or text.
            
            ## Output:
            
            """)
        
        prompt_rag_answer = ChatPromptTemplate.from_template(template_rag_answer)
        generate_queries = (
            prompt_rag_fusion 
            | self.llm
            | StrOutputParser() 
            | (lambda x: x.split("\n"))
        )
        
        def format_result(docs: List[tuple[Document, float]]):
            return "\n\n".join([f"ID: {doc.metadata.get('source_id')} - Score: ({round(score, 2)}) - Title: {doc.metadata.get('source_name')}\n{doc.page_content}" for doc, score in docs])
        
        retrieval_chain_rag_fusion = generate_queries | retriever.map() | self.reciprocal_rank_fusion | format_result
        
        ppdata ={"context": retrieval_chain_rag_fusion, "answer_output_format": itemgetter("answer_output_format"),
            "question": itemgetter("question")} 
        final_rag_chain = (ppdata | prompt_rag_answer | self.llm)
        answers = []
        retry = RetryWithErrorOutputParser.from_llm(parser=SimpleJsonOutputParser(pydantic_object=QuestionAnswered), llm=self.llm)
        for sub_question in input_data.sub_questions:
            logger.debug(f"SubQuestion: {sub_question}", )
            try:
                qdata = {"question": sub_question, "answer_output_format": outut_format}
                result = final_rag_chain.invoke(qdata)
                logger.debug(f"{result.content}")   
                parsed = retry.parse_with_prompt(result.content, prompt_rag_answer.format_prompt(**ppdata))
                answers.append(parsed)
                logger.debug(f"Question:{sub_question}\nAnswer:{result}")
            except Exception as e:
                logger.error(f"Failed to get answer for {sub_question}. {e} {traceback.format_exc()}")
        output = {"refined_objective":input_data.model_dump(), "answered_questions":answers}
        return output

    def reciprocal_rank_fusion(self, results: list[list], k=4):
        """ Reciprocal_rank_fusion that takes multiple lists of ranked documents 
            and an optional parameter k used in the RRF formula """
        from langchain.load import dumps, loads
        # Initialize a dictionary to hold fused scores for each unique document
        fused_scores = {}

        # Iterate through each list of ranked documents
        for docs in results:
            # Iterate through each document in the list, with its rank (position in the list)
            for rank, doc in enumerate(docs):
                # Convert the document to a string format to use as a key (assumes documents can be serialized to JSON)
                doc_str = dumps(doc)
                # If the document is not yet in the fused_scores dictionary, add it with an initial score of 0
                if doc_str not in fused_scores:
                    fused_scores[doc_str] = 0
                # Retrieve the current score of the document, if any
                previous_score = fused_scores[doc_str]
                # Update the score of the document using the RRF formula: 1 / (rank + k)
                fused_scores[doc_str] += 1 / (rank + k)
        
        # Sort the documents based on their fused scores in descending order to get the final reranked results
        reranked_results = [
            (loads(doc), score)
            for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        ]
        # Return the reranked results as a list of tuples, each containing the document and its fused score
        return reranked_results
    
class GetWikipediaPages(WorkflowStep):
    cache = WebCache()
    transformer = BeautifulSoupTransformer()
    def __init__(self, state_data: Dict[str, Any], step_data: StepModel, callback: Optional[ResearchProcessCallback] = None, **kwargs):
        super().__init__(state_data, step_data, callback, **kwargs)
        logger.debug("Initializing GetWikipediaPages")
        logger.debug(f"State Data: {state_data}")
        self.info_repo: InformationRepository = state_data.get("information_repository", None)
        
    def execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        logger.debug(f"Executing GetWikipediaPages")
        wikipages:List[str] = input_data.get("potential_wikipedia_pages", [])
        collected_pages = []
        collected_urls = []
        output_data = input_data.copy()
        logger.debug(f"Found {len(wikipages)} wikipedia pages.")
        for page in wikipages:
            try:
                page = wikipedia.page(page, preload=True)
                collected_pages.append(page.url)
            except Exception as e:
                logger.error(f"Failed to get summary for {page}.")
                continue
            all_links = page.references
            
            other_wiki_pages = [link for link in all_links if not link.strip().startswith("http://") and not link.strip().startswith("https://")]
            logger.error(f"Found {len(other_wiki_pages)} other wikipedia pages.")
            
            # remove links that are from https://web.archive.org
            all_links = [link for link in all_links if "https://web.archive.org" not in link]
            all_links = list(set(all_links))
            logger.debug(f"Found {len(all_links)} references for {page}")  
            downloader = WebDownloader(all_links, self.cache)
            downloader.start_download()
            to_index = []
            to_index.append({"source_name":f"Wikipedia - {page}", "summary":page.summary, "url":page.url, "content":page.content}) 
            
            for link in all_links:
                logger.debug(f"Gettng reference: {link}")
                content, extension = self.cache.get(link)
                collected_urls.append(link)
                if content is None:
                    continue
                if extension == "html":
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    if soup.title is None:
                        title = f"Page {link}"
                    else:
                        title = soup.title.string
                    
                    if isinstance(content, bytes):
                        content = content.decode(errors="ignore")
                    hash = hashlib.md5(content.encode()).hexdigest()
                    text = self.transformer.transform_documents([Document(page_content=content, metadata={ "source_name":f"{title}", "summary":"", "url":link, "source_id": hash } )], 
                            remove_comments=True,
                            tags_to_extract=["p", "li", "div", "a"], 
                            unwanted_tags=["menu", "script", "style", "noscript", "svg", "img", "figure", "figcaption", "footer", "header", "nav", 
                                           "aside", "form", "input", "button", "select", "option", "textarea", "label", "fieldset", "legend", "iframe", 
                                           "video", "audio", "source", "track", "canvas", "map", "area", "object", "param", "embed", "applet", "frame", 
                                           "frameset", "noframes", "footer", "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption", "col", "colgroup",])
                    #text = soup.get_text(separator=" ", strip=True)
                    to_index.append({"source_name":f"{title}", "summary":"", "url":link, "content": text[0].page_content, "source_id": hash}) 
                    pass
                elif extension == "pdf":
                    with open("search_data/temp.pdf", "wb") as f:
                        f.write(content)
                    import pymupdf
                    doc = pymupdf.open("search_data/temp.pdf")
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    doc.close()
                    os.remove("search_data/temp.pdf")
                    
                    hash = hashlib.md5(text.encode()).hexdigest()
                    to_index.append({"source_name":f"PDF - {link}", "summary":"", "url":link, "content": text, "source_id": hash})
                    logger.info(f"Indexed PDF {len(text)}")
                    continue
                else:
                    logger.warn(f"Unkonwn mime type: {extension}")
                    continue
                
        self.info_repo.index(to_index)
        output_data["wikipedia_pages"] = collected_pages
        output_data["downloaded_pages"] = list(set(collected_urls))
        return output_data
    
    def _execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        pass
    
class WriteReport(WorkflowStep):
    
    def __init__(self, state_data: Dict[str, Any], step_data: StepModel, callback: Optional[ResearchProcessCallback] = None, **kwargs):
        super().__init__(state_data, step_data, callback, **kwargs)
        self.output_file = kwargs.get("output_file", step_data.args.get("output_file", "report.md"))
        self.info_repo: InformationRepository = state_data.get("information_repository", None)
        
    def execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        with open("report_inputs.yaml", "w") as f:
            yaml.dump(input_data, f)
        with open("report_context.yaml", "w") as f:
            yaml.dump(context_data, f)
            
        report = FinalReport.model_validate(input_data)
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(f"# Report : {context_data.get('title')}\n\n")
            
            f.write(f"**Executive Summary**\n\n {report.executive_summary}\n\n")
            
            for section in report.sections:
                f.write(f"\n## {section.title}\n\n")
                f.write(f"{section.summary}\n\n")
                
                for paragraph in section.content:
                    f.write(f"{paragraph}\n\n")
                
                if section.potential_charts:
                    for chart in section.potential_charts:
                        f.write(f"- {chart}\n")
                        
            gathering = context_data.get("InitialGathering")
            answered_questions = gathering.get("answered_questions", [])
            for question in answered_questions:
                f.write(f"### Question: {question['question']}\n\n")
                f.write(f"Answer: {question['answer']}\n\n")
                
            
            collected = context_data.get("CollectWikipediaData")
            wikipedia = collected.get("wikipedia_pages", [])
            f.write(f"### Wikipedia Pages:\n\n")
            for page in wikipedia:
                f.write(f"[{page}]({page})\n")
                
            downloaded = collected.get("downloaded_pages", [])
            f.write(f"### Downloaded Pages:\n\n")
            for page in downloaded:
                f.write(f"[{page}]({page})\n")
        return report
    def _execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
        pass
    
        
# class BranchWorkflowStep(WorkflowStep):
#     def __init__(self, state_data: Dict[str, Any], step_data: Dict[str, Any], callback: Optional[ResearchProcessCallback] = None, **kwargs):
#         super().__init__(state_data, step_data, callback, **kwargs)
#         self.branches = step_data.get("branches", [])
        
#     def _execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
#         pass

#     def execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
#         pass

# class ConditionalWorkflowStep(WorkflowStep):
#     def __init__(self, state_data: Dict[str, Any], step_data: Dict[str, Any], callback: Optional[ResearchProcessCallback] = None, **kwargs):
#         super().__init__(state_data, step_data, callback, **kwargs)
#         self.condition = step_data.get("condition", None)
#         self.true_step = step_data.get("true_step", None)
#         self.false_step = step_data.get("false_step", None)
        
#     def _execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
#         pass

#     def execute(self, input_data: Dict[str, Any], context_data: Dict[str, Any]) -> BaseModel:
#         pass
    
def _get_step_class(step_name: str, step_type: str) -> Type[WorkflowStep]:
        """
        Get the workflow step class to use. 
        This method can be overridden to provide custom logic for selecting step classes.

        Args:
            step_name (str): The name of the step.

        Returns:
            Type[WorkflowStep]: The workflow step class to use.
        """
        if step_type == "default":
            return DefaultWorkflowStep
        elif step_type == "beamer":
            return BeamerWorkflowStep
        elif step_type == "iterative":
            return IterateWorkflowStep
        elif step_type == "noop":
            return NoopWorkflowStep
        elif step_type == "agent":
            return AgentWorkflowStep
        else:
            try:
                logger.debug(f"Trying to get class {step_type}")
                # Dynamically retrieve the class by name
                return globals()[f"{step_type}"]
            except KeyError:
                logger.error(f"Step type {step_type} not found.")
                # If the class doesn't exist, default to DefaultWorkflowStep
                raise ValueError(f"Step type {step_type} not found.")
     
def workflow_step_factory(step_data: StepModel, state: Dict[str, Any], callback: Optional[ResearchProcessCallback] = None) -> WorkflowStep:
    step_class = _get_step_class(step_data.id, step_data.type)
    kwargs = step_data.args
    logger.debug(f"Creating step {step_data.id} of type {step_data.type}")
    step = step_class(state, step_data, callback, **kwargs)
    logger.debug(f"Created step {step_data.id} of type {step_data.type}")
    return step