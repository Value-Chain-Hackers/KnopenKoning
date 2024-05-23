import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.llms.ollama import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

knowledge_extraction_prompt = PromptTemplate.from_template("""\
Please proceed to knowledge extraction from the provided text. Focus on the following aspects:
    1. Identify the key suppliers and customers of the company.
    2. Identify the raw materials used by the company and their sources.
    3. Idenitfy the locations of the company's manufacturing plants.
    4. Identify the routes used by the company to distribute its products.
    5. Identify the sustainability practices of the company.
    6. Identify the use of poluants and environmentally impactful materials.
    7. Identify the company's carbon footprint and energy consumption.
    8. Identify the company's waste management practices.
    9. Identify the company's recycling practices.
    10. Identify the company's water usage and management practices.
    11. Identify the company's social responsibility practices.
    12. Identify the company's labor practices.
    13. Identify the company's human rights practices.

If none of the above aspects are present in the text, please respond with "Not relevant".
Keep your answers concise and to the point. 
Do not include any irrelevant information, nor any information that is not present in the text.
-----
Context:
                                      
{chunk}

----- 
""")


def split_text_into_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size=4000,
        chunk_overlap=256,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_text(text)

def extract_text_from_pdf(pdf_path):
    # Open the PDF file
    document = fitz.open(pdf_path)
    text = ""
    
    # Iterate through each page
    for page_num in range(len(document)):
        page = document.load_page(page_num)  # Load the page
        text += page.get_text()  # Extract text from the page
    
    return text

def extract_all_knowledge_from_pdf(pdf_path, output_path):
    text = extract_text_from_pdf(pdf_path)
    chunks = split_text_into_chunks(text)
    llm = Ollama(model="phi3:latest", num_ctx=4096, num_predict=2048, temperature=0.1)
    chain = knowledge_extraction_prompt | llm | StrOutputParser()
    knowledge = []
    with open("output.txt", "a", encoding='utf-8') as f:
        for chunk in chunks:
            response = chain.invoke({"chunk": chunk})
            knowledge.append(response)
            f.write(response + "\n")
            f.write("-----\n")

    return knowledge