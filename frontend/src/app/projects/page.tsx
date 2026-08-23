"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus, Search, Clock, FileText, MoreHorizontal, Trash2, Edit3,
  FolderOpen, ArrowUpRight, Sparkles, X, ChevronRight, Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { fetchWorkspaces, createWorkspace, deleteWorkspace, Workspace } from "@/lib/api";

const ease = [0.16, 1, 0.3, 1] as const;

interface DisplayProject {
  id: string;
  name: string;
  description: string;
  docs: number;
  lastOpened: string;
  color: string;
}

const INITIAL_PROJECTS: DisplayProject[] = [
  { id: "mol-chem", name: "Molecular Chemistry", description: "VSEPR theory, bonding, and molecular geometry", docs: 5, lastOpened: "Just now", color: "from-blue-500 to-indigo-600" },
  { id: "org-chem", name: "Organic Reactions", description: "Reaction mechanisms and synthesis pathways", docs: 3, lastOpened: "2 hours ago", color: "from-emerald-500 to-teal-600" },
  { id: "quantum", name: "Quantum Mechanics", description: "Wave functions, operators, and quantum states", docs: 8, lastOpened: "Yesterday", color: "from-violet-500 to-purple-600" },
  { id: "thermo", name: "Thermodynamics", description: "Laws of thermodynamics and statistical mechanics", docs: 4, lastOpened: "3 days ago", color: "from-amber-500 to-orange-600" },
];

const COLOR_OPTIONS = [
  "from-blue-500 to-indigo-600",
  "from-emerald-500 to-teal-600",
  "from-violet-500 to-purple-600",
  "from-amber-500 to-orange-600",
  "from-rose-500 to-pink-600",
  "from-cyan-500 to-sky-600",
];

