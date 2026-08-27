# ChemMind Full Codebase Audit Report

## Project Overview
ChemMind is an agentic research platform for molecular chemistry with three pillars:
1. **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS
2. **Backend (Python/FastAPI)**: FastAPI, Async SQLAlchemy, Pydantic v2, PostgreSQL/SQLite
3. **AI Subsystem** (`ai/`): Agentic RAG, Chemistry Engine, Quiz Generator, Multi-Doc Reasoning, Ollama LLM

---

## Backend Architecture Mapping

### Python/FastAPI Backend (`backend/`)
**Framework Stack:**
- FastAPI 0.141.1, Uvicorn 0.52.4
- SQLAlchemy 2.0.52 (async), asyncpg 0.31.0, aiosqlite 0.22.1
- Pydantic 2.13.4, Pydantic Settings 2.15.0
- JWT (PyJWT 2.13.0), bcrypt 5.0.0, passlib 1.7.4
- SSE (sse-starlette 3.4.8)

**Database Models:**
| Model | Table | Key Fields |
|-------|-------|-----------|
| User | users | id, email, hashed_password, full_name, is_active, is_superuser |
| Workspace | workspaces | id, name, description, owner_id, is_archived |
| WorkspaceMember | workspace_members | id, workspace_id, user_id, role (owner/editor/viewer) |
| Document | documents | id, workspace_id, uploaded_by_id, filename, file_size, mime_type, storage_path, status |
| DocumentMetadata | document_metadata | id, document_id, page_count, title, author, checksum |
| Conversation | conversations | id, workspace_id, user_id, title |
| Message | messages | id, conversation_id, sender (user/assistant), content |
| Citation | citations | id, message_id, document_id, page, chunk_id, section, excerpt, source_type, url, title, domain |
| UsageRecord | usage_records | id, workspace_id, user_id, metric_type, count |

**API Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/auth/register | Register user |
| POST | /api/v1/auth/login | Login, returns JWT |
| GET | /api/v1/auth/me | Get current user |
| POST | /api/v1/workspaces | Create workspace |
| GET | /api/v1/workspaces | List user's workspaces |
| GET | /api/v1/workspaces/{id} | Get workspace |
| PUT | /api/v1/workspaces/{id} | Update workspace |
| DELETE | /api/v1/workspaces/{id} | Delete workspace (owner only) |
| POST | /api/v1/workspaces/{id}/members | Add member |
| POST | /api/v1/workspaces/{id}/documents | Upload document (multipart) |
| GET | /api/v1/workspaces/{id}/documents | List documents |
| GET | /api/v1/workspaces/{id}/documents/{doc_id} | Get document |
| DELETE | /api/v1/workspaces/{id}/documents/{doc_id} | Delete document |
| POST | /api/v1/workspaces/{id}/conversations | Create conversation |
| GET | /api/v1/workspaces/{id}/conversations | List conversations |
| GET | /api/v1/workspaces/{id}/conversations/{conv_id} | Get conversation + messages |
| POST | /api/v1/workspaces/{id}/conversations/{conv_id}/messages | Add message |
| DELETE | /api/v1/workspaces/{id}/conversations/{conv_id} | Delete conversation |
| POST | /api/v1/workspaces/{id}/conversations/{conv_id}/chat | Sync AI RAG chat |
| GET | /api/v1/workspaces/{id}/conversations/{conv_id}/chat/stream | SSE streaming chat |
| POST | /api/v1/chemistry/properties | Molecular properties from SMILES |
| POST | /api/v1/chemistry/3d | 3D molecular coordinates |
| POST | /api/v1/workspaces/{id}/quizzes | Generate grounded quiz |
| POST | /api/v1/workspaces/{id}/reasoning/multi-doc | Multi-doc synthesis |
| GET | /api/v1/workspaces/{id}/usage | Get usage summary & quotas |

**Services:**
- `StorageService`: Local file storage (`uploads/`), SHA256 checksums, workspace subdirs
- `UsageService`: Quota enforcement (docs=50, storage=500MB, AI req=200)
- `AIGatewayService`: Wraps Agentic RAG engine with resilient fallback

