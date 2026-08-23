"use client";

import { Suspense, useEffect, useState, useRef } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import {
  BookOpen, ChevronDown, ChevronLeft, ChevronRight, Eye, FileText,
  HelpCircle, Layers, Loader2, Menu, MoreHorizontal, PanelLeftClose, PanelRightClose,
  Plus, Search, Send, Sparkles, Upload, X, ZoomIn, ZoomOut, Globe, CheckCircle2, AlertCircle
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { LatexDocument } from "@/components/workspace/LatexDocument";
import { VisualiseModal } from "@/components/workspace/VisualiseModal";
import {
  Citation, ChatMessage, sendChatMessageSync, createConversation,
  fetchQuiz, fetchMultiDocAnalysis, QuizResponse, MultiDocResponse
} from "@/lib/api";

const ease = [0.16, 1, 0.3, 1] as const;

const AI_MODELS = [
  { id: "ollama", name: "Ollama Local (llama3)", desc: "Local Ollama Engine" },
  { id: "chemmind-pro", name: "ChemMind Agentic RAG", desc: "Deep Chemistry RAG" },
  { id: "gpt-4o", name: "GPT-4o", desc: "OpenAI Provider" },
  { id: "claude-sonnet", name: "Claude 3.5 Sonnet", desc: "Anthropic Provider" },
];

const SAMPLE_FILES = [
  { id: "doc-01", name: "Molecular Chemistry & VSEPR.pdf", type: "pdf", date: "Today", content: "Molecular Chemistry" },
  { id: "doc-02", name: "Organic Synthesis & Kinetics.tex", type: "tex", date: "Today", content: "Organic Kinetics" },
  { id: "doc-03", name: "Bond Dissociation & Electronegativity.csv", type: "csv", date: "Aug 20", content: "Bond Data" },
];

function WorkspacePageContent() {
  const searchParams = useSearchParams();
  const projectName = searchParams.get("name") || "Molecular Chemistry Workspace";
  const projectId = searchParams.get("project") || "mol-chem-ws";

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [showVisualiser, setShowVisualiser] = useState(false);
  const [showQuizModal, setShowQuizModal] = useState(false);
  const [showMultiDocModal, setShowMultiDocModal] = useState(false);
  const [selectedModel, setSelectedModel] = useState(AI_MODELS[0]);
  const [modelDropOpen, setModelDropOpen] = useState(false);
  const [files, setFiles] = useState(SAMPLE_FILES);
  const [activeDoc, setActiveDoc] = useState(SAMPLE_FILES[0]);
  const [zoomLevel, setZoomLevel] = useState(100);

  // Chat conversation state
  const [conversationId, setConversationId] = useState<string>("default-conv");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "m-0",
      sender: "assistant",
      content: `Welcome to ChemMind! I am grounded in '${projectName}'. Ask me anything about molecular structures, VSEPR geometries, bond energies, or request 3D visualizations and quizzes.`,
      citations: [
        {
          section: "Workspace Overview",
          excerpt: "ChemMind Agentic RAG & Chemistry Deep Engine initialized.",
          source_type: "document",
          document_id: "doc-01",
        },
      ],
    },
  ]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Responsive desktop panel layout
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1280px)");
    const update = () => { setSidebarOpen(mq.matches); setAssistantOpen(mq.matches); };
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  const handleSendMessage = async (textToSend?: string) => {
    const promptText = (textToSend || query).trim();
    if (!promptText || isGenerating) return;

    const userMsg: ChatMessage = { id: `user-${Date.now()}`, sender: "user", content: promptText };
    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setIsGenerating(true);

    try {
      // Ensure conversation exists or call sync chat endpoint
      let activeConvId = conversationId;
      if (!activeConvId) {
        const conv = await createConversation(projectId, "Research Chat");
        if (conv) {
          activeConvId = conv.id;
          setConversationId(conv.id);
        }
      }

      const res = await sendChatMessageSync(projectId, activeConvId || "default-conv", promptText, selectedModel.id, [activeDoc.id]);
      if (res) {
        setMessages((prev) => [...prev, res]);
      } else {
        // Fallback response if offline
        setMessages((prev) => [
          ...prev,
          {
            id: `asst-${Date.now()}`,
            sender: "assistant",
            content: `ChemMind AI [${selectedModel.name}]: Grounded analysis for "${promptText}". VSEPR theory states that valence electron pairs surrounding a central atom repel each other, dictating molecular shape.`,
            citations: [
              {
                section: "VSEPR Geometry & Bond Stiffness",
                excerpt: `Evidence extracted for '${promptText}'`,
                source_type: "document",
                document_id: activeDoc.id,
              },
            ],
          },
        ]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-background text-foreground">
      {/* ─── LEFT SIDEBAR ─── */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div onClick={() => setSidebarOpen(false)} className="fixed inset-0 z-30 bg-foreground/20 backdrop-blur-[1px] xl:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />
            <motion.aside
              initial={{ x: -280, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: -280, opacity: 0 }}
              transition={{ duration: 0.35, ease }}
              className="fixed inset-y-0 left-0 z-40 flex w-[280px] flex-col border-r border-border/60 bg-surface shadow-2xl xl:relative xl:z-10 xl:shadow-none"
            >
              <FileSidebar
                files={files}
                setFiles={setFiles}
                activeDoc={activeDoc}
                setActiveDoc={setActiveDoc}
                projectName={projectName}
                onClose={() => setSidebarOpen(false)}
              />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ─── MAIN CONTENT ─── */}
      <main className="workspace-main flex h-full min-h-0 min-w-0 flex-1 flex-col">
        {/* Header Toolbar */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/60 bg-surface/90 px-3 backdrop-blur-xl sm:px-5">
          <div className="flex min-w-0 items-center gap-3">
            {!sidebarOpen && (
              <ToolbarIcon label="Open navigation" onClick={() => setSidebarOpen(true)}>
                <Menu size={18} />
              </ToolbarIcon>
            )}
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold tracking-[-0.02em]">{activeDoc.name}</p>
              <p className="hidden text-[11px] text-muted sm:block">
                <Link href="/projects" className="hover:text-foreground transition-colors">{projectName}</Link>
                <span className="mx-1">·</span>Grounded Document
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1 sm:gap-2">
            <div className="hidden items-center sm:flex">
              <ToolbarIcon label="Zoom out" onClick={() => setZoomLevel((z) => Math.max(75, z - 10))}><ZoomOut size={16} /></ToolbarIcon>
              <span className="px-1 text-xs tabular-nums text-muted">{zoomLevel}%</span>
              <ToolbarIcon label="Zoom in" onClick={() => setZoomLevel((z) => Math.min(150, z + 10))}><ZoomIn size={16} /></ToolbarIcon>
              <span className="mx-2 h-4 w-px bg-border/70" />
            </div>

            {/* Quiz Generation Action */}
            <button
              onClick={() => setShowQuizModal(true)}
              className="flex items-center gap-1.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 transition-all"
            >
              <HelpCircle size={14} /> <span className="hidden sm:inline">Generate Quiz</span>
            </button>

            {/* Multi-Doc Synthesis Action */}
            <button
              onClick={() => setShowMultiDocModal(true)}
              className="flex items-center gap-1.5 rounded-xl border border-indigo-500/30 bg-indigo-500/10 px-3 py-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/20 transition-all"
            >
              <Layers size={14} /> <span className="hidden sm:inline">Multi-Doc Synthesis</span>
            </button>

            {/* 3D Visualise Button */}
            <button
              onClick={() => setShowVisualiser(true)}
              className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-md shadow-indigo-500/20 hover:brightness-110 transition-all"
            >
              <Eye size={14} /> 3D Visualise
            </button>

            <ThemeToggle className="ml-1" />

            {!assistantOpen && (
              <button onClick={() => setAssistantOpen(true)} className="ml-1 flex items-center gap-2 rounded-full bg-foreground px-3 py-1.5 text-xs font-semibold text-background transition-transform hover:-translate-y-px active:translate-y-0">
                <Sparkles size={14} /> <span className="hidden sm:inline">Ask ChemMind</span>
              </button>
            )}
          </div>
        </header>

        {/* Document Viewer (LaTeX Rendered) */}
        <div className="min-h-0 flex-1 overflow-y-auto px-3 py-6 sm:px-7 sm:py-8 lg:px-10" style={{ fontSize: `${zoomLevel}%` }}>
          <article className="mx-auto w-full max-w-[48rem] rounded-[18px] border border-border/60 bg-surface px-6 py-8 shadow-[0_10px_30px_rgba(29,29,31,0.05)] sm:rounded-[22px] sm:px-11 sm:py-10">
            <LatexDocument />
          </article>
        </div>
      </main>

      {/* ─── RIGHT ASSISTANT PANEL ─── */}
      <AnimatePresence>
        {assistantOpen && (
          <>
            <motion.div onClick={() => setAssistantOpen(false)} className="fixed inset-0 z-30 bg-foreground/20 backdrop-blur-[1px] xl:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />
            <motion.aside
              initial={{ x: 100, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 100, opacity: 0 }}
              transition={{ duration: 0.35, ease }}
              className="fixed inset-y-0 right-0 z-40 flex w-[360px] flex-col border-l border-border/60 bg-surface shadow-2xl xl:relative xl:z-10 xl:shadow-none"
            >
              <Assistant
                query={query} setQuery={setQuery}
                onClose={() => setAssistantOpen(false)}
                selectedModel={selectedModel}
                setSelectedModel={setSelectedModel}
                modelDropOpen={modelDropOpen}
                setModelDropOpen={setModelDropOpen}
                messages={messages}
                isGenerating={isGenerating}
                onSend={handleSendMessage}
                activeDocName={activeDoc.name}
              />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* 3D Visualizer Modal */}
      <AnimatePresence>
        {showVisualiser && <VisualiseModal onClose={() => setShowVisualiser(false)} />}
      </AnimatePresence>

      {/* Grounded Quiz Modal */}
      <AnimatePresence>
        {showQuizModal && <QuizModal workspaceId={projectId} onClose={() => setShowQuizModal(false)} />}
      </AnimatePresence>

      {/* Multi-Doc Synthesis Modal */}
      <AnimatePresence>
        {showMultiDocModal && <MultiDocModal workspaceId={projectId} files={files} onClose={() => setShowMultiDocModal(false)} />}
      </AnimatePresence>
    </div>
  );
}

export default function WorkspacePage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen w-screen items-center justify-center bg-background text-foreground">
        <div className="flex flex-col items-center gap-3">
          <Loader2 size={32} className="animate-spin text-violet-500" />
          <p className="text-sm font-semibold">Loading ChemMind Workspace...</p>
        </div>
      </div>
    }>
      <WorkspacePageContent />
    </Suspense>
  );
}

/* ─── TOOLBAR ICON ─── */
function ToolbarIcon({ children, label, onClick }: { children: React.ReactNode; label: string; onClick?: () => void }) {
  return (
    <button type="button" onClick={onClick} aria-label={label} className="flex size-8 items-center justify-center rounded-lg text-muted transition-colors hover:bg-background hover:text-foreground">
      {children}
    </button>
  );
}

/* ─── FILE SIDEBAR ─── */
function FileSidebar({ files, setFiles, activeDoc, setActiveDoc, projectName, onClose }: {
  files: typeof SAMPLE_FILES;
  setFiles: (f: typeof SAMPLE_FILES) => void;
  activeDoc: typeof SAMPLE_FILES[0];
  setActiveDoc: (d: typeof SAMPLE_FILES[0]) => void;
  projectName: string;
  onClose: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = () => fileInputRef.current?.click();
  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploaded = e.target.files;
    if (!uploaded) return;
    const newFiles = Array.from(uploaded).map((f, idx) => ({
      id: `uploaded-${Date.now()}-${idx}`,
      name: f.name,
      type: f.name.split(".").pop() || "pdf",
      date: "Just now",
      content: f.name,
    }));
    setFiles([...newFiles, ...files]);
    setActiveDoc(newFiles[0]);
    e.target.value = "";
  };

  const typeIcon = (type: string) => {
    const colors: Record<string, string> = {
      pdf: "bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400",
      tex: "bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400",
      csv: "bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
      doc: "bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400",
      docx: "bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400",
    };
    return colors[type] || "bg-foreground/5 text-muted";
  };

  return (
    <>
      <div className="flex items-center justify-between px-5 py-5">
        <Link href="/projects" className="text-[15px] font-bold tracking-[-0.04em]">CHEMMIND</Link>
        <ToolbarIcon label="Close sidebar" onClick={onClose}><PanelLeftClose size={17} /></ToolbarIcon>
      </div>

      <div className="mx-4 mb-3 flex items-center gap-2 rounded-xl border border-border/60 bg-background/60 px-3 py-2.5">
        <div className="flex size-7 items-center justify-center rounded-lg bg-foreground text-background text-[10px] font-bold">
          {projectName.charAt(0)}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-semibold">{projectName}</p>
          <Link href="/projects" className="text-[10px] text-muted hover:text-foreground transition-colors">Switch project →</Link>
        </div>
      </div>

      <div className="px-4">
        <input ref={fileInputRef} type="file" multiple accept=".pdf,.tex,.csv,.docx,.doc,.txt,.md" onChange={onFileChange} className="hidden" />
        <button onClick={handleUpload} className="flex w-full items-center justify-center gap-2 rounded-xl bg-foreground px-4 py-2.5 text-sm font-semibold text-background transition-transform hover:-translate-y-px active:translate-y-0 shadow-md">
          <Upload size={16} /> Upload Document
        </button>
      </div>

      <div className="mt-4 px-4">
        <div className="flex items-center gap-2 rounded-xl border border-border/60 bg-background px-3 py-2">
          <Search size={14} className="text-muted" />
          <input type="text" placeholder="Search files..." className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted/60" />
        </div>
      </div>

      <div className="mt-4 flex-1 overflow-y-auto px-3">
        <p className="px-3 text-[10px] font-semibold tracking-[0.14em] text-muted uppercase">Workspace Documents</p>
        <div className="mt-2 space-y-1">
          {files.map((file) => (
            <button
              key={file.id}
              onClick={() => setActiveDoc(file)}
              className={cn(
                "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors border",
                activeDoc.id === file.id ? "bg-background border-violet-500/40 text-foreground font-semibold shadow-sm" : "border-transparent text-muted hover:bg-background hover:text-foreground"
              )}
            >
              <span className={cn("flex size-8 shrink-0 items-center justify-center rounded-lg text-[10px] font-bold uppercase", typeIcon(file.type))}>
                {file.type.slice(0, 3)}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{file.name}</p>
                <p className="text-[10px] text-muted/60">{file.date}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="border-t border-border/60 p-4">
        <div className="upload-zone cursor-pointer" onClick={handleUpload}>
          <Upload size= {18} className="mx-auto text-muted mb-1" />
          <p className="text-xs text-muted">Drop papers or datasets here</p>
        </div>
      </div>
    </>
  );
}

/* ─── ASSISTANT PANEL ─── */
function Assistant({ query, setQuery, onClose, selectedModel, setSelectedModel, modelDropOpen, setModelDropOpen, messages, isGenerating, onSend, activeDocName }: {
  query: string; setQuery: (v: string) => void; onClose: () => void;
  selectedModel: typeof AI_MODELS[0];
  setSelectedModel: (m: typeof AI_MODELS[0]) => void;
  modelDropOpen: boolean;
  setModelDropOpen: (v: boolean) => void;
  messages: ChatMessage[];
  isGenerating: boolean;
  onSend: (txt?: string) => void;
  activeDocName: string;
}) {
  const suggestions = ["Explain VSEPR Theory", "Show bond dissociation math", "Lookup benzene properties"];
  const dropRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isGenerating]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) setModelDropOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [setModelDropOpen]);

  return (
    <>
      <div className="flex items-center justify-between border-b border-border/60 px-5 py-4">
        <div className="flex items-center gap-3">
          <span className="flex size-8 items-center justify-center rounded-full bg-accent text-white shadow-sm"><Sparkles size={15} /></span>
          <div>
            <h2 className="text-sm font-semibold">ChemMind Agentic AI</h2>
            <p className="mt-0.5 text-[11px] text-muted">Grounded & Live Web Search</p>
          </div>
        </div>
        <ToolbarIcon label="Close assistant" onClick={onClose}><PanelRightClose size={18} /></ToolbarIcon>
      </div>

      <div className="border-b border-border/50 bg-background/45 px-5 py-2.5 flex items-center justify-between">
        <p className="truncate text-xs font-medium text-muted">Context: <span className="text-foreground font-semibold">{activeDocName}</span></p>
        <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full">
          <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" /> Active
        </span>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={msg.id || i} className={cn("flex flex-col", msg.sender === "user" ? "items-end" : "items-start")}>
            <div className={cn(
              "max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm",
              msg.sender === "user"
                ? "rounded-tr-md bg-foreground text-background font-medium"
                : "rounded-tl-md border border-accent/20 bg-surface text-foreground"
            )}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 border-t border-border/50 pt-2 space-y-1">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-accent">Grounded Citations & Evidence:</p>
                  {msg.citations.map((c, idx) => (
                    <div key={idx} className="flex items-start gap-1.5 text-[11px] text-muted">
                      {c.source_type === "web" ? (
                        <a href={c.url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-blue-500 hover:underline font-semibold">
                          <Globe size={11} /> {c.title || c.domain || "Web Link"}
                        </a>
                      ) : (
                        <span>📄 <strong>{c.section || "Section"}</strong>: {c.excerpt}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {isGenerating && (
          <div className="flex items-center gap-2 text-xs text-muted">
            <Loader2 size={14} className="animate-spin text-violet-500" />
            <span>ChemMind reasoning & querying RAG gateway...</span>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input controls */}
      <div className="border-t border-border/60 bg-background/45 p-4">
        {!query && (
          <div className="mb-2.5 flex gap-1.5 overflow-x-auto pb-1">
            {suggestions.map((text) => (
              <button key={text} onClick={() => onSend(text)} className="shrink-0 rounded-full border border-border/70 bg-surface px-3 py-1 text-xs font-medium text-muted transition-colors hover:border-accent/40 hover:text-foreground">
                {text}
              </button>
            ))}
          </div>
        )}

        <div ref={dropRef} className="relative mb-2">
          <button
            onClick={() => setModelDropOpen(!modelDropOpen)}
            className="flex items-center gap-2 rounded-lg border border-border/60 bg-surface px-3 py-1 text-[11px] font-medium text-muted transition-colors hover:text-foreground hover:border-border"
          >
            <Sparkles size={12} className="text-violet-500" />
            {selectedModel.name}
            <ChevronDown size={12} className={cn("transition-transform", modelDropOpen && "rotate-180")} />
          </button>
          <AnimatePresence>
            {modelDropOpen && (
              <motion.div
                initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }}
                className="absolute bottom-full left-0 mb-1 w-60 rounded-xl border border-border/60 bg-surface p-1.5 shadow-xl z-50"
              >
                {AI_MODELS.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => { setSelectedModel(m); setModelDropOpen(false); }}
                    className={cn(
                      "flex w-full items-center justify-between rounded-lg px-3 py-2 text-left transition-colors",
                      m.id === selectedModel.id ? "bg-accent/10 text-foreground font-semibold" : "text-muted hover:bg-background hover:text-foreground"
                    )}
                  >
                    <span className="text-xs">{m.name}</span>
                    <span className="text-[10px] text-muted">{m.desc}</span>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="rounded-2xl border border-border/70 bg-surface p-2 shadow-sm focus-within:border-accent/60">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSend(); } }}
            placeholder="Ask ChemMind AI…"
            rows={2}
            className="block w-full resize-none bg-transparent px-2 py-1 text-sm outline-none placeholder:text-muted/80"
          />
          <div className="flex items-center justify-between px-1 pt-1">
            <span className="text-[10px] text-muted">Enter to send</span>
            <button
              aria-label="Send message"
              disabled={isGenerating || !query.trim()}
              onClick={() => onSend()}
              className={cn(
                "flex size-8 items-center justify-center rounded-full transition-all",
                query.trim() && !isGenerating ? "bg-foreground text-background hover:scale-105" : "bg-border/40 text-muted cursor-not-allowed"
              )}
            >
              <Send size={14} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

/* ─── GROUNDED QUIZ MODAL ─── */
function QuizModal({ workspaceId, onClose }: { workspaceId: string; onClose: () => void }) {
  const [loading, setLoading] = useState(false);
  const [quiz, setQuiz] = useState<QuizResponse | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    const data = await fetchQuiz(workspaceId, "VSEPR Geometry & Chemical Bonding", 3);
    if (data) {
      setQuiz(data);
    } else {
      // Local fallback quiz
      setQuiz({
        quiz_id: "quiz-01",
        title: "VSEPR Geometry & Electronegativity Quiz",
        workspace_id: workspaceId,
        questions: [
          {
            question_id: "q1",
            question_text: "What is the expected molecular geometry of methane (CH4) under VSEPR theory?",
            question_type: "multiple_choice",
            options: [
              { option_letter: "A", option_text: "Linear", is_correct: false },
              { option_letter: "B", option_text: "Tetrahedral", is_correct: true },
              { option_letter: "C", option_text: "Trigonal planar", is_correct: false },
              { option_letter: "D", option_text: "Octahedral", is_correct: false },
            ],
            correct_answer: "B",
            explanation: "CH4 has 4 bonding electron pairs around carbon with 0 lone pairs, yielding 109.5° tetrahedral geometry.",
            citations: [],
          },
          {
            question_id: "q2",
            question_text: "According to the Electronegativity Principle, a chemical bond is predominantly ionic when Δχ is:",
            question_type: "multiple_choice",
            options: [
              { option_letter: "A", option_text: "> 1.7", is_correct: true },
              { option_letter: "B", option_text: "< 0.4", is_correct: false },
              { option_letter: "C", option_text: "= 0", is_correct: false },
            ],
            correct_answer: "A",
            explanation: "When electronegativity difference Δχ exceeds 1.7, the bonding electrons are predominantly transferred, creating ionic character.",
            citations: [],
          },
        ],
      });
    }
    setLoading(false);
  };

  useEffect(() => { handleGenerate(); }, []);

  return (
    <motion.div className="visualise-modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
      <motion.div className="visualise-modal max-w-xl" initial={{ scale: 0.92, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.92, opacity: 0 }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-border/60 px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="flex size-8 items-center justify-center rounded-xl bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-500/20">AI</span>
            <div>
              <h3 className="text-sm font-semibold">Grounded Quiz Assessment</h3>
              <p className="text-[11px] text-muted">Generated from workspace research documents</p>
            </div>
          </div>
          <button onClick={onClose} className="flex size-8 items-center justify-center rounded-lg text-muted hover:bg-background transition-colors"><X size={18} /></button>
        </div>

        <div className="p-6 max-h-[75vh] overflow-y-auto space-y-6">
          {loading && (
            <div className="py-12 text-center">
              <Loader2 size={32} className="mx-auto animate-spin text-emerald-500 mb-3" />
              <p className="text-sm font-semibold">Generating grounded questions from papers...</p>
            </div>
          )}

          {quiz && !loading && (
            <div className="space-y-6">
              <h4 className="text-base font-bold text-foreground">{quiz.title}</h4>
              {quiz.questions.map((q, idx) => (
                <div key={q.question_id} className="rounded-xl border border-border/70 p-4 bg-background/50 space-y-3">
                  <p className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">Question {idx + 1}</p>
                  <p className="text-sm font-medium text-foreground">{q.question_text}</p>
                  <div className="space-y-2">
                    {q.options.map((opt) => {
                      const isSel = selectedAnswers[q.question_id] === opt.option_letter;
                      const showResult = submitted;
                      const isCorrect = opt.is_correct;
                      return (
                        <button
                          key={opt.option_letter}
                          disabled={submitted}
                          onClick={() => setSelectedAnswers((prev) => ({ ...prev, [q.question_id]: opt.option_letter }))}
                          className={cn(
                            "w-full flex items-center justify-between rounded-lg border px-3 py-2 text-left text-xs transition-colors",
                            showResult && isCorrect ? "border-emerald-500 bg-emerald-500/10 font-bold text-emerald-600" : "",
                            showResult && isSel && !isCorrect ? "border-red-500 bg-red-500/10 text-red-600" : "",
                            !showResult && isSel ? "border-violet-500 bg-violet-500/10 font-semibold" : "border-border/60 hover:bg-background"
                          )}
                        >
                          <span><strong>{opt.option_letter}.</strong> {opt.option_text}</span>
                          {showResult && isCorrect && <CheckCircle2 size={14} className="text-emerald-500" />}
                        </button>
                      );
                    })}
                  </div>
                  {submitted && (
                    <div className="mt-2 text-xs text-muted bg-surface p-2.5 rounded-lg border border-border/50">
                      <strong>Explanation:</strong> {q.explanation}
                    </div>
                  )}
                </div>
              ))}

              {!submitted ? (
                <button onClick={() => setSubmitted(true)} className="w-full rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors shadow-md">
                  Submit Answers & Grade
                </button>
              ) : (
                <button onClick={() => { setSubmitted(false); handleGenerate(); }} className="w-full rounded-xl border border-border/70 py-3 text-sm font-semibold text-foreground hover:bg-background transition-colors">
                  Generate Another Quiz
                </button>
              )}
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

/* ─── MULTI-DOC SYNTHESIS MODAL ─── */
function MultiDocModal({ workspaceId, files, onClose }: { workspaceId: string; files: typeof SAMPLE_FILES; onClose: () => void }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MultiDocResponse | null>(null);

  const handleSynthesize = async () => {
    setLoading(true);
    const docIds = files.map((f) => f.id);
    const data = await fetchMultiDocAnalysis(workspaceId, "Compare molecular orbital vs VSEPR predictions", docIds);
    if (data) {
      setResult(data);
    } else {
      setResult({
        workspace_id: workspaceId,
        summary: "Cross-document synthesis complete. Comparison reveals strong alignment on VSEPR tetrahedral geometries with slight deviations in bond dissociation energies between PDF and Tex datasets.",
        comparison_matrix: [
          { topic: "Molecular Geometry", document_id: "doc-01", excerpt: "CH4 exhibits tetrahedral symmetry", value_or_finding: "109.5° Bond Angle" },
          { topic: "Bond Energy Equation", document_id: "doc-02", excerpt: "Morse potential E_bond", value_or_finding: "D_e dissociation parameter" },
        ],
        discrepancies: [
          {
            topic: "Equilibrium Bond Stiffness",
            document_id_a: "doc-01",
            claim_a: "β parameter estimated at 1.85 Å⁻¹",
            document_id_b: "doc-03",
            claim_b: "Empirical fit suggests β = 1.92 Å⁻¹",
            nature_of_conflict: "Minor variation due to experimental temperature variance",
          },
        ],
        citations: [],
      });
    }
    setLoading(false);
  };

  useEffect(() => { handleSynthesize(); }, []);

  return (
    <motion.div className="visualise-modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
      <motion.div className="visualise-modal max-w-2xl" initial={{ scale: 0.92, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.92, opacity: 0 }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-border/60 px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="flex size-8 items-center justify-center rounded-xl bg-indigo-600 text-white text-xs font-bold shadow-md shadow-indigo-500/20">AI</span>
            <div>
              <h3 className="text-sm font-semibold">Multi-Document Reasoning & Conflict Detection</h3>
              <p className="text-[11px] text-muted">Cross-examination across all uploaded research papers</p>
            </div>
          </div>
          <button onClick={onClose} className="flex size-8 items-center justify-center rounded-lg text-muted hover:bg-background transition-colors"><X size={18} /></button>
        </div>

        <div className="p-6 max-h-[75vh] overflow-y-auto space-y-5">
          {loading && (
            <div className="py-12 text-center">
              <Loader2 size={32} className="mx-auto animate-spin text-indigo-600 mb-3" />
              <p className="text-sm font-semibold">Comparing papers & detecting discrepancies...</p>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-5">
              <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4">
                <p className="text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider mb-1">Executive Summary</p>
                <p className="text-xs leading-5 text-foreground">{result.summary}</p>
              </div>

              {/* Comparison Matrix */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted mb-2">Cross-Document Comparison Matrix</h4>
                <div className="border border-border/70 rounded-xl overflow-hidden text-xs">
                  <div className="grid grid-cols-3 bg-surface p-2.5 font-bold border-b border-border/60">
                    <span>Topic</span>
                    <span>Doc ID</span>
                    <span>Finding</span>
                  </div>
                  {result.comparison_matrix.map((item, idx) => (
                    <div key={idx} className="grid grid-cols-3 p-2.5 border-b border-border/40 hover:bg-background/50">
                      <span className="font-semibold">{item.topic}</span>
                      <span className="text-muted">{item.document_id}</span>
                      <span className="text-violet-600 dark:text-violet-400 font-medium">{item.value_or_finding}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Discrepancies */}
              {result.discrepancies.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-amber-500 mb-2 flex items-center gap-1">
                    <AlertCircle size={14} /> Detected Discrepancies & Conflicts
                  </h4>
                  <div className="space-y-2">
                    {result.discrepancies.map((disc, idx) => (
                      <div key={idx} className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs space-y-1">
                        <p className="font-bold text-amber-700 dark:text-amber-300">{disc.topic}</p>
                        <p><strong>{disc.document_id_a}:</strong> &quot;{disc.claim_a}&quot;</p>
                        <p><strong>{disc.document_id_b}:</strong> &quot;{disc.claim_b}&quot;</p>
                        <p className="text-[11px] text-muted pt-1 border-t border-amber-500/20">Reason: {disc.nature_of_conflict}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}
