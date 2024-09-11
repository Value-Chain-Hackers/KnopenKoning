# KnopenKoning
Master your supply chain, untangling every challenge.

## Documetation 

 - Install quarto from [Quarto](https://quarto.org/docs/download/)
 ```bash
    quarto install tinytex
    quarto render docs --format pdf
 ```

# Docker installation
docker buildx build -f ./Dockerfile.Frontend    -t vch_frontend:latest .
docker buildx build -f ./Dockerfile.Backend     -t vch_backend:latest . 

Will be exposed on port 3000;

if you use traefic, use the docker-compose.traefic



## Installation

Install python from [Python](https://www.python.org/downloads/)
Install node from [Node](https://nodejs.org/en/download/)
Install mongodb from [MongoDB](https://www.mongodb.com/try/download/community)
Install mysql from [MySQL](https://dev.mysql.com/downloads/installer/)

Check and update .env file with the correct database connection strings and urls.

```bash

### backend requirements
```bash
python -m venv .venv    

#windows
.venv\Scripts\activate  

# linux
source .venv/bin/activate

python -m pip install -r requirements.txt

# create the mysql database
python create_db.py

``` 

### frontend requirements

```bash
cd tsfrontend
npm install
```


## Running the app
```bash
python backend/main.py
```



```mermaid

graph TD

    Input --> llm
    llm --> response
    response --> llm2
    llm2 --> llm
    llm2 --NO--> llm3
    llm2 --Yes--> llm4

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


Current Status



```mermaid

graph LR
    style Collect fill:#ff6347,stroke:#333,stroke-width:2px
    style Ingest fill:#ffa500,stroke:#333,stroke-width:2px
    style Knowledge fill:#ffff00,stroke:#333,stroke-width:2px
    style GraphDatabase fill:#008000,stroke:#333,stroke-width:2px
    style FactDatabase fill:#0000ff,stroke:#333,stroke-width:2px
    style VectorStores fill:#40e0d0,stroke:#333,stroke-width:2px
    style UI fill:#1e90ff,stroke:#333,stroke-width:2px

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