**AI Subsystem (`ai/`):**
- Agentic Router: Routes to internal search, web fallback, or hybrid
- Hybrid Retrieval: Dense (embeddings) + Sparse (BM25) via RRF
- Citation Resolver: Grounds answers with document/page/section metadata
- Chemistry Engine: RDKit for SMILES validation, MW, formula, 3D coords
- Quiz Generator: Grounded MCQs with distractors & citations
- Multi-Doc Engine: Cross-document comparison matrix & discrepancy detection
- Ollama Provider: Local LLM (`llama3`, `mistral`) + embeddings (`nomic-embed-text`)

---

### Rust Backend (`backend_rust/`) - Partially Implemented

**Framework Stack:**
- Axum 0.7, Tokio 1.38, Tower-HTTP 0.6
- SQLx 0.8 (PostgreSQL, async, compile-time checked queries)
- JSONWebToken 9.2, bcrypt 0.15
- Tracing for structured logging
- Config 0.14 with env file support

**Project Structure:**
```
backend_rust/src/
├── main.rs              # App entry, router, state
├── config/mod.rs        # Settings from .env + env vars
├── db/mod.rs            # SQLx pool, migrations
├── auth/mod.rs          # JWT, bcrypt, token create/decode
├── models/              # DB models + API DTOs
│   ├── user.rs
│   ├── workspace.rs
│   ├── document.rs
│   ├── conversation.rs
│   └── usage.rs
├── services/
│   ├── storage.rs       # File storage with checksums
│   ├── usage.rs         # Quota tracking
│   └── ai_gateway.rs    # OllamaProvider + MockProvider
├── middleware/mod.rs    # Auth middleware (required + optional)
├── error/mod.rs         # AppError enum + IntoResponse
└── api/v1/
    ├── mod.rs           # Router composition
    ├── auth.rs          # register, login, me
    ├── workspaces.rs    # CRUD + members
    ├── documents.rs     # Upload, list, get, delete
    ├── conversations.rs # CRUD + messages
    ├── chat.rs          # Sync + SSE streaming
    └── usage.rs         # Quota summary
```

**Database Migration** (`migrations/001_initial.sql`):
- All 9 tables with UUID PKs, FKs, indexes, triggers for `updated_at`
- CHECK constraints on enums (role, status, sender, metric_type)

**Implemented Endpoints (matching Python):**
✅ Auth: register, login, me  
✅ Workspaces: CRUD + members  
✅ Documents: upload (multipart), list, get, delete  
✅ Conversations: CRUD + messages with citations  
✅ Chat: sync + SSE streaming with quota checks  
✅ Usage: workspace usage summary  

**Missing Endpoints:**
❌ Chemistry: `/chemistry/properties`, `/chemistry/3d`  
❌ Quiz: `/workspaces/{id}/quizzes`  
❌ Multi-Doc: `/workspaces/{id}/reasoning/multi-doc`  
❌ Health: `/health` (referenced in main.rs but not implemented)  

**Services Status:**
✅ StorageService - local files, SHA256, workspace dirs  
✅ UsageService - upsert with ON CONFLICT, quota checks  
⚠️ AIGateway - Ollama + Mock providers, but no RAG integration (no vector store, no retrieval)  
❌ Chemistry Engine - not ported  
❌ Quiz Generator - not ported  
❌ Multi-Doc Engine - not ported  
❌ Document Ingestion/Embedding Pipeline - not ported  

---

## Frontend (`frontend/`)

**Stack:**
- Next.js 16.3.1 (Turbopack), React 19.2.8, TypeScript 5
- Tailwind CSS 4, Framer Motion 13, KaTeX, Lucide React
- Zod for validation

**API Integration (`src/lib/api.ts`):**
- Base URL: `http://localhost:8000/api/v1` (env `NEXT_PUBLIC_API_URL`)
- LocalStorage fallbacks for workspaces, documents, messages
- Direct Ollama fallback for chat, quiz, multi-doc when backend unreachable
- Types defined for all API responses

**Key Features:**
- Workspace dashboard with document upload/switching
- Real-time SSE chat streaming
- 3D molecular visualizer (Three.js via custom)
- KaTeX LaTeX rendering
- Quiz assessment modals
- Multi-doc synthesis UI

