import networkx as nx
import matplotlib.pyplot as plt
import os

def visualize_graph(path="data/knowledge_graph.gml"):
    if not os.path.exists(path):
        print(f"Graph file not found at {path}")
        return

    G = nx.read_gml(path)
    print(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=0.5)
    
    node_colors = []
    for node in G.nodes(data=True):
        n_type = node[1].get('type', 'unknown')
        if n_type == 'concept':
            node_colors.append('lightblue')
        elif n_type == 'resource':
            node_colors.append('lightgreen')
        else:
            node_colors.append('gray')
            
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=1000, font_size=8, arrowsize=20)
    
    edge_labels = nx.get_edge_attributes(G, 'type')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)
    
    output_img = "data/graph_viz.png"
    plt.savefig(output_img)
    print(f"Graph visualization saved to {output_img}")

if __name__ == "__main__":
    visualize_graph()
