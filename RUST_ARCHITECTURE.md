# ChemMind Rust Backend Architecture

## Design Principles
1. **Local-First**: All services run locally, no mandatory external dependencies
2. **Lightweight**: Minimal dependencies, fast startup, low memory footprint
3. **Modular**: Clear separation of concerns, trait-based abstractions
4. **High-Performance**: Async throughout, connection pooling, zero-copy where possible
5. **Type-Safe**: Compile-time SQL verification, strong typing at boundaries

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Web Framework | Axum 0.7 | Ergonomic, tower-based, excellent performance |
| Async Runtime | Tokio 1.38 (multi-threaded) | Industry standard, robust |
| Database | SQLx 0.8 + PostgreSQL | Compile-time checked queries, async |
| Migrations | SQLx migrate | Version-controlled, embedded in binary |
| Auth | jsonwebtoken + bcrypt | Battle-tested, HS256 JWT |
| Config | config-rs + dotenvy | Layered config (file + env) |
| Validation | validator 0.17 + garde | Struct-level validation |
| Logging | tracing + tracing-subscriber | Structured, JSON output |
| Serialization | serde + serde_json | Standard, fast |
| HTTP Client | reqwest 0.12 (rustls) | Async, TLS, streaming |
| File Upload | axum-extra multipart | Streaming, memory-efficient |
| SSE | axum response::sse | Native support |
| Chemistry | rdkit-sys (via PyO3) or custom | SMILES parsing, 3D coords |

## Project Structure

```
backend_rust/
├── Cargo.toml
├── .env.example
├── migrations/
│   └── 001_initial.sql
├── src/
│   ├── main.rs                 # App entry, state, router
│   ├── config.rs               # Settings struct + loading
│   ├── db.rs                   # Pool, health check
│   ├── error.rs                # AppError, IntoResponse
│   ├── auth.rs                 # JWT, password hashing
│   ├── middleware.rs           # Auth extractors
│   ├── models/                 # DB models (sqlx::FromRow)
│   │   ├── user.rs
│   │   ├── workspace.rs
│   │   ├── document.rs
│   │   ├── conversation.rs
│   │   ├── citation.rs
│   │   └── usage.rs
│   ├── dto/                    # API request/response types
│   │   ├── auth.rs
│   │   ├── workspace.rs
│   │   ├── document.rs
│   │   ├── conversation.rs
│   │   ├── chat.rs
│   │   ├── chemistry.rs
│   │   ├── quiz.rs
│   │   ├── reasoning.rs
│   │   └── usage.rs
│   ├── services/
│   │   ├── storage.rs          # Local file storage
│   │   ├── usage.rs            # Quota tracking
│   │   ├── ai_gateway.rs       # LLM provider abstraction
│   │   ├── chemistry.rs        # SMILES → properties/3D
│   │   ├── quiz.rs             # Grounded quiz generation
│   │   ├── reasoning.rs        # Multi-doc synthesis
│   │   └── ingestion.rs        # PDF → chunks → embeddings
│   ├── retrieval/              # Vector search (pgvector)
│   │   ├── embeddings.rs
│   │   ├── vector_store.rs
│   │   └── hybrid.rs
│   └── api/v1/
│       ├── mod.rs              # Router composition
│       ├── auth.rs
│       ├── workspaces.rs
│       ├── documents.rs
│       ├── conversations.rs
│       ├── chat.rs
│       ├── chemistry.rs
│       ├── quiz.rs
│       ├── reasoning.rs
│       ├── usage.rs
│       └── health.rs
└── tests/
    ├── integration.rs
    └── unit_*.rs
```

## Database Schema (PostgreSQL + pgvector)

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;  -- for embeddings

-- Core tables (same as migration 001_initial.sql)
-- ... users, workspaces, workspace_members, documents, document_metadata
-- ... conversations, messages, citations, usage_records

-- Vector embeddings for RAG
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    token_count INT,
    embedding vector(384),  -- nomic-embed-text dimensions
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

## Service Architecture

### AIGateway (Trait-Based)
```rust
#[async_trait]
trait LLMProvider: Send + Sync {
    async fn generate(&self, req: ChatRequest) -> Result<(String, Vec<Citation>)>;
    async fn stream(&self, req: ChatRequest) -> Result<Vec<StreamChunk>>;
    async fn embed(&self, texts: Vec<String>) -> Result<Vec<Vec<f32>>>;
}

struct OllamaProvider { ... }
struct MockProvider { ... }

struct AIGateway {
    ollama: OllamaProvider,
    mock: MockProvider,
}
```

### Chemistry Engine
- Pure Rust SMILES parser for validation, MW, formula
- For 3D coords: bind to RDKit via PyO3 or use `chemfiles` crate
- Fallback to heuristic 2D→3D if RDKit unavailable

### Ingestion Pipeline
```
PDF Upload → Storage → Background Task:
  1. Extract text (pdf-extract / lopdf)
  2. Chunk with overlap (chemistry-aware)
  3. Generate embeddings (Ollama nomic-embed-text)
  4. Store in document_chunks with pgvector
  5. Update document status → READY
```

