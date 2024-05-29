# KnopenKoning
Master your supply chain, untangling every challenge.



## Installation
```bash

python -m venv .venv    

#windows
.venv\Scripts\activate  

# linux
source .venv/bin/activate


python -m pip install -r requirements.txt
``` 


## Building the rag index
```bash
python build_rag.py
python build_knowledge.py
```


## Running the app
```bash
python backend/main.py
```


```mermaid

graph LR
    subgraph Collect
    PDF[PDF\nannual reports] --> Store
    Crawling[
        Crawling:\nWeb Site\nBrand Site\nProduct Pages
    ] --> Store
    SEC[
        US SEC\nFilings\n10-K\n10-Q
    ] --> Store
    Wikipedia[Wiki\nCompany Pages\nIngrediens\nChemicals] --> Store

    DuckDuckGo[Search\nDuckDuckGo] --> Store

    Store --> Ingestion['Processing\nIngestion']
    end
    subgraph Ingest
        Ingestion --> Transform <--> Extract[Extract:\n Nodes, Edges]
        Transform <--> Structurize[Structurize:\n CSV, JSON, Markdown]
        Transform --> Embeddings
        Structurize --> Knowledge
    end
    subgraph Knowledge
        Transform --> LLM
        Extract <--> IndexGraph
        Extract <--> IndexFact
        LLM --> Structurize
    end
    RAG --> Retrievers
    subgraph GraphDatabase
        IndexGraph[Graph\nNodes\nLinks] --> Neo4j 
        RAG --> Neo4j
    end
    subgraph FactDatabase
        IndexFact --> Sqlite 
        IndexFact --> Markdown
        Markdown --> RAG
        Sqlite --> RAG
    end

    subgraph VectorStores
        Embeddings --> Faiss
        Embeddings --> Chroma
        Faiss --> RAG
        Chroma --> RAG
    end



    subgraph UI
       
        UIAI --> Query --> Retrievers --> Results --> Visualize
        Query --> Visualize
    end


```

### Welke Leverenciers leveren nou aan wie? Supplychain map.
### Een entiteit als node pakken, dat betekend unilever aanzich ook al een entiteit is. 
### Formele juridische leverancier, maar je hebt ook de phyzieke leverancier. De administratie en de financiele stroom hoeft niet dezelfde mapping te hoeven zijn, een andere lens die je erover legt, kijk je naar de goederenstroom of de financiele stroom, dat maakt ook uit. 
### We hebben het over producten maar je kan het ook hebben over merknamen dat kan ook nog eens zien wat het is over unilever. 
### je kan het zien als een groep van entiteiten maar je kan het ook zien als een groep van... merkennamen, lipton, ola. Dus als je gaat zoeken, dan kan je daarop zoeken, ook de leveranciers van de merknamen. Switch to Scania.

