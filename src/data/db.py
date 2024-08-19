from pymongo import MongoClient

class MongoDB:
    def __init__(self, mongo_uri, db_name):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]

    def get_collection(self, collection_name):
        return self.db[collection_name]

db = MongoDB("mongodb://localhost:27017/", "price_tracker")
