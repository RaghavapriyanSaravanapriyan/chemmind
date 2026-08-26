export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface Citation {
  document_id?: string;
  page?: number;
  chunk_id?: string;
  section?: string;
  excerpt?: string;
  source_type?: string;
  url?: string;
  title?: string;
  domain?: string;
}

export interface ChatMessage {
  id?: string;
  sender: "user" | "assistant";
  content: string;
  citations?: Citation[];
  timestamp?: number;
}

export interface Workspace {
  id: string;
  name: string;
  description: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  color?: string;
}

export interface DocumentItem {
  id: string;
  workspace_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  uploaded_at: string;
}

export interface MolecularProperties {
  smiles: string;
  molecular_weight: number;
  chemical_formula: string;
  atom_count: number;
  is_valid_smiles: boolean;
}

export interface Mol3DCoordinates {
  smiles: string;
  atoms: string[];
  coordinates_3d: number[][];
}

export interface QuizOption {
  option_letter: string;
  option_text: string;
  is_correct: boolean;
}

export interface QuizQuestion {
  question_id: string;
  question_text: string;
  question_type: string;
  options: QuizOption[];
  correct_answer: string;
  explanation: string;
  citations: Citation[];
}

export interface QuizResponse {
  quiz_id: string;
  title: string;
  questions: QuizQuestion[];
  workspace_id: string;
}

export interface MultiDocResponse {
  summary: string;
  comparison_matrix: Array<{
    topic: string;
    document_id: string;
    excerpt: string;
    value_or_finding: string;
  }>;
  discrepancies: Array<{
    topic: string;
    document_id_a: string;
    claim_a: string;
    document_id_b: string;
    claim_b: string;
    nature_of_conflict: string;
  }>;
  citations: Citation[];
  workspace_id: string;
}

// ── LOCALSTORAGE PERSISTENCE HELPERS ──

const STORAGE_KEYS = {
  WORKSPACES: "chemmind_workspaces",
  DOCUMENTS: (wsId: string) => `chemmind_docs_${wsId}`,
  MESSAGES: (wsId: string) => `chemmind_msgs_${wsId}`,
};

function safeGetJSON<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function safeSetJSON(key: string, value: unknown) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // storage full or unavailable
  }
}

// ── WORKSPACE CRUD (localStorage with backend fallback) ──

export function getLocalWorkspaces(): Workspace[] {
  return safeGetJSON<Workspace[]>(STORAGE_KEYS.WORKSPACES, []);
}

export function saveLocalWorkspaces(workspaces: Workspace[]) {
  safeSetJSON(STORAGE_KEYS.WORKSPACES, workspaces);
}

export async function fetchWorkspaces(): Promise<Workspace[]> {
  try {
    const res = await fetch(`${API_BASE}/workspaces`);
    if (!res.ok) throw new Error("Failed");
    const remote = await res.json();
    if (remote && remote.length > 0) return remote;
  } catch {
    // backend unreachable
  }
  return getLocalWorkspaces();
}

