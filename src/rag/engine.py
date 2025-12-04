import networkx as nx
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from src.utils import get_llm
import json

class QueryEngine:
    def __init__(self, graph_path="data/knowledge_graph.gml"):
        self.llm = get_llm()
        self.graph = nx.read_gml(graph_path)
        
        # Prompt to map query to concepts
        self.concept_extraction_prompt = ChatPromptTemplate.from_template("""
        Given the user query, identify the key concepts that are likely present in the knowledge graph.
        Return a JSON list of concept IDs (snake_case) or titles.
        
        User Query: {query}
        
        Example Output:
        ["gradient_descent", "loss_function"]
        """)
        
        self.concept_chain = self.concept_extraction_prompt | self.llm | JsonOutputParser()
        
        # Prompt to generate answer
        self.answer_prompt = ChatPromptTemplate.from_template("""
        Context:
        {context}
        
        Question: {query}
        
        Task: Explain the answer using the Context.
        CRITICAL: You MUST cite the source URL and Span for every fact.
        
        Format:
        <Explanation> [Source](URL) (Span: <Span>)
        
        Example:
        Gradient Descent is an algorithm. [Slide](http://example.com/slide.pdf) (Span: 5)
        
        Answer:
        """)
        
        self.answer_chain = self.answer_prompt | self.llm | StrOutputParser()

    def extract_concepts(self, query):
        try:
            result = self.concept_chain.invoke({"query": query})
            print(f"Raw concept extraction result: {result}")
            
            if isinstance(result, dict):
                concepts = result.get("concept_ids") or result.get("concepts") or []
            elif isinstance(result, list):
                concepts = result
            else:
                concepts = []
                
            print(f"Identified concepts: {concepts}")
            return concepts
        except Exception as e:
            print(f"Error extracting concepts: {e}")
            return []

    def get_subgraph(self, concepts, radius=1):
        nodes_to_include = set()
        for concept_item in concepts:
            if isinstance(concept_item, dict):
                concept = concept_item.get("concept_id") or concept_item.get("title")
            else:
                concept = concept_item
            
            if not concept:
                continue
                
            matched_node = None
            if self.graph.has_node(concept):
                matched_node = concept
            else:
                for node, data in self.graph.nodes(data=True):
                    if data.get('title', '').lower() == str(concept).lower():
                        matched_node = node
                        break
            
            if matched_node:
                undirected_graph = self.graph.to_undirected()
                subgraph_nodes = nx.single_source_shortest_path_length(undirected_graph, matched_node, cutoff=radius).keys()
                nodes_to_include.update(subgraph_nodes)
        
        if not nodes_to_include:
            return None
            
        return self.graph.subgraph(nodes_to_include)

    def format_context(self, subgraph):
        if not subgraph:
            return "No relevant context found in the knowledge graph."
        
        context = "Nodes:\n"
        for node, data in subgraph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            if node_type == 'concept':
                context += f"- Concept: {data.get('title', node)} ({data.get('difficulty', '')})\n"
                context += f"  Definition: {data.get('definition', '')}\n"
            elif node_type == 'resource':
                context += f"- Resource: {data.get('resource_type', 'web')}\n"
                context += f"  URL: {data.get('url')}\n"
                if data.get('span'):
                    context += f"  Span: {data.get('span')}\n"
            elif node_type == 'example':
                context += f"- Example: {data.get('content')}\n"
                
        context += "\nEdges:\n"
        for u, v, data in subgraph.edges(data=True):
            context += f"- {u} --[{data.get('type')}]--> {v}\n"
            
        return context

    def query(self, user_input):
        print(f"Processing query: {user_input}")
        
        concepts = self.extract_concepts(user_input)
            
        subgraph = self.get_subgraph(concepts)
        context = self.format_context(subgraph)
        
        answer = self.answer_chain.invoke({"context": context, "query": user_input})
        
        sanitized_concepts = []
        for c in concepts:
            if isinstance(c, dict):
                sanitized_concepts.append(c.get("title") or c.get("concept_id") or str(c))
            else:
                sanitized_concepts.append(str(c))
        
        return {
            "answer": answer,
            "context": context,
            "concepts": sanitized_concepts
        }

if __name__ == "__main__":
    engine = QueryEngine()
    response = engine.query("What is artificial intelligence?")
    print("\nResponse:\n", response)
