import pymongo
from pymongo import MongoClient


myclient = pymongo.MongoClient("mongodb://root:kpnBCdiAFamV5InlXPvaq7X2M5TsDOEd@localhost:27017/")

if "vch" in myclient.list_database_names():
    print("The database exists.")
    mydb = myclient["vch"]
else:
    print("The database does not exist. Creating...")
    mydb = myclient["vch"]

if "vch" in mydb.list_collection_names():
    print("The collection exists.")
    collection = mydb["vch"]
else:
    print("The collection does not exist. Creating...")
    collection  = mydb.create_collection("vch")

collection.insert_many([{"_id": "John", "address": "Highway 37"}, {"_id": "Peter", "address": "Lowstreet 27"}, {"_id": "Amy", "address": "Apple st 652"}])


print(myclient.list_database_names())