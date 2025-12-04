import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.graph.builder import GraphBuilder

import asyncio
import argparse

def main():
    parser = argparse.ArgumentParser(description="Build Knowledge Graph")
    parser.add_argument("--provider", type=str, default=None, help="LLM Provider (ollama or openrouter)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of docs per type (None for all)")
    parser.add_argument("--concurrency", type=int, default=2, help="Async concurrency")
    args = parser.parse_args()

    print(f"Starting Knowledge Graph Construction with provider: {args.provider or 'auto'}...")
    builder = GraphBuilder(provider=args.provider)
    
    async def run_build():
        print(f"Processing Slides (Limit {args.limit})...")
        await builder.build_graph_async(limit=args.limit, query={"type": "slide"}, concurrency=args.concurrency)
        
        print(f"Processing Web Pages (Limit {args.limit})...")
        await builder.build_graph_async(limit=args.limit, query={"type": "web_page"}, concurrency=args.concurrency) 
    
    asyncio.run(run_build())
    
    output_path = "data/knowledge_graph.gml"
    os.makedirs("data", exist_ok=True)
    builder.save_graph(output_path)
    print("Graph construction complete.")

if __name__ == "__main__":
    main()
