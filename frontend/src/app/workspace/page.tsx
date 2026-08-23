"use client";

import { useEffect, useState, useRef } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import {
  BookOpen, ChevronDown, ChevronLeft, ChevronRight, Eye, FileText,
  Menu, MoreHorizontal, PanelLeftClose, PanelRightClose, Plus,
  Search, Send, Sparkles, Upload, X, ZoomIn, ZoomOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { LatexDocument } from "@/components/workspace/LatexDocument";
import { VisualiseModal } from "@/components/workspace/VisualiseModal";

const ease = [0.16, 1, 0.3, 1] as const;

const AI_MODELS = [
  { id: "chemmind-pro", name: "ChemMind Pro", desc: "Best quality" },
  { id: "chemmind-fast", name: "ChemMind Fast", desc: "Quick answers" },
  { id: "gpt-4o", name: "GPT-4o", desc: "OpenAI" },
  { id: "claude-sonnet", name: "Claude Sonnet", desc: "Anthropic" },
  { id: "gemini-pro", name: "Gemini Pro", desc: "Google" },
];

const SAMPLE_FILES = [
  { name: "Molecular Chemistry.pdf", type: "pdf", date: "Today" },
  { name: "VSEPR Theory Notes.tex", type: "tex", date: "Today" },
  { name: "Organic Reactions.pdf", type: "pdf", date: "Yesterday" },
  { name: "Bond Energy Data.csv", type: "csv", date: "Aug 20" },
  { name: "Lab Report Draft.docx", type: "doc", date: "Aug 18" },
];

export default function WorkspacePage() {
  const searchParams = useSearchParams();
  const projectName = searchParams.get("name") || "Untitled Project";
  const projectId = searchParams.get("project") || "unknown";

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [showVisualiser, setShowVisualiser] = useState(false);
  const [selectedModel, setSelectedModel] = useState(AI_MODELS[0]);
  const [modelDropOpen, setModelDropOpen] = useState(false);
  const [files, setFiles] = useState(SAMPLE_FILES);

  // Desktop: default both panels open
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1280px)");
    const update = () => { setSidebarOpen(mq.matches); setAssistantOpen(mq.matches); };
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  // Dynamic margins for desktop
  const isDesktop = typeof window !== "undefined" && window.innerWidth >= 1280;
  const mainStyle: React.CSSProperties = {};

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
              <FileSidebar files={files} setFiles={setFiles} projectName={projectName} onClose={() => setSidebarOpen(false)} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ─── MAIN CONTENT ─── */}
      <main className="workspace-main flex h-full min-h-0 min-w-0 flex-1 flex-col">
        {/* Toolbar */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/60 bg-surface/90 px-3 backdrop-blur-xl sm:px-5">
          <div className="flex min-w-0 items-center gap-3">
            {!sidebarOpen && (
              <ToolbarIcon label="Open navigation" onClick={() => setSidebarOpen(true)}>
                <Menu size={18} />
              </ToolbarIcon>
            )}
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold tracking-[-0.02em]">Introduction to Molecular Chemistry</p>
              <p className="hidden text-[11px] text-muted sm:block">
                <Link href="/projects" className="hover:text-foreground transition-colors">{projectName}</Link>
                <span className="mx-1">·</span>Chapter 1
              </p>
            </div>
          </div>
          <div className="flex items-center gap-0.5">
            <div className="hidden items-center sm:flex">
              <ToolbarIcon label="Previous page"><ChevronLeft size={17} /></ToolbarIcon>
              <span className="px-1 text-xs tabular-nums text-muted">1 / 42</span>
              <ToolbarIcon label="Next page"><ChevronRight size={17} /></ToolbarIcon>
              <span className="mx-2 h-4 w-px bg-border/70" />
              <ToolbarIcon label="Zoom out"><ZoomOut size={16} /></ToolbarIcon>
              <ToolbarIcon label="Zoom in"><ZoomIn size={16} /></ToolbarIcon>
              <ToolbarIcon label="More"><MoreHorizontal size={17} /></ToolbarIcon>
            </div>
            {/* Visualise Button */}
            <button
              onClick={() => setShowVisualiser(true)}
              className="ml-2 hidden items-center gap-2 rounded-full border border-violet-300 bg-violet-50 px-3.5 py-1.5 text-xs font-semibold text-violet-700 transition-all hover:-translate-y-px hover:shadow-md dark:border-violet-700 dark:bg-violet-900/30 dark:text-violet-300 sm:flex"
            >
              <Eye size={14} /> Visualise
            </button>
            <ThemeToggle className="ml-1" />
            {!assistantOpen && (
              <button onClick={() => setAssistantOpen(true)} className="ml-2 flex items-center gap-2 rounded-full bg-foreground px-3 py-1.5 text-xs font-semibold text-background transition-transform hover:-translate-y-px active:translate-y-0">
                <Sparkles size={14} /> <span className="hidden sm:inline">Ask ChemMind</span>
              </button>
            )}
          </div>
        </header>

        {/* Document viewer - LaTeX rendered */}
        <div className="min-h-0 flex-1 overflow-y-auto px-3 py-6 sm:px-7 sm:py-8 lg:px-10">
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
              className="fixed inset-y-0 right-0 z-40 flex w-[352px] flex-col border-l border-border/60 bg-surface shadow-2xl xl:relative xl:z-10 xl:shadow-none"
            >
              <Assistant
                query={query} setQuery={setQuery}
                onClose={() => setAssistantOpen(false)}
                selectedModel={selectedModel}
                setSelectedModel={setSelectedModel}
                modelDropOpen={modelDropOpen}
                setModelDropOpen={setModelDropOpen}
              />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Visualiser Modal */}
      <AnimatePresence>
        {showVisualiser && <VisualiseModal onClose={() => setShowVisualiser(false)} />}
      </AnimatePresence>
    </div>
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
function FileSidebar({ files, setFiles, projectName, onClose }: {
  files: typeof SAMPLE_FILES;
  setFiles: (f: typeof SAMPLE_FILES) => void;
  projectName: string;
  onClose: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = () => fileInputRef.current?.click();
  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploaded = e.target.files;
    if (!uploaded) return;
    const newFiles = Array.from(uploaded).map((f) => ({
      name: f.name,
      type: f.name.split(".").pop() || "file",
      date: "Just now",
    }));
    setFiles([...newFiles, ...files]);
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
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-5">
        <Link href="/projects" className="text-[15px] font-bold tracking-[-0.04em]">CHEMMIND</Link>
        <ToolbarIcon label="Close sidebar" onClick={onClose}><PanelLeftClose size={17} /></ToolbarIcon>
      </div>

      {/* Project badge */}
      <div className="mx-4 mb-3 flex items-center gap-2 rounded-xl border border-border/60 bg-background/60 px-3 py-2.5">
        <div className="flex size-7 items-center justify-center rounded-lg bg-foreground text-background text-[10px] font-bold">
          {projectName.charAt(0)}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-semibold">{projectName}</p>
          <Link href="/projects" className="text-[10px] text-muted hover:text-foreground transition-colors">Switch project →</Link>
        </div>
      </div>

      {/* Upload button */}
      <div className="px-4">
        <input ref={fileInputRef} type="file" multiple accept=".pdf,.tex,.csv,.docx,.doc,.txt,.md" onChange={onFileChange} className="hidden" />
        <button onClick={handleUpload} className="flex w-full items-center justify-center gap-2 rounded-xl bg-foreground px-4 py-2.5 text-sm font-semibold text-background transition-transform hover:-translate-y-px active:translate-y-0">
          <Upload size={16} /> Upload Document
        </button>
      </div>

      {/* Search */}
      <div className="mt-4 px-4">
        <div className="flex items-center gap-2 rounded-xl border border-border/60 bg-background px-3 py-2">
          <Search size={14} className="text-muted" />
          <input type="text" placeholder="Search files..." className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted/60" />
        </div>
      </div>

      {/* File list */}
      <div className="mt-4 flex-1 overflow-y-auto px-3">
        <p className="px-3 text-[10px] font-semibold tracking-[0.14em] text-muted uppercase">Your Documents</p>
        <div className="mt-2 space-y-1">
          {files.map((file, i) => (
            <button key={`${file.name}-${i}`} className={cn(
              "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors",
              i === 0 ? "bg-background text-foreground" : "text-muted hover:bg-background hover:text-foreground"
            )}>
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

      {/* Drop zone */}
      <div className="border-t border-border/60 p-4">
        <div className="upload-zone" onClick={handleUpload}>
          <Upload size={18} className="mx-auto text-muted mb-1" />
          <p className="text-xs text-muted">Drop files here</p>
        </div>
      </div>
    </>
  );
}

/* ─── ASSISTANT PANEL ─── */
function Assistant({ query, setQuery, onClose, selectedModel, setSelectedModel, modelDropOpen, setModelDropOpen }: {
  query: string; setQuery: (v: string) => void; onClose: () => void;
  selectedModel: typeof AI_MODELS[0];
  setSelectedModel: (m: typeof AI_MODELS[0]) => void;
  modelDropOpen: boolean;
  setModelDropOpen: (v: boolean) => void;
}) {
  const suggestions = ["Summarize this section", "Explain this simply", "Find key concepts"];
  const dropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) setModelDropOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [setModelDropOpen]);

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/60 px-5 py-4">
        <div className="flex items-center gap-3">
          <span className="flex size-8 items-center justify-center rounded-full bg-accent text-white shadow-sm"><Sparkles size={15} /></span>
          <div>
            <h2 className="text-sm font-semibold">ChemMind</h2>
            <p className="mt-0.5 text-[11px] text-muted">Grounded in this document</p>
          </div>
        </div>
        <ToolbarIcon label="Close assistant" onClick={onClose}><PanelRightClose size={18} /></ToolbarIcon>
      </div>

      {/* Reading context */}
      <div className="border-b border-border/50 bg-background/45 px-5 py-3">
        <p className="text-[10px] font-semibold tracking-[0.12em] text-muted uppercase">Reading now</p>
        <p className="mt-1 truncate text-xs font-medium">Introduction to Molecular Chemistry</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-5">
        <div className="space-y-5">
          <div className="ml-auto max-w-[84%] rounded-2xl rounded-tr-md bg-foreground px-4 py-3 text-sm leading-6 text-background">
            Can you explain the VSEPR theory simply?
          </div>
          <div className="max-w-[93%] rounded-2xl rounded-tl-md border border-accent/15 bg-accent/7 px-4 py-3.5 text-sm leading-6">
            <p>Absolutely. Think of VSEPR as electrons giving each other space.</p>
            <p className="mt-3 text-muted">
              Because electron pairs carry the same charge, they naturally arrange themselves
              as far apart as possible around the central atom. That spacing creates a molecule&apos;s shape.
            </p>
            <div className="mt-4 flex items-center gap-2 border-t border-accent/15 pt-3 text-[11px] font-medium text-accent">
              <span className="size-1.5 rounded-full bg-accent" /> Based on this page
            </div>
          </div>
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-border/60 bg-background/45 p-4">
        {/* Suggestions */}
        <AnimatePresence initial={false}>
          {!query && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="mb-3 flex gap-2 overflow-x-auto pb-1">
              {suggestions.map((text) => (
                <button key={text} onClick={() => setQuery(text)} className="shrink-0 rounded-full border border-border/70 bg-surface px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:border-accent/40 hover:text-foreground">
                  {text}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Model selector */}
        <div ref={dropRef} className="relative mb-2">
          <button
            onClick={() => setModelDropOpen(!modelDropOpen)}
            className="flex items-center gap-2 rounded-lg border border-border/60 bg-surface px-3 py-1.5 text-[11px] font-medium text-muted transition-colors hover:text-foreground hover:border-border"
          >
            <Sparkles size={12} />
            {selectedModel.name}
            <ChevronDown size={12} className={cn("transition-transform", modelDropOpen && "rotate-180")} />
          </button>
          <AnimatePresence>
            {modelDropOpen && (
              <motion.div
                initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }}
                className="absolute bottom-full left-0 mb-1 w-56 rounded-xl border border-border/60 bg-surface p-1.5 shadow-xl z-50"
              >
                {AI_MODELS.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => { setSelectedModel(m); setModelDropOpen(false); }}
                    className={cn(
                      "flex w-full items-center justify-between rounded-lg px-3 py-2 text-left transition-colors",
                      m.id === selectedModel.id ? "bg-accent/8 text-foreground" : "text-muted hover:bg-background hover:text-foreground"
                    )}
                  >
                    <span className="text-xs font-medium">{m.name}</span>
                    <span className="text-[10px] text-muted/70">{m.desc}</span>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Text input */}
        <div className="rounded-2xl border border-border/70 bg-surface p-2 shadow-sm transition-shadow focus-within:border-accent/60 focus-within:shadow-[0_0_0_3px_rgba(0,102,204,0.1)]">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about this document…"
            rows={2}
            className="block w-full resize-none bg-transparent px-2 py-1 text-sm leading-5 outline-none placeholder:text-muted/80"
          />
          <div className="flex items-center justify-between px-1 pt-1">
            <span className="text-[10px] text-muted">Using {selectedModel.name}</span>
            <button
              aria-label="Send message"
              onClick={() => setQuery("")}
              className={cn(
                "flex size-8 items-center justify-center rounded-full transition-all",
                query ? "bg-foreground text-background hover:scale-105" : "bg-border/40 text-muted"
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
