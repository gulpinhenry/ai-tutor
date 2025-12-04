import networkx as nx
import os

def inspect_resources():
    path = "data/knowledge_graph.gml"
    if not os.path.exists(path):
        print("Graph file not found.")
        return

    G = nx.read_gml(path)
    
    print("--- All Resource Nodes ---")
    count = 0
    slide_count = 0
    for node, data in G.nodes(data=True):
        if data.get('type') == 'resource':
            res_type = data.get('resource_type')
            span = data.get('span')
            print(f"Resource: {node}")
            print(f"  Type: {res_type}")
            print(f"  Span: {span}")
            print("-" * 20)
            
            if res_type == 'slide':
                slide_count += 1
            count += 1
            # if count >= 50:
            #     print("... (truncated)")
            #     break
    
    print(f"Total Resources: {count}")
    print(f"Total Slides: {slide_count}")

if __name__ == "__main__":
    inspect_resources()
