import streamlit as st
import time
from utils.extract_knowledge import get_huggingface_model
from langchain_chroma import Chroma
from langchain_community.llms.ollama import Ollama
from langchain_core.prompts import PromptTemplate
from langchain.indexes import SQLRecordManager, index
# Initialize the retriever (ensure you replace this with your actual initialization)
hf = get_huggingface_model("BAAI/bge-base-en-v1.5")
chroma = Chroma("docs",  embedding_function=hf, persist_directory="./.cache/chroma/docs")
retriever = chroma.as_retriever(search_kwargs= {"k": 5})

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
llm = Ollama(model="phi3:instruct", num_ctx=4096, num_predict=2048, temperature=0.1, base_url="http://ollama:11434/")
prompt = PromptTemplate.from_template("Please answer the following question: {question}\nUse only the information provided in the context below to answer the question.\nContext:\n{context}")
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

def get_answer(question):
    answer = rag_chain.invoke(question)
    return answer

def main():
    st.title("Ask the AI a question about the supply chain of Unilever!")

    # Question box
    question = st.text_input("Ask a question:")
    if question:
        with st.spinner('Retrieving answer...'):
            answer = get_answer(question)
            st.write(answer)

if __name__ == "__main__":
    main()
