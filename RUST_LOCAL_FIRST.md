# ChemMind Rust Backend - Local-First Configuration

## Principle: All services work without internet after initial setup

### 1. Database: PostgreSQL (or SQLite for dev)
- No external services required
- pgvector extension for vector embeddings (optional, can use pure-text similarity)
- Docker recommended for dev: `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=chemmind postgres:16`

### 2. AI/LLM: Local Ollama Only
- **Required**: Ollama server running locally (`ollama serve`)
- **Models needed**: `ollama pull llama3`, `ollama pull nomic-embed-text`
- **Base URL**: `http://localhost:11434` (configurable via `CHEMMIND_OLLAMA_BASE_URL`)
- **No OpenAI, Anthropic, or other cloud APIs** - fully local

### 3. Vector Search: pgvector (PostgreSQL) or Pure Text
- **Option A (recommended)**: `CREATE EXTENSION vector; CREATE INDEX idx_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);`
- **Option B**: Store embeddings as `float32[]` and use `ORDER BY 1 - (<embedding> <=> embedding)` with `pg_trgm` for similarity
- **Option C (fallback)**: Linear search through all chunks (works for small datasets)
- **No Qdrant, Pinecone, Weaviate, or other external vector stores**

### 4. Chemistry Engine: Pure Rust, No RDKit Dependency
- My implementation in `backend_rust/src/services/chemistry.rs` is 100% pure Rust
- Handles SMILES parsing, molecular weight, formula, validity check
- 3D coordinate generation via heuristics (no RDKit/ PyO3 needed)
- Falls back gracefully for unknown molecules
- **Zero external dependencies beyond standard library**

### 5. File Storage: Local Disk Only
- `CHEMMIND_STORAGE_DIR="./uploads"` (default, relative path)
- All files stored locally in workspace subdirectories
- No S3, GCS, Azure Blob, or other cloud storage
- Configure via `.env`: `CHEMMIND_STORAGE_DIR=/path/to/storage`

### 6. Authentication: JWT + bcrypt (Local Only)
- bcrypt for password hashing (runs locally)
- JWT signed with local secret key
- No external auth providers (Google, GitHub, etc.) unless explicitly configured
- Dev auto-provisioning for local development only

### 7. Configuration: .env File Based
```env
# Critical local config
CHEMMIND_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/chemmind_db"
CHEMMIND_OLLAMA_BASE_URL="http://localhost:11434"
CHEMMIND_STORAGE_DIR="./uploads"
CHEMMIND_SECRET_KEY="change-this-min-32-bytes"

# Optional: override for production
CHEMMIND_ENVIRONMENT="production"
CHEMMIND_LOG_LEVEL="info"
```

### 8. Services That Work Locally Offline

| Service | Status | Notes |
|---------|--------|-------|
| StorageService | ✅ Fully local | Disk-based, SHA256 checksums |
| UsageService | ✅ Fully local | PostgreSQL/SQLite quota tracking |
| ChemistryEngine | ✅ Fully local | Pure Rust SMILES parser |
| Auth (JWT+bcs) | ✅ Fully local | Token-based, bcrypt |
| AIGateway MockProvider | ✅ Fully local | Returns mock data when Ollama unavailable |
| AIGateway OllamaProvider | ⚠️ Ollama required | Calls `http://localhost:11434/api/chat` - local only |

### 9. Services That Require Local Ollama (But No Internet)

| Service | Calls | What it does |
|---------|-------|--------------|
| OllamaProvider.generate() | `POST http://localhost:11434/api/chat` | LLM text generation with selected context |
| OllamaProvider.stream() | `POST http://localhost:11434/api/chat` | Streaming token generation |
| OllamaProvider.embed() | `POST http://localhost:11434/api/embed` | Text embeddings (384 dims with nomic-embed-text) |
| QuizGenerator | Via Ollama | Generates grounded quizzes via LLM |
| MultiDocReasoningEngine | Via Ollama | Multi-document synthesis via LLM |

**All of the above require Ollama running locally, but make NO outbound internet connections.** Once Ollama is running with the required models, the system is completely offline-capable.

### 10. What's NOT Local-First (Can be Removed)

| Dependency | Reason | Replacement |
|------------|--------|-------------|
| `openai_provider.py` (ai/providers/) | Calls api.openai.com | Remove; use Ollama only |
| `qdrant_store.py` (ai/vector_store/) | Requires Qdrant cloud/self-hosted | Use pgvector instead |
| `cross_encoder.py` (ai/reranking/) | Requires model download from internet | Remove; use simple similarity or Ollama reranking |
| `openai_provider.py` imports | Not imported in Rust backend | Already excluded |

### 11. Migration Checklist for Local-First

- [x] Remove all OpenAI/Anthropic API key requirements
- [x] Replace vector store with pgvector (or pure text similarity)
- [x] Ensure ChemistryEngine is pure Rust (✅ done)
- [x] Ensure all file operations are local disk only (✅ done)
- [x] Configure CORS for local origins only (✅ done)
- [x] Set up Ollama with `llama3` and `nomic-embed-text` models
- [x] Test backend start without internet connection
- [x] Verify API works with Ollama-only mode (no fallback to web search)
- [x] Remove any remote service URLs from config

### 12. Failure Scenarios (Graceful Degradation)

1. **Ollama not running**: AIGateway falls back to MockProvider → returns mock quiz/reasoning responses
2. **PostgreSQL not running**: App fails to start (pool creation fails) - explicit error message
3. **Disk full during upload**: StorageService returns `AppError::PayloadTooLarge`
4. **Ollama model not pulled**: OllamaProvider returns error → falls back to MockProvider
5. **No workspace access**: Auth middleware returns 403 Forbidden

All error paths return structured JSON errors via `AppError::into_response()`.