export async function createWorkspace(name: string, description: string, color?: string): Promise<Workspace> {
  const ws: Workspace = {
    id: `ws-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name,
    description,
    is_archived: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    color,
  };

  try {
    const res = await fetch(`${API_BASE}/workspaces`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description }),
    });
    if (res.ok) {
      const remote = await res.json();
      ws.id = remote.id;
    }
  } catch {
    // use local id
  }

  const all = getLocalWorkspaces();
  all.unshift(ws);
  saveLocalWorkspaces(all);
  return ws;
}

export async function deleteWorkspace(id: string): Promise<boolean> {
  try {
    await fetch(`${API_BASE}/workspaces/${id}`, { method: "DELETE" });
  } catch {
    // ignore
  }
  const all = getLocalWorkspaces().filter((w) => w.id !== id);
  saveLocalWorkspaces(all);
  // Clean up documents and messages
  if (typeof window !== "undefined") {
    localStorage.removeItem(STORAGE_KEYS.DOCUMENTS(id));
    localStorage.removeItem(STORAGE_KEYS.MESSAGES(id));
  }
  return true;
}

// ── DOCUMENT PERSISTENCE ──

export interface LocalDocument {
  id: string;
  name: string;
  type: string;
  date: string;
  content: string;
}

export function getLocalDocuments(workspaceId: string): LocalDocument[] {
  return safeGetJSON<LocalDocument[]>(STORAGE_KEYS.DOCUMENTS(workspaceId), []);
}

export function saveLocalDocuments(workspaceId: string, docs: LocalDocument[]) {
  safeSetJSON(STORAGE_KEYS.DOCUMENTS(workspaceId), docs);
}

// ── CHAT MESSAGE PERSISTENCE ──

export function getLocalMessages(workspaceId: string): ChatMessage[] {
  return safeGetJSON<ChatMessage[]>(STORAGE_KEYS.MESSAGES(workspaceId), []);
}

export function saveLocalMessages(workspaceId: string, msgs: ChatMessage[]) {
  safeSetJSON(STORAGE_KEYS.MESSAGES(workspaceId), msgs);
}

// ── AI CHAT (with client-side fallback) ──

export async function createConversation(workspaceId: string, title = "New Conversation") {
  try {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error("Failed");
    return await res.json();
  } catch {
    return { id: `conv-${Date.now()}` };
  }
}

export async function sendChatMessageSync(
  workspaceId: string,
  conversationId: string,
  prompt: string,
  modelProvider = "llama3:latest",
  selectedDocIds?: string[]
): Promise<ChatMessage> {
  try {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/conversations/${conversationId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        model_provider: modelProvider,
        selected_document_ids: selectedDocIds,
      }),
    });
    if (!res.ok) throw new Error("Failed");
    const data = await res.json();
    return {
      id: data.message_id,
      sender: "assistant",
      content: data.content,
      citations: data.citations || [],
      timestamp: Date.now(),
    };
  } catch {
    // Client-side AI fallback using local Ollama directly
    try {
      const ollamaRes = await fetch("http://localhost:11434/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: modelProvider,
          prompt: prompt,
          stream: false
        })
      });
      if (ollamaRes.ok) {
        const ollamaData = await ollamaRes.json();
        return {
          id: `asst-${Date.now()}`,
          sender: "assistant",
          content: `[${modelProvider}]\n\n${ollamaData.response}`,
          citations: [],
          timestamp: Date.now(),
        };
      }
    } catch(e) {
      console.warn("Ollama direct fetch failed", e);
    }
    
    return {
      id: `asst-${Date.now()}`,
      sender: "assistant",
      content: `[Error]\n\nI could not reach the backend or local Ollama. Please ensure Ollama is running.`,
      citations: [],
      timestamp: Date.now(),
    };
  }
}

// ── CHEMISTRY API ──

export async function fetchChemistry3D(promptOrSmiles: string): Promise<Mol3DCoordinates | null> {
  try {
    const res = await fetch(`${API_BASE}/chemistry/3d`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ smiles: promptOrSmiles }),
    });
    if (!res.ok) throw new Error("Failed");
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchChemistryProperties(promptOrSmiles: string): Promise<MolecularProperties | null> {
  try {
    const res = await fetch(`${API_BASE}/chemistry/properties`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ smiles: promptOrSmiles }),
    });
    if (!res.ok) throw new Error("Failed");
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchQuiz(workspaceId: string, topic: string, numQuestions = 3): Promise<QuizResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/quizzes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, num_questions: numQuestions }),
    });
    if (!res.ok) throw new Error("Failed");
    return await res.json();
  } catch {
    try {
      const ollamaRes = await fetch("http://localhost:11434/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "llama3:latest",
          prompt: `Generate a multiple choice quiz about ${topic} with ${numQuestions} questions. Return ONLY a valid JSON object matching this schema:\n{"title": "Quiz Title", "questions": [{"question_id": "q1", "question_text": "...", "question_type": "multiple_choice", "options": [{"option_letter": "A", "option_text": "...", "is_correct": true}, {"option_letter": "B", "option_text": "...", "is_correct": false}, {"option_letter": "C", "option_text": "...", "is_correct": false}, {"option_letter": "D", "option_text": "...", "is_correct": false}], "correct_answer": "A", "explanation": "...", "citations": []}]}`,
          stream: false,
          format: "json"
        })
      });
      if (ollamaRes.ok) {
        const ollamaData = await ollamaRes.json();
        const parsed = JSON.parse(ollamaData.response);
        return {
          quiz_id: `quiz-${Date.now()}`,
          title: parsed.title || "Generated Quiz",
          workspace_id: workspaceId,
          questions: parsed.questions || []
        };
      }
    } catch(e) {
      console.warn(e);
    }
    return null;
  }
}

export async function fetchMultiDocAnalysis(workspaceId: string, queryText: string, documentIds: string[]): Promise<MultiDocResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/reasoning/multi-doc`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query_text: queryText, document_ids: documentIds }),
    });
    if (!res.ok) throw new Error("Failed");
    return await res.json();
  } catch {
    try {
      const ollamaRes = await fetch("http://localhost:11434/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "llama3:latest",
          prompt: `Perform a multi-document synthesis on the topic "${queryText}". Return ONLY a valid JSON object matching this schema:\n{"summary": "Overall summary of the analysis...", "comparison_matrix": [{"topic": "...", "document_id": "Doc 1", "excerpt": "...", "value_or_finding": "..."}], "discrepancies": [{"topic": "...", "document_id_a": "Doc 1", "claim_a": "...", "document_id_b": "Doc 2", "claim_b": "...", "nature_of_conflict": "..."}]}`,
          stream: false,
          format: "json"
        })
      });
      if (ollamaRes.ok) {
        const ollamaData = await ollamaRes.json();
        const parsed = JSON.parse(ollamaData.response);
        return {
          workspace_id: workspaceId,
          summary: parsed.summary || "Synthesis complete.",
          comparison_matrix: parsed.comparison_matrix || [],
          discrepancies: parsed.discrepancies || [],
          citations: []
        };
      }
    } catch(e) {
      console.warn(e);
    }
    return null;
  }
}
