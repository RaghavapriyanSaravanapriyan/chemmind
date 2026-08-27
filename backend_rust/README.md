# ChemMind Backend (Rust)

A fast, lightweight, production-grade Rust backend for ChemMind - a chemistry-focused research workspace.

## Features

- **100% Local**: No cloud dependencies required
- **Fast & Lightweight**: Built with Axum, SQLx, and Tokio
- **Type-Safe**: Compile-time checked SQL queries with SQLx
- **Secure**: JWT authentication, bcrypt password hashing, CORS protection
- **Production-Ready**: Structured logging, error handling, health checks
- **Async/Concurrent**: Full async support with Tokio
- **SSE Streaming**: Real-time chat streaming support
- **Provider-Independent AI**: Ollama, Mock providers for LLM/embeddings

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Axum      │────▶│  PostgreSQL │
│  (Next.js)  │     │   API       │     │  (SQLx)     │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │  Services   │
                    │  • Storage  │
                    │  • Usage    │
                    │  • AI       │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Ollama    │
                    │  (Local AI) │
                    └─────────────┘
```

## Quick Start

### Prerequisites

- Rust 1.70+
- PostgreSQL 14+
- Ollama (for AI features)

### Local Development

1. **Start infrastructure**:
```bash
docker-compose up -d postgres ollama
```

2. **Configure environment**:
```bash
cd backend_rust
cp .env.example .env
# Edit .env with your settings
```

3. **Run migrations**:
```bash
sqlx migrate run
```

4. **Build and run**:
```bash
cargo run --release
```

Server starts at `http://localhost:8000`

### Using Docker

```bash
docker-compose up -d
```

## API Endpoints

### Health
- `GET /health` - Health check
- `GET /api/v1/health` - API health check

### Authentication
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

### Workspaces
- `POST /api/v1/workspaces` - Create workspace
- `GET /api/v1/workspaces` - List workspaces
- `GET /api/v1/workspaces/{id}` - Get workspace
- `PUT /api/v1/workspaces/{id}` - Update workspace
- `DELETE /api/v1/workspaces/{id}` - Delete workspace
- `POST /api/v1/workspaces/{id}/members` - Add member

### Documents
- `POST /api/v1/workspaces/{id}/documents` - Upload document
- `GET /api/v1/workspaces/{id}/documents` - List documents
- `GET /api/v1/workspaces/{id}/documents/{doc_id}` - Get document
- `DELETE /api/v1/workspaces/{id}/documents/{doc_id}` - Delete document

### Conversations
- `POST /api/v1/workspaces/{id}/conversations` - Create conversation
- `GET /api/v1/workspaces/{id}/conversations` - List conversations
- `GET /api/v1/workspaces/{id}/conversations/{conv_id}` - Get conversation
- `POST /api/v1/workspaces/{id}/conversations/{conv_id}/messages` - Add message
- `DELETE /api/v1/workspaces/{id}/conversations/{conv_id}` - Delete conversation

### AI Chat
- `POST /api/v1/workspaces/{id}/conversations/{conv_id}/chat` - Sync chat
- `GET /api/v1/workspaces/{id}/conversations/{conv_id}/chat/stream?prompt=...` - SSE streaming chat

### Usage
- `GET /api/v1/workspaces/{id}/usage` - Get usage summary

## Configuration

Environment variables (prefix: `CHEMMIND_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | "ChemMind Backend API" | Project name |
| `API_V1_STR` | "/api/v1" | API prefix |
| `ENVIRONMENT` | "development" | Environment |
| `SECRET_KEY` | (required) | JWT secret (32+ chars) |
| `ALGORITHM` | "HS256" | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 43200 | Token expiry |
| `BACKEND_CORS_ORIGINS` | ["http://localhost:3000"] | CORS origins |
| `STORAGE_DIR` | "./uploads" | File storage path |
| `MAX_UPLOAD_SIZE_MB` | 50 | Max upload size |
| `ALLOWED_EXTENSIONS` | [".pdf"] | Allowed file extensions |
| `DEFAULT_WORKSPACE_DOC_LIMIT` | 50 | Document quota |
| `DEFAULT_WORKSPACE_STORAGE_MB` | 500 | Storage quota (MB) |
| `DEFAULT_WORKSPACE_AI_REQUEST_LIMIT` | 200 | AI request quota |
| `DATABASE_URL` | (required) | PostgreSQL connection string |
| `OLLAMA_BASE_URL` | "http://localhost:11434" | Ollama URL |
| `DEFAULT_LLM_MODEL` | "llama3" | Default LLM model |
| `DEFAULT_EMBEDDING_MODEL` | "nomic-embed-text" | Default embedding model |
| `LOG_LEVEL` | "INFO" | Log level |

## Database Schema

- **users** - User accounts
- **workspaces** - Research workspaces
- **workspace_members** - Workspace membership with roles
- **documents** - Uploaded documents with metadata
- **document_metadata** - Extended document info
- **conversations** - Chat conversations
- **messages** - Conversation messages
- **citations** - AI response citations
- **usage_records** - Quota tracking

## AI Providers

The AI Gateway supports multiple providers:

1. **Ollama** (default) - Local LLM inference
2. **Mock** - Offline testing provider

Configure via `model_provider` parameter: `ollama`, `mock`

## Testing

```bash
# Unit tests
cargo test

# Integration tests (requires running postgres)
cargo test --test integration
```

## Performance

- Connection pooling (20 max, 5 min)
- Prepared statements
- Async I/O throughout
- Zero-copy where possible
- Optimized database indexes

## Security

- Password hashing with bcrypt (cost 12)
- JWT tokens with expiration
- Role-based access control (owner/editor/viewer)
- Input validation with validator crate
- CORS configuration
- SQL injection prevention via SQLx

## License

MIT