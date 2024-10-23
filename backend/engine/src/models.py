from pydantic import BaseModel, Field, ValidationError
from typing import Any, Dict, List, Optional, Type

import yaml

# # define an enum for the step types
class StepMode(str):
    SEQUENTIAL = "sequential" # all steps are executed in sequence
    PARALLEL = "parallel" # all steps are executed in parallel
    ITERATIVE = "iterative" # steps are executed in sequence but the iterate over a list of inputs
    PARALLEL_ITERATIVE = "parallel_iterative" # steps are executed in parallel for each input in a list

# class StepInputOutputModel(BaseModel):
#     model: Type[BaseModel] | str = Field("str", description="The model class or name to use for the field.")
#     processors: Optional[List[str]] = Field(None, description="A list of processors to apply to the field.")
    
# class StepRetryModel(BaseModel):
#     max_retries: int = Field(3, description="The maximum number of retries for the step.")
#     retry_delay: int = Field(5, description="The delay between retries in seconds.")
#     retry_on: List[str] = Field(["Exception"], description="A list of exceptions to retry on.")

# class NextAction(str):
#     CONTINUE = "continue"
#     GOTO = "goto"
#     REPEAT = "repeat"
#     EXIT = "exit"

# class NextStepModel(BaseModel):
#     condition: Optional[str] = Field(..., description="The condition to evaluate.")
#     action: NextAction = Field(NextAction.CONTINUE, description="The action to take based on the condition.")
#     goto: Optional[str] = Field(None, description="The name of the step to go to.")
#     max_repeats: Optional[int] = Field(None, description="The maximum number of repeats.")
    
class StepModel(BaseModel):
    id: str = Field(..., description="The unique identifier for the step.")
    type: Type | str = Field("default", description="The type of the step (e.g., 'beamer', 'iterative').")
    description: Optional[str] = Field(..., description="A description of the step.")
    mode: Optional[str] = Field(StepMode.SEQUENTIAL, description="The mode of the step (e.g., 'sequential', 'parallel', 'iterative').")
    input_model: Optional[str] = Field("str", description="The name of the input model for the step.")
    output_model: Optional[str] = Field("str", description="The name of the output model for the step.")
    args: Optional[Dict[str, Any]] = Field({}, description="Additional arguments for the step.")
    steps: Optional[List['StepModel']] = Field([], description="A list of steps or step IDs to execute in sequence.")
    next_step: Optional[str] = Field(None, description="The name of the next step in the workflow.")
   
class WorkflowModel(BaseModel):
    name: str = Field(..., description="The name of the workflow.")
    description: Optional[str] = Field(..., description="A description of the workflow.")
    steps: List[StepModel] = Field(..., description="A list of steps in the workflow.")

StepModel.model_rebuild()

class SimpleTextModel(BaseModel):
    """
    A simple text model for testing purposes.
    """
    text: str = Field(..., description="A simple text field.")

class ResearchObjective(BaseModel):
    """
    Input model representing the initial research topic provided by the user.
    
    Attributes:
        topic (str): The main topic or question that the research will focus on.
        key_terms (List[str]): A list of key terms or concepts extracted from the topic.
        clarifying_questions (Optional[List[str]]): Additional questions to refine the scope.
    """
    topic: str = Field(..., description="The main topic or question that the research will focus on.")
    key_terms: List[str] = Field(..., description="A list of key terms or concepts extracted from the topic.")
    clarifying_questions: Optional[List[str]] = Field(None, description="Additional questions to refine the scope.")



class ReportOutlineSection(BaseModel):
    """
    Model representing a single section of the outline or a report.
    
    Attributes:
        title (str): The title of the outline section.
        description (str): The content of the report section.
    """
    title: str = Field(..., description="The title of the outline section.")
    description: str = Field("", description="The extended description to explain what this report item will contain.")
    points_to_cover: Optional[List[str]] = Field(None, description="A list of points/viewpoints to cover in this section.")
    sections: Optional[List['ReportOutlineSection']] = Field(None, description="A list of sub-sections within this section.")


class RefinedObjective(BaseModel):
    """
    Output model representing the refined research objective after initial processing.
    
    Attributes:
        topic (str): The main topic or question after refinement.
        refined_key_terms (List[str]): A refined list of key terms or concepts.
        sub_questions (List[str]): Sub-questions generated to guide the research.
    """
    topic: str = Field(..., description="The main topic or question after refinement.")
    refined_key_terms: List[str] = Field(..., description="A refined list of key terms or concepts.")
    sub_questions: List[str] = Field(..., description="Sub-questions generated to guide the research. Provide at least 10")
    overall_report_structure: Optional[List[ReportOutlineSection]|List[str]] = Field(None, description="An outline of the overall report structure. Provide at least 7 sections, including Introduction, Methodology and Conclusion.")
    potential_wikipedia_pages: Optional[List[str]] = Field(None, description="A list of potential Wikipedia pages related to the topic.")