---

## Gap Analysis

### Rust Backend Missing Features

| Feature | Python Location | Rust Status | Priority |
|---------|----------------|-------------|----------|
| Chemistry Properties | `chemistry.py` + `ChemistryEngine` | Missing | High |
| Chemistry 3D Coords | `chemistry.py` + `ChemistryEngine` | Missing | High |
| Quiz Generation | `quizzes.py` + `QuizGenerator` | Missing | High |
| Multi-Doc Reasoning | `reasoning.py` + `MultiDocEngine` | Missing | High |
| Health Endpoint | `health.py` | Referenced but missing | Medium |
| Document Ingestion | `ai/ingestion/` | Missing | Medium |
| Vector Store/Retrieval | `ai/retrieval/`, `ai/vector_store/` | Missing | Medium |
| Embeddings Pipeline | `ai/embeddings/` | Missing | Medium |
| Agentic RAG Router | `ai/agentic/` | Mock only | Medium |
| Reranking | `ai/reranking/` | Missing | Low |

### Legacy/Unused Code

**Python Backend:**
- `ai/` package is separate but tightly coupled via imports in `ai_gateway.py`
- MockVectorStore used as fallback - not production ready
- Web search fallback in AIGatewayService uses hardcoded PubChem URL
- Dev user auto-provisioning in `deps.py` creates users on every unauthenticated request

**Rust Backend:**
- Health endpoint referenced in `main.rs:87-96` but `health.rs` missing
- `endpoints/` directory exists but empty (code is in parent `v1/`)
- No testcontainers setup for integration tests (configured in Cargo.toml but not used)

### Bottlenecks & Issues

1. **Python**: Sync RAG calls block event loop; no connection pooling config visible
2. **Python**: File upload reads entire file into memory before storage
3. **Rust**: SSE streaming collects all chunks into Vec before sending (memory)
4. **Rust**: No request validation (validator crate imported but not used)
5. **Both**: No rate limiting, no API versioning strategy beyond `/v1`
6. **Frontend**: localStorage fallback duplicates backend logic, creates sync issues

### Unnecessary Remote Dependencies

1. **OpenAI Provider** (`ai/providers/openai_provider.py`) - not used in local mode
2. **Qdrant Vector Store** (`ai/vector_store/qdrant_store.py`) - requires external service
3. **Cross-Encoder Reranker** (`ai/reranking/cross_encoder.py`) - requires model download
4. **Web Search Fallback** - calls external PubChem API

---

## Migration Strategy

### Phase 1: Complete Rust Backend (Stage 2-3)
1. Add missing endpoints: chemistry, quiz, multi-doc
2. Implement health endpoint
3. Port Chemistry Engine (pure Rust or bind to RDKit via PyO3)
4. Port Quiz Generator & Multi-Doc Engine (simplified, LLM-based)
5. Add document ingestion pipeline (PDF parsing → chunking → embeddings)

### Phase 2: Local-First Conversion (Stage 4)
1. Remove OpenAI, Qdrant, Cross-Encoder dependencies
2. Use local Ollama for all LLM/embedding needs
3. Use SQLx + PostgreSQL (or SQLite for dev) for vector storage (pgvector)
4. Ensure all services work without internet

### Phase 3: Frontend Integration (Stage 5)
1. Update API base URL to Rust backend port
2. Remove localStorage fallbacks (trust backend)
3. Fix any response format mismatches
4. Test all flows end-to-end

### Phase 4: Performance & Security (Stage 6)
1. Add request validation (validator crate)
2. Implement rate limiting (tower-governor)
3. Add structured logging with correlation IDs
4. Benchmark and optimize hot paths

### Phase 5: Cleanup (Stage 7)
1. Remove Python backend after validation
2. Remove unused AI package code
3. Clean up frontend localStorage fallbacks
4. Update documentation

### Phase 6: Validation (Stage 8)
1. Clean build from scratch
2. Run all tests (unit + integration)
3. Test failure scenarios (DB down, Ollama down)
4. Load test critical endpoints