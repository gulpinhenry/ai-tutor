import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ingestion.scraper import WebScraper
from src.ingestion.store import MongoStore

def main():
    url = "https://pantelis.github.io/courses/ai/"
    print(f"Starting ingestion for: {url}")
    
    store = MongoStore()
    store.clear_collection()
    
    scraper = WebScraper(url)
    scraper.scrape()
    
    store = MongoStore()
    count = store.count_documents()
    print(f"Ingestion complete. Total documents in DB: {count}")
    
    print("\nIngested URLs:")
    for u in store.get_all_urls():
        print(f"- {u}")

if __name__ == "__main__":
    main()
