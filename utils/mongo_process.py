from datetime import datetime
from typing import List
from pymongo import MongoClient
from bson import ObjectId

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/', username='root', password='kpnBCdiAFamV5InlXPvaq7X2M5TsDOEd')
db = client['vch']
processes_collection = db['processes']

class ProcessElement:
    title:str = None
    type:str = None
    description:str = None
    icon:str = None
    content:str = None
    query:str = None

class QuestionAnswerPair:
    question:str = None
    answers: List[ProcessElement] | None = None

class Process:
    id = None
    owner = None
    question = None
    elements: List[ProcessElement] | None = None
    search_results = None
    created_at = None

    def __init__(self, id, question, elements=None, search_results=None, owner=None, created_at=None):
        self.id = id
        self.question = question
        self.elements = elements or []
        self.search_results = search_results or []
        self.owner = owner
        self.created_at = created_at or datetime.now()
        
    def save(self):
        process_data = self.to_dict()
        process_data['updated_at'] = datetime.now()
        processes_collection.update_one({"_id": self.id}, {"$set": process_data}, upsert=True)

    @staticmethod
    def get(id):
        process_data = processes_collection.find_one({"_id": id})
        if process_data:
            return Process(process_data["_id"], process_data["question"], process_data.get("elements", []), process_data.get("search_results", []), process_data.get("owner", None), process_data.get("created_at", None))
        return None
    

    @staticmethod
    def get_byOwner(id):
        cur = processes_collection.find({"owner":2}).limit(10).sort([('created_at', -1)])
        docs = []
        for doc in cur:
            docs.append(doc)
        return docs

    def to_dict(self):
        return {
            "id": str(self.id),
            "question": self.question,
            "elements": self.elements,
            "search_results": self.search_results,
            "owner": self.owner,
            "created_at": self.created_at
        }
    
if __name__ == "__main__":
    # process = Process(ObjectId(), "What is the process for handling personal data?")
    # process.elements.append("Identify the data subject")
    # process.elements.append("Obtain consent")
    # process.elements.append("Process data")
    # process.save()
    
    # process = Process.get(process.id)
    # print(process.id, process.question, process.elements)

    byOwner = Process.get_byOwner(2)
    for p in byOwner:
        print(p["_id"], p["question"],p.get("created_at"))