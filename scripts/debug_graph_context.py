import networkx as nx
import sys
import os

def check_concept_neighborhood(concept_id="artificial_intelligence"):
    path = "data/knowledge_graph.gml"
    if not os.path.exists(path):
        print("Graph file not found.")
        return

    G = nx.read_gml(path)
    
    if not G.has_node(concept_id):
        print(f"Concept '{concept_id}' not found in graph.")
        for n, d in G.nodes(data=True):
            if d.get('title', '').lower() == concept_id.replace('_', ' '):
                print(f"Found concept by title: {n}")
                concept_id = n
                break
        else:
            return

    print(f"--- Neighborhood of '{concept_id}' ---")
    
    concept_data = G.nodes[concept_id]
    print(f"Concept: {concept_data.get('title', concept_id)}")
    print(f"  Definition: {concept_data.get('definition', 'N/A')}")
    print(f"  Aliases: {concept_data.get('aliases', [])}")
    
    in_edges = G.in_edges(concept_id, data=True)
    print(f"\nIncoming Edges ({len(in_edges)}):")
    for u, v, d in in_edges:
        edge_type = d.get('type')
        print(f"  {u} --[{edge_type}]--> {v}")
        
        node_data = G.nodes[u]
        node_type = node_data.get('type')
        
        if node_type == 'resource':
            print(f"    [Resource] Type: {node_data.get('resource_type')}")
            print(f"    URL: {node_data.get('url')}")
            if node_data.get('span'):
                print(f"    Span: {node_data.get('span')}")
        elif node_type == 'example':
            print(f"    [Example] Content: {node_data.get('content')}")

    out_edges = G.out_edges(concept_id, data=True)
    print(f"\nOutgoing Edges ({len(out_edges)}):")
    for u, v, d in out_edges:
        print(f"  {u} --[{d.get('type')}]--> {v}")

if __name__ == "__main__":
    check_concept_neighborhood()
