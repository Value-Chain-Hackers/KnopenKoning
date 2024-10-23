from callbacks import CallbackManager, StdOutPrintProcessCallback
from process import ResearchProcess
import setup_logging
from models import *


if __name__ == "__main__":

    callback_manager = CallbackManager([
        StdOutPrintProcessCallback()
    ])
    # Initialize the research process
    process = ResearchProcess(workflow_path='./src/research_process.yaml', model_registry=model_registry, callback=callback_manager)

    # Palital Feed Additives : Identify the key countries where Palital Feed Additives sources its raw materials from.
    # Vlastuin CDI : Which multi-nationals are likely end customers of Vlastuin CDI.
    # DORC International BV : What are the most likely customers of DORC International BV in the Netherlands.
    # Zeiss : Identify the key dependencies of Zeiss on the Chinese components market.
    

    # Set initial input for the first step
    # process.set_input("DefineObjective", {
    #     "topic": "DORC International BV : What are the most likely customers of DORC International BV in the Netherlands.",
    #     "key_terms": ["DORC International BV","customers of DORC International BV","Netherlands"]
    # })
    
    
    process.set_input("DefineObjective", {
        "topic": "How can we improve the sustainability of the supply chain for toilet paper?",
        "key_terms": ["supply chain","toilet paper", "sustainability"]
    })
    
    
    # process.set_input("DefineObjective", {
    #     "topic": "Vlastuin CDI: Which multi-nationals are likely end customers of Vlastuin CDI.",
    #     "key_terms": ["Vlastuin CDI","multi-nationals", "end-customers"]

    # })
    # process.set_input("DefineObjective", {
    #     "topic": "Zeiss : Identify the key dependencies of Zeiss on the Chinese components",
    #     "key_terms": ["Zeiss","dependency", "Chinese components"]

    # })

    # Run the entire process
    process.run()
  