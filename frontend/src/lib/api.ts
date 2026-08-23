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
}

export interface Workspace {
  id: string;
  name: string;
  description: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
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

// ── API CLIENT FUNCTIONS ──

export async function fetchWorkspaces(): Promise<Workspace[]> {
  try {
    const res = await fetch(`${API_BASE}/workspaces`);
    if (!res.ok) throw new Error("Failed to fetch workspaces");
    return await res.json();
  } catch (err) {
    console.warn("API server unreachable, returning empty list:", err);
    return [];
  }
}

export async function createWorkspace(name: string, description: string): Promise<Workspace | null> {
  try {
    const res = await fetch(`${API_BASE}/workspaces`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description }),
    });
    if (!res.ok) throw new Error("Failed to create workspace");
    return await res.json();
  } catch (err) {
    console.error("Failed to create workspace:", err);
    return null;
  }
}

export async function deleteWorkspace(id: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/workspaces/${id}`, { method: "DELETE" });
    return res.ok;
  } catch (err) {
    console.error("Failed to delete workspace:", err);
    return false;
  }
}

export async function createConversation(workspaceId: string, title = "New Conversation") {
  try {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error("Failed to create conversation");
    return await res.json();
  } catch (err) {
    console.error("Failed to create conversation:", err);
    return null;
  }
}

export async function sendChatMessageSync(
  workspaceId: string,
  conversationId: string,
  prompt: string,
  modelProvider = "ollama",
  selectedDocIds?: string[]
): Promise<ChatMessage | null> {
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
    if (!res.ok) throw new Error("Failed to send chat message");
    const data = await res.json();
    return {
      id: data.message_id,
      sender: "assistant",
      content: data.content,
      citations: data.citations || [],
    };
  } catch (err) {
    console.error("Chat sync error:", err);
    return null;
  }
}

export async function fetchChemistry3D(promptOrSmiles: string): Promise<Mol3DCoordinates | null> {
  try {
    const res = await fetch(`${API_BASE}/chemistry/3d`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ smiles: promptOrSmiles }),
    });
    if (!res.ok) throw new Error("Failed to fetch 3D coordinates");
    return await res.json();
  } catch (err) {
    console.error("Chemistry 3D error:", err);
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
    if (!res.ok) throw new Error("Failed to fetch properties");
    return await res.json();
  } catch (err) {
    console.error("Chemistry properties error:", err);
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
    if (!res.ok) throw new Error("Failed to generate quiz");
    return await res.json();
  } catch (err) {
    console.error("Quiz generation error:", err);
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
    if (!res.ok) throw new Error("Failed to analyze multi-documents");
    return await res.json();
  } catch (err) {
    console.error("Multi-doc analysis error:", err);
    return null;
  }
}
