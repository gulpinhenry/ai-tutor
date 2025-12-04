import os
from pymongo import MongoClient
from datetime import datetime

class MongoStore:
    def __init__(self, db_name="ai_tutor", collection_name="raw_data"):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def save_document(self, url, content, html, doc_type="web_page", metadata=None):
        """
        Saves a document to MongoDB. Upserts based on URL.
        """
        if metadata is None:
            metadata = {}
            
        document = {
            "url": url,
            "content": content, # Text content
            "html": html,       # Raw HTML
            "type": doc_type,
            "metadata": metadata,
            "ingested_at": datetime.utcnow()
        }
        
        self.collection.update_one(
            {"url": url},
            {"$set": document},
            upsert=True
        )
        print(f"Saved/Updated: {url}")

    def get_all_urls(self):
        """Returns a list of all ingested URLs."""
        return [doc["url"] for doc in self.collection.find({}, {"url": 1})]

    def count_documents(self):
        return self.collection.count_documents({})

    def clear_collection(self):
        """Deletes all documents in the collection."""
        self.collection.delete_many({})
        print(f"Collection '{self.collection.name}' cleared.")