### Retrieval (Hybrid)
- Dense: pgvector cosine similarity on embeddings
- Sparse: PostgreSQL tsvector + tsquery (BM25-ish)
- Fusion: Reciprocal Rank Fusion (RRF)

## API Contract (Preserving Python Behavior)

### Auth
- `POST /api/v1/auth/register` → `{id, email, full_name, ...}`
- `POST /api/v1/auth/login` → `{access_token, token_type: "bearer"}`
- `GET /api/v1/auth/me` → User profile

### Workspaces
- `POST /api/v1/workspaces` → Workspace
- `GET /api/v1/workspaces` → Workspace[]
- `GET /api/v1/workspaces/{id}` → Workspace
- `PUT /api/v1/workspaces/{id}` → Workspace
- `DELETE /api/v1/workspaces/{id}` → 204
- `POST /api/v1/workspaces/{id}/members` → WorkspaceMember

### Documents
- `POST /api/v1/workspaces/{id}/documents` (multipart) → Document + metadata
- `GET /api/v1/workspaces/{id}/documents` → Document[]
- `GET /api/v1/workspaces/{id}/documents/{doc_id}` → Document + metadata
- `DELETE /api/v1/workspaces/{id}/documents/{doc_id}` → 204

### Conversations
- `POST /api/v1/workspaces/{id}/conversations` → Conversation
- `GET /api/v1/workspaces/{id}/conversations` → Conversation[]
- `GET /api/v1/workspaces/{id}/conversations/{conv_id}` → Conversation + Messages[]
- `POST /api/v1/workspaces/{id}/conversations/{conv_id}/messages` → Message
- `DELETE /api/v1/workspaces/{id}/conversations/{conv_id}` → 204

### Chat (AI)
- `POST /api/v1/workspaces/{id}/conversations/{conv_id}/chat` → AIChatResponse
- `GET /api/v1/workspaces/{id}/conversations/{conv_id}/chat/stream` → SSE Stream

### Chemistry
- `POST /api/v1/chemistry/properties` → MolecularPropertiesResponse
- `POST /api/v1/chemistry/3d` → Mol3DResponse

### Quiz
- `POST /api/v1/workspaces/{id}/quizzes` → QuizResponse

### Multi-Doc Reasoning
- `POST /api/v1/workspaces/{id}/reasoning/multi-doc` → MultiDocResponse

### Usage
- `GET /api/v1/workspaces/{id}/usage` → WorkspaceUsageSummary

### Health
- `GET /health` → HealthResponse
- `GET /api/v1/health` → HealthResponse

## Frontend Communication

- Base URL: `http://localhost:8000/api/v1` (configurable via `NEXT_PUBLIC_API_URL`)
- Auth: `Authorization: Bearer <token>` header
- File Upload: `multipart/form-data` with field `file`
- SSE: `Accept: text/event-stream`, events are JSON chunks
- Error Format: `{error: {code: string, message: string}}`

## Configuration (.env)

```env
# App
CHEMMIND_PROJECT_NAME="ChemMind Backend API"
CHEMMIND_API_V1_STR="/api/v1"
CHEMMIND_ENVIRONMENT="development"

# Security
CHEMMIND_SECRET_KEY="change-me-32-bytes-minimum"
CHEMMIND_ALGORITHM="HS256"
CHEMMIND_ACCESS_TOKEN_EXPIRE_MINUTES=43200

# CORS
CHEMMIND_BACKEND_CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Storage
CHEMMIND_STORAGE_DIR="./uploads"
CHEMMIND_MAX_UPLOAD_SIZE_MB=50
CHEMMIND_ALLOWED_EXTENSIONS=[".pdf"]

# Quotas
CHEMMIND_DEFAULT_WORKSPACE_DOC_LIMIT=50
CHEMMIND_DEFAULT_WORKSPACE_STORAGE_MB=500
CHEMMIND_DEFAULT_WORKSPACE_AI_REQUEST_LIMIT=200

# Database
CHEMMIND_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/chemmind_db"

# AI / Ollama
CHEMMIND_OLLAMA_BASE_URL="http://localhost:11434"
CHEMMIND_DEFAULT_LLM_MODEL="llama3"
CHEMMIND_DEFAULT_EMBEDDING_MODEL="nomic-embed-text"

# Logging
CHEMMIND_LOG_LEVEL="info"
```

## Development Workflow

1. **Start PostgreSQL**: `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16`
2. **Start Ollama**: `ollama serve` then `ollama pull llama3 nomic-embed-text`
3. **Run Rust Backend**: `cargo run --release` (port 8000)
4. **Run Frontend**: `cd frontend && npm run dev` (port 3000)

## Production Considerations

- Run migrations on startup (embedded via `sqlx::migrate!`)
- Use `cargo build --release` with LTO, strip symbols
- Configure connection pool: min=5, max=20, timeouts
- Enable TLS via reverse proxy (nginx/Caddy)
- Set `RUST_LOG=info,chemmind_backend=debug`
- Monitor with tracing-opentelemetry if needed