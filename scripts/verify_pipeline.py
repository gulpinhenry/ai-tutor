import sys
import os
import networkx as nx

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.graph.builder import GraphBuilder
from src.rag.engine import QueryEngine

def verify_pipeline():
    print("=== 1. Building Targeted Graph (Slides + 2 Web Pages) ===")
    builder = GraphBuilder()
    
    print("Processing Slides...")
    builder.build_graph(query={"type": "slide"})
    
    print("Processing Web Pages (Limit 2)...")
    builder.build_graph(limit=2, query={"type": "web_page"})
    
    builder.save_graph("data/test_graph.gml")
    
    print("\n=== 2. Verifying Graph Structure ===")
    G = nx.read_gml("data/test_graph.gml")
    print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    
    resource_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'resource']
    print(f"Total Resource Nodes: {len(resource_nodes)}")
    
    nodes_with_spans = [n for n, d in G.nodes(data=True) if d.get('span')]
    print(f"Resources with Spans: {len(nodes_with_spans)}")
    if nodes_with_spans:
        print(f"Sample Span: {G.nodes[nodes_with_spans[0]]}")
    else:
        print("WARNING: No spans found!")

    print("\n=== 3. Verifying RAG Query ===")
    engine = QueryEngine(graph_path="data/test_graph.gml")
    
    query = "What are the body motions?" # test
    print(f"Query: {query}")
    response = engine.query(query)
    print(f"\nResponse:\n{response}")
    
    if "URL:" in response:
        print("\nSUCCESS: Citation found in response.")
    else:
        print("\nWARNING: No citation found in response.")

if __name__ == "__main__":
    verify_pipeline()
