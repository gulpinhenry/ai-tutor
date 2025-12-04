import sys
import os
sys.path.append(os.getcwd())
from src.ingestion.store import MongoStore
from src.graph.chunker import Chunker
import json

def debug_chunker():
    store = MongoStore()
    chunker = Chunker()
    
    slide_doc = store.collection.find_one({"type": "slide"})
    if not slide_doc:
        print("No slides found in DB.")
        return

    print(f"Testing Chunker on Slide: {slide_doc['url']}")
    print(f"Metadata keys: {slide_doc.get('metadata', {}).keys()}")
    
    chunks = chunker.chunk_document(slide_doc)
    print(f"Generated {len(chunks)} chunks.")
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}:")
        print(f"  Text length: {len(chunk['text'])}")
        print(f"  Metadata: {chunk['metadata']}")
        if i >= 3: break

if __name__ == "__main__":
    debug_chunker()
