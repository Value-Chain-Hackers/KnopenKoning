from config import MODEL_NAME, EMBEDDING_MODEL, NER_MODEL
from utils.extract_knowledge import extract_text_from_pdf, split_text_into_chunks
from transformers import pipeline
from tqdm import tqdm 
import json

pipe = pipeline("token-classification", model=NER_MODEL)

def extract_named_entities(pdf_path):
    ikea =  extract_text_from_pdf(pdf_path)
    ikea_chunks = split_text_into_chunks(ikea, 256, 24)
    entities = []
    for chunk in ikea_chunks:
        result = pipe(chunk)
        if(len(result)>0):
            entities.extend(result)
    return entities

def combine_tokens(entities):
    combined_entities = []
    current_entity = None

    for token in entities:
        if not current_entity:
            current_entity = {
                'entity': token['entity'],
                'score': token['score'],
                'word': token['word'].replace('##', ''),
                'start': token['start'],
                'end': token['end']
            }
        elif token['start'] == current_entity['end']:
            # Continuation of the current entity
            current_entity['word'] += token['word'].replace('##', '')
            current_entity['end'] = token['end']
            current_entity['score'] = min(current_entity['score'], token['score'])
        else:
            # End of current entity and start of a new entity
            combined_entities.append(current_entity)
            current_entity = {
                'entity': token['entity'],
                'score': token['score'],
                'word': token['word'].replace('##', ''),
                'start': token['start'],
                'end': token['end']
            }
    
    # Add the last entity if it exists
    if current_entity:
        combined_entities.append(current_entity)

    return combined_entities

def deduplicate_entities(entities):
    seen = set()
    deduplicated_entities = []

    for entity in entities:
        entity_tuple = (entity['entity'], entity['word'], entity['start'], entity['end'])
        if entity_tuple not in seen:
            seen.add(entity_tuple)
            deduplicated_entities.append(entity_tuple)
    
    return deduplicated_entities

if __name__ == "__main__":
    
    pdf_files = ["./data/cocacola.pdf", "./data/unilever.pdf", "./data/ikea.pdf", "./data/albertheijn.pdf"]
    ents = {}
    for file in tqdm(pdf_files):
        result = extract_named_entities(file)
        result = combine_tokens(result)
        result = deduplicate_entities(result)
        print(result)
        with open(file.replace(".pdf","_ner.json"), "w", encoding="utf-8") as file:
            json.dump(result, file)
        ents[file] = result
    print(ents)

