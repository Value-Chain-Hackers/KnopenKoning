from pymongo import MongoClient
from bson import ObjectId

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/', username='root', password='kpnBCdiAFamV5InlXPvaq7X2M5TsDOEd')
db = client['vch']
processes_collection = db['processes']

class Process:
    id = None
    question = None
    elements = None
    search_results = None

    def __init__(self, id, question, elements=None, search_results=None):
        self.id = id
        self.question = question
        self.elements = elements or []
        self.search_results = search_results or []

    def save(self):
        process_data = {
            "_id": self.id,
            "question": self.question,
            "elements": self.elements,
            "search_results": self.search_results
        }
        processes_collection.update_one({"_id": self.id}, {"$set": process_data}, upsert=True)

    @staticmethod
    def get(id):
        process_data = processes_collection.find_one({"_id": id})
        if process_data:
            return Process(process_data["_id"], process_data["question"], process_data["elements"], process_data["search_results"])
        return None
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "question": self.question,
            "elements": self.elements,
            "search_results": self.search_results
        }
    
if __name__ == "__main__":
    process = Process(ObjectId(), "What is the process for handling personal data?")
    process.elements.append("Identify the data subject")
    process.elements.append("Obtain consent")
    process.elements.append("Process data")
    process.save()
    
    process = Process.get(process.id)
    print(process.id, process.question, process.elements)