export default function ProjectsPage() {
  const [projects, setProjects] = useState<DisplayProject[]>(INITIAL_PROJECTS);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newColor, setNewColor] = useState(COLOR_OPTIONS[0]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadBackendWorkspaces() {
      const backendWs = await fetchWorkspaces();
      if (backendWs && backendWs.length > 0) {
        const formatted = backendWs.map((ws: Workspace, idx: number) => ({
          id: ws.id,
          name: ws.name,
          description: ws.description || "Active study workspace",
          docs: 3,
          lastOpened: "Recently",
          color: COLOR_OPTIONS[idx % COLOR_OPTIONS.length],
        }));
        setProjects(formatted);
      }
    }
    loadBackendWorkspaces();
  }, []);

  const filtered = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.description.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setLoading(true);
    const created = await createWorkspace(newName.trim(), newDesc.trim() || "Workspace for research");
    const id = created ? created.id : newName.toLowerCase().replace(/\s+/g, "-") + "-" + Date.now();

    setProjects([
      {
        id,
        name: newName.trim(),
        description: newDesc.trim() || "Study workspace for scientific research",
        docs: 0,
        lastOpened: "Just now",
        color: newColor,
      },
      ...projects,
    ]);

    setNewName("");
    setNewDesc("");
    setNewColor(COLOR_OPTIONS[0]);
    setShowCreate(false);
    setLoading(false);
  };

  const handleDelete = async (id: string) => {
    await deleteWorkspace(id);
    setProjects(projects.filter((p) => p.id !== id));
    setMenuOpenId(null);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Top Bar */}
      <header className="sticky top-0 z-30 border-b border-border/50 bg-background/80 backdrop-blur-2xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <Link href="/" className="group flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-foreground text-background transition-transform duration-300 group-hover:scale-105">
              <span className="text-sm font-bold">C</span>
            </div>
            <span className="text-[15px] font-semibold tracking-[-0.02em]">ChemMind</span>
          </Link>
          <div className="flex items-center gap-3">
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main Section */}
      <main className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease }}>
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-muted">Your workspace hub</p>
          <h1 className="mt-2 text-3xl font-bold tracking-[-0.04em] sm:text-4xl">Research Workspaces</h1>
          <p className="mt-2 text-base text-muted">Manage your documents, Agentic RAG chat, and 3D molecular models.</p>
        </motion.div>

        {/* Toolbar */}
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease, delay: 0.1 }}
          className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="flex items-center gap-2 rounded-xl border border-border/60 bg-surface px-4 py-2.5 shadow-sm transition-shadow focus-within:border-accent/50 focus-within:shadow-[0_0_0_3px_rgba(0,102,204,0.08)] sm:w-80">
            <Search size={16} className="text-muted" />
            <input
              value={search} onChange={(e) => setSearch(e.target.value)}
              type="text" placeholder="Search projects..."
              className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted/60"
            />
          </div>

          <button
            onClick={() => setShowCreate(true)}
            className="group inline-flex items-center justify-center gap-2 rounded-xl bg-foreground px-5 py-2.5 text-sm font-semibold text-background shadow-md transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg active:translate-y-0"
          >
            <Plus size={16} />
            New Workspace
          </button>
        </motion.div>

        {/* Project Grid */}
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <AnimatePresence mode="popLayout">
            {filtered.map((project, i) => (
              <motion.div
                key={project.id}
                layout
                initial={{ opacity: 0, y: 24, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.5, ease, delay: i * 0.04 }}
              >
                <ProjectCard
                  project={project}
                  menuOpen={menuOpenId === project.id}
                  onMenuToggle={() => setMenuOpenId(menuOpenId === project.id ? null : project.id)}
                  onDelete={() => handleDelete(project.id)}
                />
              </motion.div>
            ))}
          </AnimatePresence>

          {filtered.length === 0 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="col-span-full flex flex-col items-center py-20 text-center">
              <div className="flex size-16 items-center justify-center rounded-2xl bg-surface border border-border/60">
                <FolderOpen size={28} className="text-muted" />
              </div>
              <p className="mt-5 text-lg font-semibold">No workspaces found</p>
              <p className="mt-1 text-sm text-muted">
                {search ? "Try a different search query." : "Create a new workspace to start studying."}
              </p>
              {!search && (
                <button onClick={() => setShowCreate(true)} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-foreground px-5 py-2.5 text-sm font-semibold text-background">
                  <Plus size={16} /> New Workspace
                </button>
              )}
            </motion.div>
          )}
        </div>
      </main>

      {/* Create Modal */}
      <AnimatePresence>
        {showCreate && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/20 backdrop-blur-sm"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setShowCreate(false)}
          >
            <motion.div
              className="w-[min(90vw,480px)] rounded-2xl border border-border/60 bg-surface p-6 shadow-2xl sm:p-8"
              initial={{ scale: 0.93, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.93, opacity: 0 }}
              transition={{ duration: 0.3, ease }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold tracking-[-0.03em]">Create Research Workspace</h2>
                  <p className="mt-1 text-sm text-muted">Set up your workspace for paper ingestion & AI synthesis.</p>
                </div>
                <button onClick={() => setShowCreate(false)} className="flex size-8 items-center justify-center rounded-lg text-muted hover:bg-background transition-colors">
                  <X size={18} />
                </button>
              </div>

              <label className="text-xs font-semibold text-muted block mb-1.5">Workspace Name</label>
              <input
                value={newName} onChange={(e) => setNewName(e.target.value)}
                type="text" placeholder="e.g. Molecular Kinetics Research"
                autoFocus
                className="w-full rounded-xl border border-border/70 bg-background px-4 py-3 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/10"
              />

              <label className="text-xs font-semibold text-muted block mb-1.5 mt-4">Description</label>
              <textarea
                value={newDesc} onChange={(e) => setNewDesc(e.target.value)}
                rows={2} placeholder="Target research scope..."
                className="w-full rounded-xl border border-border/70 bg-background px-4 py-3 text-sm outline-none resize-none focus:border-accent/50 focus:ring-2 focus:ring-accent/10"
              />

              <div className="mt-7 flex gap-3">
                <button onClick={() => setShowCreate(false)} className="flex-1 rounded-xl border border-border/70 px-4 py-3 text-sm font-medium text-muted hover:text-foreground">
                  Cancel
                </button>
                <button
                  onClick={handleCreate}
                  disabled={!newName.trim() || loading}
                  className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-foreground px-4 py-3 text-sm font-semibold text-background transition-all hover:-translate-y-px hover:shadow-lg disabled:opacity-40"
                >
                  {loading ? <Loader2 size={16} className="animate-spin" /> : "Create Workspace"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ProjectCard({ project, menuOpen, onMenuToggle, onDelete }: {
  project: DisplayProject; menuOpen: boolean; onMenuToggle: () => void; onDelete: () => void;
}) {
  return (
    <div className="group relative rounded-2xl border border-border/50 bg-surface transition-all duration-400 hover:-translate-y-1 hover:border-border hover:shadow-xl">
      <div className={cn("h-1.5 rounded-t-2xl bg-gradient-to-r", project.color)} />

      <div className="p-5 sm:p-6">
        <div className="flex items-start justify-between">
          <div className={cn("flex size-10 items-center justify-center rounded-xl bg-gradient-to-br text-white text-sm font-bold shadow-sm", project.color)}>
            {project.name.charAt(0)}
          </div>

          <div className="relative">
            <button onClick={onMenuToggle} className="flex size-8 items-center justify-center rounded-lg text-muted opacity-0 transition-all group-hover:opacity-100 hover:bg-background hover:text-foreground">
              <MoreHorizontal size={16} />
            </button>
            <AnimatePresence>
              {menuOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 4, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 4, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-full z-20 mt-1 w-40 rounded-xl border border-border/60 bg-surface p-1.5 shadow-xl"
                >
                  <button onClick={onDelete} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
                    <Trash2 size={13} /> Delete Workspace
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        <h3 className="mt-4 text-base font-semibold tracking-[-0.02em]">{project.name}</h3>
        <p className="mt-1 text-sm text-muted line-clamp-2">{project.description}</p>

        <div className="mt-5 flex items-center justify-between">
          <div className="flex items-center gap-4 text-xs text-muted">
            <span className="flex items-center gap-1.5"><FileText size={13} /> {project.docs} docs</span>
            <span className="flex items-center gap-1.5"><Clock size={13} /> {project.lastOpened}</span>
          </div>
        </div>

        <Link
          href={`/workspace?project=${encodeURIComponent(project.id)}&name=${encodeURIComponent(project.name)}`}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-border/60 bg-background/60 px-4 py-2.5 text-sm font-medium text-foreground transition-all hover:bg-foreground hover:text-background hover:shadow-md"
        >
          Open Workspace <ArrowUpRight size={14} />
        </Link>
      </div>
    </div>
  );
}