class CollectedWikipediaData(BaseModel):
    """
    Output model representing the refined research objective after initial processing.
    
    Attributes:
        topic (str): The main topic or question after refinement.
        refined_key_terms (List[str]): A refined list of key terms or concepts.
        sub_questions (List[str]): Sub-questions generated to guide the research.
    """
    topic: str = Field(..., description="The main topic or question after refinement.")
    refined_key_terms: List[str] = Field(..., description="A refined list of key terms or concepts.")
    sub_questions: List[str] = Field(..., description="Sub-questions generated to guide the research. Provide at least 10")
    overall_report_structure: Optional[List[ReportOutlineSection]|List[str]] = Field(None, description="An outline of the overall report structure. Provide at least 7 sections, including Introduction, Methodology and Conclusion.")
    potential_wikipedia_pages: Optional[List[str]] = Field(None, description="A list of potential Wikipedia pages related to the topic.")

    wikipedia_pages: List[str] = Field(..., description="A list of Wikipedia pages related to the topic.")
    downloaded_pages: Optional[List[str]] = Field(None, description="A list of downloaded web pages for offline processing.")
    
class InformationSource(BaseModel):
    """
    Model representing an information source used in the research process.
    Attributes:
        document_id (Optional[str]): The unique identifier for the document.
        quote (Optional[str]): The quote from the document.
        url (Optional[str]): The URL of the source if available.
        summary (Optional[str]): A brief summary of the information extracted from the source.
    """
    document_id: Optional[str] = Field(..., description="The unique identifier for the document.")
    quote: Optional[str] = Field(..., description="The quote from the document.")
    url: Optional[str] = Field(None, description="The URL of the source if available.")
    summary: Optional[str] = Field("", description="A brief summary of the information extracted from the source.")

class QuestionAnswered(BaseModel):
    """
    Model representing a question and its answer.
    
    Attributes:
        question (str): The question.
        answer (str): The answer to the question.
    """
    question: str = Field(..., description="The question that is anwsered.")
    score: int = Field(..., description="The score of the answer between 1 and 10 .")
    answer: str = Field(..., description="The answer to the question. Explain the answer in detail.")
    document_ids: List[str] = Field([], description="A list of document IDs that where used or contains the answer.(required !)")

class InitialGatheringOutput(BaseModel):
    """
    Output model for the results of the initial information gathering stage.
    
    Attributes:
        refined_objective (RefinedObjective): The refined research objective.
        collected_information (List[InformationSource]): A list of information sources gathered.
    """
    refined_objective: RefinedObjective = Field(..., description="The refined research objective.")
    answered_questions: Optional[List[QuestionAnswered]] = Field(None, description="A list of questions answered during the gathering process.")

class Hypothesis(BaseModel):
    """
    Model representing a hypothesis formed based on gathered information.
    
    Attributes:
        hypothesis_text (str): The text of the hypothesis.
        supporting_evidence (Optional[List[InformationSource]]): A list of information sources supporting the hypothesis.
        contradicting_evidence (Optional[List[InformationSource]]): A list of information sources contradicting the hypothesis.
    """
    hypothesis_text: str = Field(..., description="The long description of the hypothesis, with detailed rationale about the cause and concequences.")
    supporting_evidence: Optional[List[InformationSource]|List[str]] = Field(None, description="A list of information sources supporting the hypothesis.")
    contradicting_evidence: Optional[List[InformationSource]|List[str]] = Field(None, description="A list of information sources contradicting the hypothesis.")

class HypothesisTestingOutput(BaseModel):
    """
    Output model representing the results of hypothesis formation and testing.
    
    Attributes:
        hypotheses (List[Hypothesis]): A list of hypotheses formed during the process.
        remaining_gaps (Optional[List[str]]): A list of remaining gaps or questions that need further investigation.
    """
    hypotheses: List[Hypothesis] = Field(..., description="A list of hypotheses formed during the process.")
    remaining_gaps: Optional[List[str]] = Field(..., description="the remaining gaps or questions that need further investigation as a list of strings.")
    additional_remarks: Optional[str] = Field(None, description="Additional remarks or insights from the hypothesis testing process.")

class FocusedResearchInput(BaseModel):
    """
    Input model for conducting a focused deep dive into specific aspects of the research.
    
    Attributes:
        hypotheses (List[Hypothesis]): A list of hypotheses guiding the deep dive.
        specific_areas_of_interest (List[str]): Specific areas or topics to focus on during the deep dive.
    """
    hypotheses: List[Hypothesis] = Field(..., description="A list of hypotheses guiding the deep dive.")
    specific_areas_of_interest: Optional[List[str]] = Field(None, description="Specific areas or topics to focus on during the deep dive.")

class FocusedResearchOutput(BaseModel):
    """
    Output model representing the results of the focused deep dive.
    
    Attributes:
        in_depth_information (List[InformationSource]): A list of in-depth information sources gathered.
        updated_hypotheses (List[Hypothesis]): A list of updated hypotheses based on the new information.
    """
    summary: str = Field(..., description="A detailed summary of the focused research.")
    in_depth_information: List[InformationSource] = Field(..., description="A list of in-depth information sources gathered.")
    updated_hypotheses: List[Hypothesis] = Field(..., description="A list of updated hypotheses based on the new information.")

