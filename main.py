from utils import extract_all_knowledge_from_pdf, summarize_all_text, extract_knowledge_graph

allknowledge = extract_all_knowledge_from_pdf("unilever-annual-report-and-accounts-2023.pdf", "output.txt")

# join all the knowledge into a single string
allknowledge_str = "\n".join(allknowledge)

summarized_knowledge = summarize_all_text(allknowledge_str, "output_summary.txt")

knowledge_graph = extract_knowledge_graph(allknowledge_str, "output_graph.json")