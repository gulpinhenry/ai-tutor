import sys
import os
from collections import Counter

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ingestion.store import MongoStore

def main():
    store = MongoStore()
    count = store.count_documents()
    print(f"Total documents: {count}")
    
    pipeline = [
        {"$group": {"_id": "$type", "count": {"$sum": 1}}}
    ]
    results = store.collection.aggregate(pipeline)
    print("\nBreakdown by Type:")
    for res in results:
        print(f" - {res['_id']}: {res['count']}")

    print("\nIngested URLs (first 50):")
    urls = store.get_all_urls()
    for u in urls[:50]:
        print(f" - {u}")
    
    if len(urls) > 50:
        print(f"... and {len(urls) - 50} more.")

if __name__ == "__main__":
    main()