class SynthesisInput(BaseModel):
    """
    Input model for the synthesis and reasoning stage.
    
    Attributes:
        in_depth_information (List[InformationSource]): A list of in-depth information sources to be synthesized.
        hypotheses (List[Hypothesis]): A list of hypotheses to be connected and synthesized.
    """
    in_depth_information: List[InformationSource] = Field(..., description="A list of in-depth information sources to be synthesized.")
    hypotheses: List[Hypothesis] = Field(..., description="A list of hypotheses to be connected and synthesized.")

class SynthesisOutput(BaseModel):
    """
    Output model representing the results of the synthesis and reasoning stage.
    
    Attributes:
        conclusions (List[str]): A list of conclusions derived from the synthesis.
        synthesized_narrative (str): A synthesized narrative that ties together the research findings.
        identified_implications (Optional[List[str]]): A list of identified implications or insights from the research.
    """
    conclusions: List[str] = Field(..., description="A list of detailed and exhaustive conclusions derived from the synthesis.")
    synthesized_narrative: str = Field(..., description="A synthesized narrative that ties together the research findings.")
    identified_implications: Optional[List[str]] = Field(None, description="A list of identified implications or insights from the research.")


class ReportSection(BaseModel):
    """
    Model representing a single section of the draft report.
    
    Attributes:
        title (str): The title of the report section.
        content (str): The content of the report section.
    """
    title: str = Field(..., description="The title of the report section.")
    summary: Optional[str] = Field(None, description="A summary of this report section.")
    content: List[str] = Field("", description="The complete and very detailed content of the report section using markdown syntax. Use an array where each item is a paragraph(at least 5 paragraphs of 10+ sentences).")
    potential_charts: Optional[List[str]] = Field(None, description="A list of potential charts or visualizations to include in the section.")

class DraftReport(BaseModel):
    """
    Output model representing the draft report generated after synthesis.
    
    Attributes:
        title (str): The title of the report.
        sections (List[ReportSection]): A list of sections that make up the report.
        draft_complete (bool): A flag indicating whether the draft is complete.
    """
    title: str = Field(..., description="The title of the report.")
    sections: List[ReportSection] = Field(..., description="A list of sections that make up the report.")

class RefinedReport(BaseModel):
    """
    Output model representing the refined report after review and feedback.
    
    Attributes:
        title (str): The title of the refined report.
        sections (List[ReportSection]): A list of refined sections of the report.
        final_complete (bool): A flag indicating whether the final report is complete.
        implemented_feedback (Optional[str]): A description of the feedback implemented in the final report.
    """
    title: str = Field(..., description="The title of the refined report.")
    sections: List[ReportSection] = Field(..., description="A list of refined sections of the report.")
    implemented_feedback: Optional[str] = Field(None, description="A description of the feedback implemented in the final report.")

class FinalReport(BaseModel):
    """
    Output model representing the final version of the research report.
    
    Attributes:
        title (str): The title of the final report.
        sections (List[ReportSection]): A list of sections included in the final report.
        executive_summary (Optional[str]): An optional executive summary for the report.
        format (str): The format in which the report is generated (e.g., 'PDF', 'Word', 'Web').
    """
    title: str = Field(..., description="The title of the final report.")
    sections: List[ReportSection] = Field(..., description="A list of sections included in the final report.")
    executive_summary: str = Field(None, description="An executive summary for the report.")
    format: str = Field(..., description="The format in which the report is generated (e.g., 'PDF', 'Word', 'Web').")

class Feedback(BaseModel):
    """
    Input model for collecting feedback on the final report.
    
    Attributes:
        report_id (str): The unique identifier for the report.
        user_feedback (str): Feedback provided by the user on the report.
        suggestions (Optional[List[str]]): Optional suggestions for improving future reports.
    """
    report_id: str = Field(..., description="The unique identifier for the report.")
    user_feedback: str = Field(..., description="Feedback provided by the user on the report.")
    suggestions: Optional[List[str]] = Field(None, description="Optional suggestions for improving future reports.")

class LearningLoopOutput(BaseModel):
    """
    Output model representing the result of the feedback and learning loop process.
    
    Attributes:
        enhanced_model_version (str): The version identifier for the enhanced AI model.
        improvements_summary (Optional[str]): A summary of improvements made based on feedback.
    """
    enhanced_model_version: str = Field(..., description="The version identifier for the enhanced AI model.")
    improvements_summary: Optional[str] = Field(None, description="A summary of improvements made based on feedback.")


model_registry = {
    "ResearchObjective": ResearchObjective,
    "RefinedObjective": RefinedObjective,
    "InitialGatheringOutput": InitialGatheringOutput,
    "HypothesisTestingOutput": HypothesisTestingOutput,
    "FocusedResearchOutput": FocusedResearchOutput,
    "SynthesisOutput": SynthesisOutput,
    "DraftReport": DraftReport,
    "RefinedReport": RefinedReport,
    "FinalReport": FinalReport,
    "Feedback": Feedback,
    "LearningLoopOutput": LearningLoopOutput,
    "SimpleTextModel": SimpleTextModel,
    "CollectedWikipediaData": CollectedWikipediaData
}