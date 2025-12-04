# Erica AI Tutor - Walkthrough

## Overview
Erica is a GraphRAG-based AI tutor for the "Introduction to AI" course. It ingests course materials (web pages, slides, videos), builds a Knowledge Graph with granular resource tracking (spans/timecodes), and uses it to answer student questions with context-aware explanations and precise citations.

## Prerequisites
- **Docker Desktop** running.
- **Ollama** running locally (optional, for cost savings).
  - Pull model: `ollama pull qwen2.5:0.5b`
- **OpenRouter API Key** (configured in [.env](.env)) as a fallback.
- **MongoDB Atlas URI** (configured in [.env](.env)).

## Quick Start

### 1. Start the Environment
```bash
docker-compose up --build -d
```
*This starts the `app` container which holds the Python environment.*

### 2. Ingestion (M2)
Ingest course materials from the website, YouTube, and slides. This step clears the DB and re-scrapes everything.
```bash
docker-compose exec app python scripts/ingest_website.py
```
*Verify ingestion:*
```bash
docker-compose exec app python scripts/inspect_ingestion.py
```

### 3. Graph Construction (M3)
Build the Knowledge Graph. This extracts Concepts, Relations, Examples, and Resources (with spans) using the LLM.
```bash
docker-compose exec app python scripts/build_graph.py
```
*Note: This process can take a while. It saves the graph to [data/knowledge_graph.gml](./data/knowledge_graph.gml).*

*Verify graph structure and spans:*
```bash
docker-compose exec app python scripts/debug_graph_context.py
docker-compose exec app python scripts/inspect_resources.py
```

### 4. Visualization (Optional)
Visualize the constructed graph:
```bash
docker-compose exec app python scripts/visualize_graph.py
```
Check [data/graph_viz.png](./data/graph_viz.png).

### 5. Chat Interface (M4)
Launch the Streamlit Chat UI:
```bash
docker-compose exec app streamlit run src/ui/chat.py --server.port 8501 --server.address 0.0.0.0
```
Open your browser at `http://localhost:8501`.

## System Components
- **Ingestion**: `src/ingestion/`
    - `scraper.py`: Main crawler.
    - `youtube_loader.py`: Fetches transcripts with timecodes.
    - `slide_loader.py`: Extracts text from PDF slides by page.
- **Storage**: MongoDB (Raw Data)
- **Graph**: `src/graph/`
    - `chunker.py`: Metadata-aware chunking (preserves spans).
    - `builder.py`: LLM-based extraction of Concepts, Relations, Examples.
- **RAG Engine**: `src/rag/engine.py` (Query processing, Subgraph retrieval, Citation formatting)
- **UI**: `src/ui/chat.py` (Streamlit)

## Testing
To verify the system components (M1-M4), run the test suite:

### Unit Tests
Verifies `Chunker` (M2) and `GraphBuilder` (M3) logic.
```bash
docker-compose exec app python -m unittest discover tests
```
```
# Erica AI Tutor - Walkthrough

## Overview
Erica is a GraphRAG-based AI tutor for the "Introduction to AI" course. It ingests course materials (web pages, slides, videos), builds a Knowledge Graph with granular resource tracking (spans/timecodes), and uses it to answer student questions with context-aware explanations and precise citations.

## Prerequisites
- **Docker Desktop** running.
- **Ollama** running locally (optional, for cost savings).
  - Pull model: `ollama pull qwen2.5:0.5b`
- **OpenRouter API Key** (configured in `.env`) as a fallback.
- **MongoDB Atlas URI** (configured in `.env`).

## Quick Start

### 1. Start the Environment
```bash
docker-compose up --build -d
```
*This starts the `app` container which holds the Python environment.*

### 2. Ingestion (M2)
Ingest course materials from the website, YouTube, and slides. This step clears the DB and re-scrapes everything.
```bash
docker-compose exec app python scripts/ingest_website.py
```
*Verify ingestion:*
```bash
docker-compose exec app python scripts/inspect_ingestion.py
```

### 3. Graph Construction (M3)
Build the Knowledge Graph. This extracts Concepts, Relations, Examples, and Resources (with spans) using the LLM.
```bash
docker-compose exec app python scripts/build_graph.py
```
*Note: This process can take a while. It saves the graph to `data/knowledge_graph.gml`.*

*Verify graph structure and spans:*
```bash
docker-compose exec app python scripts/debug_graph_context.py
docker-compose exec app python scripts/inspect_resources.py
```

### 4. Visualization (Optional)
Visualize the constructed graph:
```bash
docker-compose exec app python scripts/visualize_graph.py
```
Check `data/graph_viz.png`.

### 5. Chat Interface (M4)
Launch the Streamlit Chat UI:
```bash
docker-compose exec app streamlit run src/ui/chat.py --server.port 8501 --server.address 0.0.0.0
```
Open your browser at `http://localhost:8501`.

## System Components
- **Ingestion**: `src/ingestion/`
    - `scraper.py`: Main crawler.
    - `youtube_loader.py`: Fetches transcripts with timecodes.
    - `slide_loader.py`: Extracts text from PDF slides by page.
- **Storage**: MongoDB (Raw Data)
- **Graph**: `src/graph/`
    - `chunker.py`: Metadata-aware chunking (preserves spans).
    - `builder.py`: LLM-based extraction of Concepts, Relations, Examples.
- **RAG Engine**: `src/rag/engine.py` (Query processing, Subgraph retrieval, Citation formatting)
- **UI**: `src/ui/chat.py` (Streamlit)

## Testing
To verify the system components (M1-M4), run the test suite:

### Unit Tests
Verifies `Chunker` (M2) and `GraphBuilder` (M3) logic.
```bash
docker-compose exec app python -m unittest discover tests
```

### Integration Test
Verifies the full pipeline (Ingestion -> Graph -> RAG) using mock data.
```bash
docker-compose exec app python tests/test_integration.py
```
*Note: The local Qwen 0.5B model may struggle with strict citation formatting in the generated text, but the test verifies that the correct resource URL is retrieved and present in the response.*

### 4. Verify Robustness
Run the robustness tests to ensure the system handles API errors and malformed JSON correctly:
```bash
docker-compose exec app python tests/test_youtube_loader.py
docker-compose exec app python tests/test_builder_robustness.py
```
These tests verify:
*   Graceful handling of YouTube API "Too Many Requests" and missing transcripts.
*   **Advanced JSON Repair**:
    *   Heuristic-based escaping of unescaped quotes inside strings.
    *   Correct handling of literal control characters (newlines, tabs).
    *   Double-escaping of LaTeX backslashes.
*   Automatic fixing of truncated JSON (unclosed strings/braces).
*   Handling of "Extra data" after JSON.

### Async Graph Build Test
Verifies the asynchronous graph builder.
```bash
docker-compose exec app python tests/test_async_builder.py
```

## Troubleshooting
- **Rate Limits**: If using OpenRouter, check your usage. The system defaults to local Ollama (`qwen2.5:0.5b`) if available.
- **Missing Spans**: Ensure `scripts/build_graph.py` is run *after* `scripts/ingest_website.py`. Check `scripts/inspect_resources.py` to verify spans are present in the graph.
- **Localhost Issues**: If `localhost:8501` is unreachable, ensure port `8501` is mapped in `docker-compose.yml` and the container is running (`docker-compose ps`).
```
