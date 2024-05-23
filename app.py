import streamlit as st
from langchain_chroma import Chroma
from utils.build_rag import get_huggingface_model

hf = get_huggingface_model("BAAI/bge-base-en-v1.5")
chroma = Chroma("docs",  embedding_function=hf, persist_directory="./.cache/chroma/docs")


def main():
    st.title("File Upload and Question Box")

    # File upload
    #uploaded_file = st.file_uploader("Choose a file", type=["csv", "txt", "xlsx", "pdf", "docx", "jpg", "png"])
    
    # if uploaded_file is not None:
    #     st.write(f"File {uploaded_file.name} uploaded successfully.")
        
    #     # You can add your file processing code here
    #     # For example, reading and displaying the content of a text file
    #     if uploaded_file.type == "text/plain":
    #         content = uploaded_file.read().decode("utf-8")
    #         st.text_area("File Content", content, height=250)

    # Question box
    question = st.text_input("Ask a question:")
    if question:
        docs = chroma.as_retriever().get_relevant_documents(question)
        if(docs):
            st.write(f"You asked: {question}\n Found {len(docs)} found.")
            st.write(docs)
        else:
            st.write("No relevant documents found.")
            
if __name__ == "__main__":
    main()
