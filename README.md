# ChemMind — Production Agentic RAG & Chemistry Deep Engine

ChemMind is an agentic research platform designed for molecular chemistry, literature review, and interactive paper synthesis. It seamlessly connects a **Next.js 16 Frontend**, a **Rust (Axum) Backend**, and an **Agentic AI & RAG Subsystem** capable of running on local Ollama models.

---

## 🏛️ Technical Stack & Architectural Pillars

ChemMind is built upon three distinct architectural pillars:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 16)                           │
│   • React 19 / TypeScript           • KaTeX LaTeX Document Reader      │
│   • Tailwind CSS & Framer Motion    • 3D Molecular Mesh & Property UI  │
│   • SSE Real-time Chat Streaming    • Workspace & Document Sidebars    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST / SSE API Protocols
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      BACKEND (Rust / Axum API)                         │
│   • Axum + SQLx (PostgreSQL)           • SSE Streaming Endpoint        │
│   • JWT auth + bcrypt password hashing • Usage Limits & Quotas         │
│   • Document Ingestion & Storage       • Chemistry, Quiz & Multi-Doc   │
│   • Provider-Independent AI Gateway    • Multi-Doc Reasoning Routers   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ AI Gateway Bridge
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      AI & AGENTIC RAG SUBSYSTEM                        │
│   • Agentic Router & Web Fallback   • Chemistry Property Engine (RDKit) │
│   • Dense/Sparse Hybrid Retrieval   • Grounded Quiz Generator          │
│   • Citation Resolver & Linker      • Multi-Doc Reasoning Engine       │
│   • Ollama Local LLM Provider       • Provider-Agnostic Gateway        │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Pillar 1: Modern Frontend Architecture (`frontend/`)

- **Framework & Core**: Next.js 16 (App Router with Turbopack), React 19, TypeScript.
- **Styling & Aesthetics**: Custom Vanilla CSS & Tailwind CSS with curated color schemes, dark/light theme toggle, glassmorphism overlays, and Framer Motion micro-animations.
- **LaTeX Document Rendering**: KaTeX engine rendering inline math ($\psi_{sp^3}$) and display block equations ($\theta_{\min}$) with section navigation.
- **3D Molecular Visualizer**: Interactive 3D molecular mesh renderer calculating real 3D atomic coordinates, SMILES syntax validation, empirical formula, and molecular weights.
- **Workspace Dashboard**: Dynamic document upload, file switching sidebar, quiz assessment modals, and multi-document comparison synthesis UI.
- **Real-Time Assistant Panel**: Dynamic model selector (Ollama Local, ChemMind RAG, GPT-4o, Claude 3.5 Sonnet), SSE token streaming, and clickable citation links.

---

### Pillar 2: Backend API (`backend_rust/`)

- **Framework & Runtime**: Axum (Rust) with Tokio.
- **Database ORM**: SQLx with PostgreSQL (async connection pooling).
- **API Endpoints**:
  - `/api/v1/workspaces`: Workspace CRUD, member access roles, quota enforcement.
  - `/api/v1/workspaces/{id}/documents`: PDF document upload, text extraction, semantic metadata.
  - `/api/v1/workspaces/{id}/conversations/{id}/chat`: SSE token streaming and synchronous RAG generation.
  - `/api/v1/chemistry`: Chemical SMILES property calculation (`/properties`) and 3D spatial coordinates (`/3d`).
  - `/api/v1/workspaces/{id}/quizzes`: Grounded multiple-choice quiz generation with evidence citations.
  - `/api/v1/workspaces/{id}/reasoning/multi-doc`: Cross-document matrix synthesis and discrepancy detection.
- **Security & Development Flow**: JWT bearer token authentication with bcrypt password hashing. The frontend auto-provisions a local developer account so startup is friction-free.

---

### Pillar 3: AI & Agentic RAG Subsystem (`ai/`)

