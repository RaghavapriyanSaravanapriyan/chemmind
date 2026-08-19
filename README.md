# ChemMind — AI & RAG Subsystem (`rag` Branch)

> **Branch:** `rag`  
> **Subsystem:** AI, RAG Pipeline, Vector Retrieval, LLM Integration, & Chemistry Tools  
> **Status:** Stage A1 Complete (Foundation & Gateway)

---

## Architecture Overview

The `ai/` package provides a provider-independent AI and RAG engine for ChemMind. It handles scientific paper ingestion, semantic chunking, vector indexing in Qdrant, grounded RAG generation with structured citations, and chemistry entity reasoning via RDKit.

### Core Architectural Principles
1. **Provider Independence:** Application logic depends on standard interfaces (`BaseLLMProvider`, `BaseEmbeddingProvider`) and the `LLMGateway`, never hardcoded to specific model APIs or Ollama vendor details.
2. **Deterministic Chemistry:** LLMs are used for intent classification and tool selection; exact chemical calculations, SMILES validation, and 3D molecular coordinate generation are delegated to RDKit.
3. **Structured Citations:** Answers include first-class citation metadata (workspace ID, document ID, page number, section, bounding box coordinates) enabling instant document viewer navigation.
4. **Testability:** Complete unit test coverage across configuration, schemas, providers, and gateway delegation.

```text
Application Services / Backend
            ↓
       LLM Gateway
   ┌────────┴────────┐
Ollama            Mock / External APIs
   │
   ▼
Vector Store (Qdrant) & Embeddings
```

---

## Subsystem Roadmap (Stages A1 – A12)

| Stage | Phase | Status | Description |
|---|---|---|---|
| **Stage A1** | Package Foundation | **Completed** | Interfaces, Pydantic schemas, `LLMGateway`, Ollama & Mock providers, configuration system, test suite. |
| **Stage A2** | Document Ingestion | **Completed** | PDF parsing (`pypdf`), text/layout extraction, page/section mapping, metadata & SHA256 checksum generation. |
| **Stage A3** | Semantic Chunking | **Completed** | Structure & Chemistry-aware chunking for LaTeX papers, atomic equation preservation, chemical entity tagging. |
| **Stage A4** | Embedding Pipeline | **Completed** | Dense vectorization (`LLMGateway`), Qdrant Vector Store integration (`qdrant-client`), Mock vector store, payload indexing. |
| **Stage A5** | Basic Retrieval | **Completed** | Dense vector retrieval (`DenseRetriever`), workspace boundary isolation, score thresholding, chemical pre-filtering. |
| **Stage A6** | LLM Generation | *Next* | Prompt construction and RAG generation via `LLMGateway`. |
| **Stage A7** | Citation Mapping | Planned | Attaching structured `Citation` metadata with precise source locations. |
| **Stage A8** | Hybrid Retrieval | Planned | Combining dense vector search with sparse keyword indexing. |
| **Stage A9** | Reranking | Planned | Cross-encoder reranking for candidate evidence optimization. |
| **Stage A10**| Multi-Doc Reasoning | Planned | RAG cross-examination across multiple user-selected papers. |
| **Stage A11**| Grounded Quizzes | Planned | Generating objective-focused quizzes with source attribution. |
| **Stage A12**| Chemistry Engine | Planned | Chemical entity extraction, SMILES validation, and 3D mol generation. |

---

## File Inventory & Descriptions

```text
ai/
├── requirements.txt         # Core dependencies (pydantic, httpx, pytest, etc.)
├── config.py                # Pydantic settings with environment variable resolution
├── __init__.py              # Package entry point exposing gateway, settings, and schemas
│
├── schemas/                 # Data contracts & Pydantic models
│   ├── __init__.py
│   ├── llm.py               # ChatMessage, Role, LLMRequest, LLMResponse, StreamChunk, TokenUsage
│   ├── citation.py          # Citation, SourceLocation (page numbers, section, bbox)
│   ├── document.py          # DocumentMetadata, DocumentChunk
│   └── embedding.py         # EmbeddingRequest, EmbeddingResponse
│
├── providers/               # Abstract & Concrete AI Backends
│   ├── __init__.py
│   ├── base_llm.py          # BaseLLMProvider abstract class (generate, stream)
│   ├── base_embedding.py    # BaseEmbeddingProvider abstract class (embed)
│   ├── ollama_llm.py        # Ollama REST client implementation (/api/chat)
│   ├── ollama_embedding.py  # Ollama REST embedding client (/api/embed) & MockEmbeddingProvider
│   └── mock_llm.py          # Fast offline Mock LLM provider for unit testing & development
│
├── generation/              # Gateway & LLM Orchestration
│   ├── __init__.py
│   └── gateway.py           # LLMGateway for dynamic provider switching and invocation
│
├── utils/                   # Subsystem Utilities
│   ├── __init__.py
│   └── logger.py            # Centralized structured logger for the ai/ package
│
└── tests/                   # Automated Test Suite
    ├── __init__.py
    ├── test_config.py       # Configuration and env override tests
    ├── test_schemas.py      # Pydantic schema validation & serialization tests
    ├── test_providers.py    # Mock & Provider execution unit tests
    └── test_gateway.py      # LLMGateway delegation and provider switching tests
```

### Detailed File Responsibilities

- **`ai/config.py`**: Reads `CHEMMIND_AI_*` environment variables (e.g. `CHEMMIND_AI_OLLAMA_BASE_URL`, `CHEMMIND_AI_DEFAULT_LLM_MODEL`) with sensible defaults for local development.
- **`ai/schemas/llm.py`**: Defines strict data structures for single/multi-turn messages, completion options, response payloads, token metrics, and streaming deltas.
- **`ai/schemas/citation.py`**: Standardizes citation data so frontend document viewers can jump straight to highlighted bounding boxes on specific PDF pages.
- **`ai/schemas/document.py`**: Captures extracted document metadata and chunk representations containing text, page numbers, and detected chemical entities.
- **`ai/providers/base_llm.py`**: Interface enforcing `generate(request)` and `stream(request)` across all vendor implementations.
- **`ai/providers/ollama_llm.py`**: Asynchronous `httpx` implementation communicating with local Ollama instances for synchronous and streaming chat completions.
- **`ai/providers/mock_llm.py`**: Offline provider simulating streaming and static completions without requiring a running Ollama server.
- **`ai/generation/gateway.py`**: The primary entry point for AI operations. Consumer code calls `gateway.generate()`, `gateway.stream()`, or `gateway.embed()` without needing to know which vendor is active.

---

## Local Setup & Testing

### 1. Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r ai/requirements.txt
```

### 2. Running Unit Tests
```bash
pytest ai/tests
```
All 11 foundation tests must pass cleanly before opening a Pull Request into `main`.
