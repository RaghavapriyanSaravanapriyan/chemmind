<div align="center">

<img width="1252" height="285" alt="ChemMind banner" src="https://github.com/user-attachments/assets/9d7618f5-bd4e-4773-bf2d-2465d0e9fd2b" />

**Open Source — Chemistry Research Assistant**

An AI-powered chemistry research workspace for literature discovery, research-paper analysis, citation tracking, 3D molecular modelling, and chemistry-focused information retrieval — combining retrieval-augmented generation with deterministic chemistry tools.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Rust](https://img.shields.io/badge/Rust-2021-orange.svg)](backend_rust/)
[![Next.js](https://img.shields.io/badge/Next.js-16-blue.svg)](frontend/)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](ai/)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

ChemMind is a unified workspace where researchers, chemists, and students can discover literature, upload research papers, analyze them with natural language, receive grounded answers with precise citations, visualize molecular structures in 3D, and generate assessments — all powered by local or cloud-hosted LLMs.

```text
┌──────────────────┬────────────────────────────────────┬──────────────────────┐
│                  │                                    │                      │
│   DOCUMENTS      │          DOCUMENT VIEWER           │      AI COPILOT      │
│                  │                                    │                      │
│   Sources        │          PDF / LaTeX               │      Chat            │
│   Collections    │          Tables                    │      Citations       │
│   Notes          │          Equations                 │      Summaries       │
│   Molecules      │          Figures                   │      Quizzes         │
│   Quizzes        │          References                │      Actions         │
│                  │                                    │                      │
└──────────────────┴────────────────────────────────────┴──────────────────────┘
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Agentic RAG Pipeline** | Autonomous query routing with dense/sparse hybrid retrieval, reciprocal rank fusion, and reranking |
| **Structured Citations** | Every response is grounded in source material with document ID, page number, section title, and direct navigation |
| **3D Molecular Visualizer** | Interactive 3D molecular mesh renderer with SMILES validation, empirical formula, and molecular weight computation |
| **Chemistry Engine** | Deterministic molecular property calculations powered by RDKit with pure-Python heuristics fallback |
| **Grounded Quiz Generator** | AI-generated multiple-choice assessments with plausible distractors and evidence citations |
| **Multi-Document Reasoning** | Cross-document comparative analysis, conflict detection, and synthesis matrices |
| **Real-Time Streaming** | SSE token streaming from LLM to frontend with live citation rendering |
| **Local-First AI** | Full functionality with Ollama-hosted models — no cloud API key required |
| **Provider-Agnostic Gateway** | Switch between Ollama, OpenAI, Anthropic, or Gemini without code changes |
| **LaTeX Rendering** | KaTeX-powered inline and display math rendering with section navigation |
| **Workspace Dashboard** | Multi-workspace management with document upload, quiz modals, and comparison tools |

---

## Architecture

ChemMind is built on three distinct architectural pillars:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                       FRONTEND (Next.js 16)                           │
│   React 19 / TypeScript             KaTeX LaTeX Document Reader       │
│   Tailwind CSS & Framer Motion      3D Molecular Mesh & Property UI   │
│   SSE Real-time Chat Streaming      Workspace & Document Sidebars     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST / SSE API
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     BACKEND (Rust / Axum API)                          │
│   Axum + SQLx (PostgreSQL)             SSE Streaming Endpoint         │
│   JWT Auth + bcrypt Hashing            Usage Limits & Quotas          │
│   Document Ingestion & Storage         Chemistry, Quiz & Multi-Doc    │
│   Provider-Independent AI Gateway      Multi-Doc Reasoning Routers    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ AI Gateway Bridge
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    AI & AGENTIC RAG SUBSYSTEM                          │
│   Agentic Router & Web Fallback       Chemistry Property Engine       │
│   Dense/Sparse Hybrid Retrieval       Grounded Quiz Generator         │
│   Citation Resolver & Linker          Multi-Doc Reasoning Engine      │
│   Ollama Local LLM Provider           Provider-Agnostic Gateway       │
└────────────────────────────────────────────────────────────────────────┘
```

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 16, React 19, TypeScript | Application shell, workspace UI, document viewer |
| **Styling** | Tailwind CSS, Framer Motion | Responsive design, animations, dark/light themes |
| **Math Rendering** | KaTeX | Inline and display LaTeX equations |
| **Backend** | Rust, Axum, Tokio | High-performance API gateway, auth, orchestration |
| **Database** | PostgreSQL (SQLx) | Application state, user data, workspace metadata |
| **Vector Store** | Qdrant | Document embeddings and semantic retrieval |
| **AI/LLM** | Python, Ollama, OpenAI API | RAG pipeline, generation, embeddings |
| **Chemistry** | RDKit | Deterministic molecular property calculations |
| **Infrastructure** | Docker Compose, Redis | Local development stack, caching |
| **Authentication** | JWT (HS256), bcrypt | Token-based auth with password hashing |

**API Endpoints**:
- `/api/v1/workspaces`: Workspace CRUD, member access roles, quota enforcement.
- `/api/v1/workspaces/{id}/documents`: Document upload (PDF, TXT, MD, CSV, TeX), text extraction, semantic metadata.
- `/api/v1/workspaces/{id}/conversations/{id}/chat`: SSE token streaming and synchronous RAG generation.
- `/api/v1/chemistry`: Chemical SMILES property calculation (`/properties`) and 3D spatial coordinates (`/3d`).
- `/api/v1/workspaces/{id}/quizzes`: Grounded multiple-choice quiz generation with evidence citations.
- `/api/v1/workspaces/{id}/reasoning/multi-doc`: Cross-document matrix synthesis and discrepancy detection.
- `/api/v1/ai/models`: Ollama model listing via backend proxy (no direct browser→Ollama).
- `/api/v1/ai/embed`: Text embeddings (Ollama with mock fallback, model override supported).
- `/api/v1/ai/api-keys`: BYOK storage (keys never logged, only last4 exposed).
- **Security & Development Flow**: JWT bearer token authentication with bcrypt password hashing. The frontend auto-provisions a local developer account so startup is friction-free.

---

## Getting Started

### Prerequisites

- [Rust](https://rustup.rs/) (latest stable)
- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://python.org/) (3.11+)
- [Docker](https://docker.com/) & Docker Compose
- [Ollama](https://ollama.com/) (for local LLM inference)

### 1. Start Infrastructure

```bash
docker-compose up -d postgres qdrant redis ollama
```

### 2. Pull Local Models

```bash
ollama pull qwen2.5:1.5b
ollama pull hf.co/CompendiumLabs/bge-base-en-v1.5-gguf:latest
# Or list what's already installed and set CHEMMIND_DEFAULT_* to match:
ollama list
```

### 3. Start the Backend

```bash
cd backend_rust
cp .env.example .env
cargo run
```

Verify at `http://localhost:8000/health`.

### 4. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### 5. Verify

Navigate to `http://localhost:3000/projects`, open or create a workspace, and:

- Select **Ollama Local (qwen2.5:1.5b)** in the assistant panel and chat with real-time streaming
- Click **3D Visualize**, enter `CH4` or `benzene`, and compute 3D coordinates
- Generate a quiz grounded in your workspace documents
- Run multi-document synthesis for cross-paper comparison

---

## Configuration

### Backend (`backend_rust/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `CHEMMIND_DATABASE_URL` | `postgresql://postgres:postgres_password@localhost:5432/chemmind_db` | PostgreSQL connection string |
| `CHEMMIND_SECRET_KEY` | *(change in production)* | JWT signing key |
| `CHEMMIND_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama service endpoint |
| `CHEMMIND_DEFAULT_LLM_MODEL` | `qwen2.5:1.5b` | Default LLM model (must be `ollama list` installed) |
| `CHEMMIND_DEFAULT_EMBEDDING_MODEL` | `hf.co/CompendiumLabs/bge-base-en-v1.5-gguf:latest` | Default embedding model (must be installed) |
| `CHEMMIND_STORAGE_DIR` | `./uploads` | Document file storage |
| `CHEMMIND_MAX_UPLOAD_SIZE_MB` | `50` | Maximum upload size |

### AI Subsystem (`ai/`)

| Variable | Default | Description |
|----------|---------|-------------|
| `CHEMMIND_AI_PROVIDER` | `ollama` | Active LLM provider |
| `CHEMMIND_AI_EMBEDDING_PROVIDER` | `ollama` | Active embedding provider |
| `CHEMMIND_AI_QDRANT_HOST` | `localhost` | Qdrant vector store host |
| `CHEMMIND_AI_QDRANT_PORT` | `6333` | Qdrant vector store port |

Full example available at [backend_rust/.env.example](backend_rust/.env.example).

---

## Testing

Run the complete verification suite:

```bash
# Python AI unit tests
python -m pytest tests/

# Rust backend tests (unit + integration)
cargo test --manifest-path backend_rust/Cargo.toml

# Frontend lint
npm --prefix frontend run lint

# Frontend production build
npm --prefix frontend run build
```

On Windows PowerShell:

```powershell
python -m pytest tests/; cargo test --manifest-path backend_rust/Cargo.toml; npm --prefix frontend run lint; npm --prefix frontend run build
```

---

## Project Structure

```text
chemmind/
├── frontend/                  # Next.js 16 application
│   ├── app/                   #   App Router pages
│   ├── components/            #   React components
│   └── package.json
│
├── backend_rust/              # Axum REST API
│   ├── src/
│   │   ├── api/v1/            #   Route handlers
│   │   ├── models/            #   Data models (SQLx)
│   │   ├── services/          #   Business logic
│   │   └── main.rs
│   ├── migrations/            #   SQL migrations
│   └── Cargo.toml
│
├── ai/                        # Python AI & RAG subsystem
│   ├── agentic/               #   Query routing & agent logic
│   ├── chunking/               #   Document chunking (LaTeX/Chem)
│   ├── chemistry/              #   RDKit molecular engine
│   ├── citations/               #   Citation resolution & linking
│   ├── embeddings/              #   Embedding pipeline
│   ├── generation/              #   RAG service & LLM gateway
│   ├── prompts/                 #   Prompt templates
│   ├── providers/                #   LLM & embedding providers
│   ├── quizzes/                  #   Quiz generation engine
│   ├── retrieval/                #   Hybrid retrieval engine
│   ├── reranking/                #   Result reranking
│   ├── vector_store/             #   Qdrant vector store interface
│   └── config.py
│
├── tests/                     # Cross-cutting test suite
├── scripts/                   # DevOps & utility scripts
├── docker-compose.yml         # Local infrastructure
├── ARCHITECTURE.md            # Detailed system architecture
├── CONTRIBUTING.md            # Contribution workflow
└── LICENSE                    # MIT License
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/workspaces` | CRUD | Workspace management with quota enforcement |
| `/api/v1/workspaces/{id}/documents` | POST | PDF upload, text extraction, semantic metadata |
| `/api/v1/workspaces/{id}/conversations/{id}/chat` | POST | SSE streaming and synchronous RAG generation |
| `/api/v1/chemistry/properties` | POST | SMILES validation and molecular weight calculation |
| `/api/v1/chemistry/3d` | POST | 3D spatial coordinate generation |
| `/api/v1/workspaces/{id}/quizzes` | POST | Grounded multiple-choice quiz generation |
| `/api/v1/workspaces/{id}/reasoning/multi-doc` | POST | Cross-document synthesis and conflict detection |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

```text
Branch Assignments:
  rag        → AI, RAG pipeline, LLM integration
  frontend   → UI, React/Next.js frontend
  backend    → Rust (Axum), APIs, database
  devops     → Deployment, Docker, CI/CD, infrastructure
```

---

## License

This project is licensed under the [MIT License](LICENSE).

Copyright (c) 2026 Raghavapriyan Saravanapriyan