- **Agentic Router (`AgenticRouter`)**: Autonomously evaluates internal document sufficiency vs query intent. Routes queries to internal vector search, web search fallback, or hybrid synthesis.
- **Hybrid Retrieval Engine (`HybridRetriever`)**: Merges dense vector embeddings (`DenseRetriever`) with sparse keyword matching (`BM25KeywordRetriever`) via Reciprocal Rank Fusion (`rrf`).
- **Citation Resolver (`CitationResolver`)**: Extracts grounded source evidence and attaches metadata (document ID, page number, section title, web URLs) for exact traceability.
- **Chemistry Engine (`ChemistryEngine`)**: Validates SMILES strings, calculates exact molecular weights, extracts empirical formulas, and computes 3D molecular spatial mesh coordinates via RDKit with pure-Python heuristics fallback.
- **Grounded Quiz Engine (`QuizGenerator`)**: Analyzes document chunks to craft multiple-choice questions with plausible distractors and explanation citations.
- **Multi-Doc Reasoning Engine (`MultiDocReasoningEngine`)**: Cross-examines multiple research papers to construct comparative analysis matrices and detect conflicting claims.
- **Local Ollama Integration (`OllamaLLMProvider` & `LLMGateway`)**: Provider-agnostic gateway supporting local Ollama models (`llama3`, `mistral`, `gemma`) via REST (`http://localhost:11434/api/chat`).

---

## 🚀 Definitive Local Launch Guide (Using Local Ollama)

Follow these steps to run the complete ChemMind application locally with your own Ollama model.

### Step 1: Install & Start Ollama
Ensure [Ollama](https://ollama.com) is installed on your local machine. Start the local server:
```bash
ollama serve
```
*(Default host: `http://localhost:11434`)*

### Step 2: Pull Your Local Model
In a separate terminal, pull your preferred LLM and embedding models (e.g. `llama3` or `mistral`):
```bash
ollama pull llama3
ollama pull nomic-embed-text
```

### Step 3: Start the Backend API (Rust)
1. Start the Postgres + Ollama infrastructure:
```bash
docker-compose up -d postgres ollama
```
2. Open a terminal in the root directory:
```bash
cd backend_rust
cp .env.example .env
```
3. Run the Axum development server:
```bash
cargo run
```
4. Confirm backend health by navigating to `http://localhost:8000/health`.

### Step 4: Start the Frontend Application (Next.js)
1. Open a new terminal in the `frontend/` folder:
```bash
cd frontend
npm run dev
```
2. Open `http://localhost:3000` in your web browser.

### Step 5: Verify the Application
- Navigate to the **Projects** dashboard at `http://localhost:3000/projects`.
- Click **Open Workspace** or create a new workspace.
- In the Workspace view:
  - **Chat Assistant**: Select **"Ollama Local (llama3)"** in the assistant panel and type a query. Watch real-time streaming tokens and citation badges!
  - **3D Visualise**: Click the **"3D Visualise"** button in the header toolbar, enter `CH4` or `benzene`, and click **Compute 3D Structure** to render calculated 3D coordinates and molecular properties.
  - **Generate Quiz**: Click **"Generate Quiz"** in the top bar to create an assessment grounded in your workspace documents.
  - **Multi-Doc Synthesis**: Click **"Multi-Doc Synthesis"** to perform cross-document comparison and conflict detection.

---

## 🧪 Automated Testing & Verification

Run the complete verification suite from the repository root. This runs the AI tests,
Rust tests, frontend linting, and the frontend production build:

```bash
# Python AI tests
python -m pytest ai/tests

# Rust backend tests, including integration tests
cargo test --manifest-path backend_rust/Cargo.toml

# Frontend checks
npm --prefix frontend run lint
npm --prefix frontend run build
```

On Windows PowerShell, run the same checks with:

```powershell
python -m pytest ai/tests; cargo test --manifest-path backend_rust/Cargo.toml; npm --prefix frontend run lint; npm --prefix frontend run build
```

Run an individual package when diagnosing a failure:

```bash
# AI tests
python -m pytest ai/tests

# Rust backend tests
cargo test --manifest-path backend_rust/Cargo.toml

# Frontend lint and production build
npm --prefix frontend run lint
npm --prefix frontend run build
```
