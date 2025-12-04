import sys
import os
from pymongo import MongoClient

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ingestion.store import MongoStore

def main():
    store = MongoStore()
    doc = store.collection.find_one({"content": {"$regex": "Image:"}})
    
    if doc:
        print(f"Found document with image: {doc['url']}")
        print("--- Content Snippet ---")
        print(doc['content'][:500])
        print("...")
    else:
        print("No documents found with '[Image:' marker.")

if __name__ == "__main__":
    main()
