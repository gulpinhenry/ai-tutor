import json
import os
import networkx as nx
import asyncio
from src.utils import get_llm
from src.ingestion.store import MongoStore
from src.graph.chunker import Chunker
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

class GraphBuilder:
    def __init__(self, provider=None, persistent_dir="data"):
        self.store = MongoStore()
        self.chunker = Chunker()
        self.persistent_dir = persistent_dir
        self.graph_path = os.path.join(persistent_dir, "knowledge_graph.gml")
        self.state_path = os.path.join(persistent_dir, "processed_chunks.json")
        
        if os.path.exists(self.graph_path):
            print(f"Resuming: Loading existing graph from {self.graph_path}")
            self.graph = nx.read_gml(self.graph_path)
        else:
            self.graph = nx.DiGraph()
            
        self.processed_ids = set()
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r') as f:
                    self.processed_ids = set(json.load(f))
                print(f"Resuming: Loaded {len(self.processed_ids)} processed chunk IDs")
            except Exception as e:
                print(f"Warning: Could not load state file: {e}")

        self.llm = get_llm(provider=provider)
        
        # Define extraction prompt
        self.extraction_prompt = ChatPromptTemplate.from_template("""
        You are an expert Knowledge Graph builder. Your task is to extract Concepts, Relations, and Examples from the provided text.
        
        CRITICAL INSTRUCTIONS:
        1. This task is VITAL. Failure to produce valid JSON will break the entire system.
        2. You MUST think step by step before generating the JSON. Briefly explain your reasoning in a "Thought:" section at the beginning.
        3. The final output MUST contain a valid JSON block enclosed in curly braces.
        
        JSON FORMATTING RULES (STRICT):
        - ESCAPE ALL DOUBLE QUOTES inside string values. Example: "He said \\"Hello\\"" NOT "He said "Hello"".
        - ESCAPE ALL BACKSLASHES in LaTeX. Example: "\\\\theta" NOT "\\theta".
        - NO newlines or tabs inside string values unless escaped ("\\\\n").
        
        Schema:
        {{
            "concepts": [
                {{"id": "unique_snake_case_id", "title": "Human Readable Title", "definition": "Concise definition"}}
            ],
            "relations": [
                {{"source": "concept_id_1", "target": "concept_id_2", "type": "relation_type (e.g., IS_A, PART_OF, DEPENDS_ON, RELATED_TO)", "description": "Brief explanation"}}
            ],
            "examples": [
                {{"content": "Description of the example", "related_concepts": ["concept_id_1"]}}
            ]
        }}
        
        If no relevant concepts are found, return:
        {{
            "concepts": [],
            "relations": [],
            "examples": []
        }}

        Text to analyze:
        {text}
        """)
        
        self.chain = self.extraction_prompt | self.llm | StrOutputParser()

    def repair_json(self, json_str):
        """
        Attempts to repair common JSON errors:
        1. Unescaped quotes inside strings.
        2. Unescaped control characters (newlines, tabs).
        3. LaTeX backslashes.
        """
        import re
        
        json_str = json_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        token = "___ESCAPED_QUOTE___"
        json_str = json_str.replace('\\"', token)
        
        new_chars = []
        i = 0
        n = len(json_str)
        
        while i < n:
            char = json_str[i]
            
            if char == '"':
                j = i - 1
                while j >= 0 and json_str[j].isspace():
                    j -= 1
                prev_char = json_str[j] if j >= 0 else ''
                
                is_valid_start = prev_char in '{[:,'
                
                k = i + 1
                while k < n and json_str[k].isspace():
                    k += 1
                next_char = json_str[k] if k < n else ''
                
                is_valid_end = next_char in '}:],'
                
                if next_char == ',':
                    m = k + 1
                    while m < n and json_str[m].isspace():
                        m += 1
                    char_after_comma = json_str[m] if m < n else ''
                    
                    if char_after_comma not in '" { [ 0 1 2 3 4 5 6 7 8 9 - t f n':
                        is_valid_end = False
                
                if is_valid_start or is_valid_end:
                    new_chars.append('"')
                else:
                    new_chars.append('\\"')
            else:
                new_chars.append(char)
            i += 1
            
        json_str = "".join(new_chars)
        
        json_str = json_str.replace(token, '\\"')
        
        def fix_string_content(match):
            content = match.group(1)
            
            def replace_backslash(m):
                c = m.group(1)
                if c in ['"', '\\', '/', 'u']: return m.group(0)
                return '\\\\' + c
            
            content = re.sub(r'\\(.|$)', replace_backslash, content)

            content = content.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            
            return f'"{content}"'

        pattern = r'"((?:[^"\\]|\\.)*)"'
        return re.sub(pattern, fix_string_content, json_str, flags=re.DOTALL)

    def fix_truncated_json(self, json_str):
        clean_str = json_str.replace('\\"', '')
        quote_count = clean_str.count('"')
        
        if quote_count % 2 != 0:
            json_str += '"'
            
        stack = []
        for char in json_str:
            if char == '{':
                stack.append('}')
            elif char == '[':
                stack.append(']')
            elif char == '}' or char == ']':
                if stack:
                    if stack[-1] == char:
                        stack.pop()
        
        while stack:
            json_str += stack.pop()
            
        return json_str

    def parse_output(self, output_str):
        if not output_str:
            return {}

        match = re.search(r'(\{[\s\n]*"concepts".*)', output_str, re.DOTALL)
        
        if match:
            output_str = match.group(1)
            end_idx = output_str.rfind('}')
            if end_idx != -1:
                output_str = output_str[:end_idx+1]
        else:
            start_idx = output_str.find('{')
            end_idx = output_str.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                output_str = output_str[start_idx : end_idx + 1]
            else:
                print(f"Warning: No JSON object found in output. Raising error to trigger retry.")
                raise ValueError("No JSON object found in output")

        def try_load(s):
            try:
                return json.loads(s)
            except json.JSONDecodeError as e:
                if "Extra data" in str(e):
                    if hasattr(e, 'pos'):
                        return json.loads(s[:e.pos])
                raise e

        try:
            return try_load(output_str)
        except json.JSONDecodeError:
            repaired = self.repair_json(output_str)
            try:
                return try_load(repaired)
            except json.JSONDecodeError:
                fixed = self.fix_truncated_json(repaired)
                try:
                    return try_load(fixed)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON even after repair and truncation fix: {e}")
                    raise ValueError(f"Failed to parse JSON: {e}")

    def save_checkpoint(self):
        os.makedirs(self.persistent_dir, exist_ok=True)
        
        nx.write_gml(self.graph, self.graph_path)
        
        with open(self.state_path, 'w') as f:
            json.dump(list(self.processed_ids), f)
        
        print(f"Checkpoint saved: {len(self.graph.nodes)} nodes, {len(self.processed_ids)} chunks processed.")

    def build_graph(self, limit=None, query=None):
        filter_query = query if query else {}
        docs = self.store.collection.find(filter_query)
        if limit:
            docs = docs.limit(limit)
            
        for doc in docs:
            url = doc['url']
            print(f"Processing: {url}")
            chunks = self.chunker.chunk_document(doc)
            
            for i, chunk_data in enumerate(chunks):
                try:
                    print(f" - Chunk {i+1}/{len(chunks)}")
                    text = chunk_data['text']
                    metadata = chunk_data['metadata']
                    
                    result_str = self.chain.invoke({"text": text})
                    result = self.parse_output(result_str)
                    self.update_graph(result, metadata)
                except Exception as e:
                    print(f"Error processing chunk {i} of {url}: {e}")

    async def process_chunk_async(self, text, metadata, semaphore, max_retries=10):
        async with semaphore:
            attempt = 0
            while True:
                attempt += 1
                try:
                    result_str = await self.chain.ainvoke({"text": text})
                    result = self.parse_output(result_str)
                    return result, metadata
                except Exception as e:
                    import traceback
                    traceback.print_exc() # Optional: reduce noise if retrying forever
                    print(f"Error processing chunk (Attempt {attempt}): {e}")
                    
                    if max_retries and attempt >= max_retries:
                        print(f"Max retries ({max_retries}) reached. Skipping chunk.")
                        return None, None
                    
                    import asyncio
                    # Exponential backoff, capped at 60 seconds
                    sleep_time = min(2 * attempt, 60)
                    print(f"Retrying in {sleep_time} seconds...")
                    await asyncio.sleep(sleep_time)

    async def build_graph_async(self, limit=None, query=None, concurrency=2):
        filter_query = query if query else {}
        docs = list(self.store.collection.find(filter_query))
        if limit:
            docs = docs[:limit]
            
        print(f"Starting async build for {len(docs)} documents with concurrency {concurrency}...")
        
        semaphore = asyncio.Semaphore(concurrency)
        tasks = []
        
        total_chunks = 0
        chunks_to_process = []
        
        for doc in docs:
            url = doc['url']
            doc_chunks = self.chunker.chunk_document(doc)
            
            for i, chunk in enumerate(doc_chunks):
                # Generate stable ID
                chunk_id = f"{url}::{i}"
                
                if chunk_id in self.processed_ids:
                    continue
                    
                chunks_to_process.append((chunk, chunk_id))
            
            total_chunks += len(doc_chunks)

        print(f"Queuing {len(chunks_to_process)} chunks (Skipped {total_chunks - len(chunks_to_process)} already processed)...")
        
        processed_count = 0
        save_interval = 10
        
        async def process_wrapper(chunk_data, chunk_id):
            nonlocal processed_count
            text = chunk_data['text']
            metadata = chunk_data['metadata']
            
            result, meta = await self.process_chunk_async(text, metadata, semaphore)
            
            if result:
                self.update_graph(result, meta)
                self.processed_ids.add(chunk_id)
                
                processed_count += 1
                if processed_count % save_interval == 0:
                    self.save_checkpoint()

        tasks = [process_wrapper(c, cid) for c, cid in chunks_to_process]
        
        if tasks:
            await asyncio.gather(*tasks)
            self.save_checkpoint()
        else:
            print("No new chunks to process.")

    def update_graph(self, extraction_result, metadata):
        concepts = extraction_result.get("concepts", [])
        relations = extraction_result.get("relations", [])
        examples = extraction_result.get("examples", [])
        
        source_url = metadata.get('source')
        span = metadata.get('span')
        res_type = metadata.get('type')
        
        if span:
            res_id = f"{source_url}#{span}"
        else:
            res_id = source_url
            span = "" 
            
        if not self.graph.has_node(res_id):
            self.graph.add_node(res_id, type="resource", url=source_url, span=span, resource_type=res_type or "web")
        
        for concept in concepts:
            c_id = concept.get("id")
            if c_id:
                if not self.graph.has_node(c_id):
                    concept_data = concept.copy()
                    concept_data.pop("type", None)
                    self.graph.add_node(c_id, **concept_data, type="concept")
                else:
                    pass
                
                self.graph.add_edge(res_id, c_id, type="explains")

        for rel in relations:
            src = rel.get("source")
            tgt = rel.get("target")
            r_type = rel.get("type")
            
            if src and tgt and r_type:
                if not self.graph.has_node(src):
                    self.graph.add_node(src, type="concept_placeholder")
                if not self.graph.has_node(tgt):
                    self.graph.add_node(tgt, type="concept_placeholder")
                
                self.graph.add_edge(src, tgt, type=r_type)

        for ex in examples:
            content = ex.get("content")
            target_concept = ex.get("exemplifies")
            
            if content and target_concept:
                ex_id = f"ex_{hash(content)}"
                if not self.graph.has_node(ex_id):
                    self.graph.add_node(ex_id, type="example", content=content)
                
                if not self.graph.has_node(target_concept):
                    self.graph.add_node(target_concept, type="concept_placeholder")
                    
                self.graph.add_edge(ex_id, target_concept, type="exemplifies")

    def save_graph(self, path="knowledge_graph.gml"):
        nx.write_gml(self.graph, path)
        print(f"Graph saved to {path}")
        print(f"Nodes: {self.graph.number_of_nodes()}, Edges: {self.graph.number_of_edges()}")

if __name__ == "__main__":
    import asyncio
    builder = GraphBuilder()
    asyncio.run(builder.build_graph_async(limit=5, concurrency=5))
    builder.save_graph("test_graph.gml")
