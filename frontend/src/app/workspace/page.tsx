"use client";

import { useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { BookOpen, ChevronLeft, ChevronRight, FileText, Menu, MoreHorizontal, PanelLeftClose, Plus, Search, Sparkles, ZoomIn, ZoomOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/ui/theme-toggle";

const ease = [0.16, 1, 0.3, 1] as const;

export default function WorkspacePage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-background text-foreground">
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div onClick={() => setSidebarOpen(false)} className="fixed inset-0 z-30 bg-foreground/20 backdrop-blur-[1px] xl:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />
            <motion.aside initial={{ x: -256, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: -256, opacity: 0 }} transition={{ duration: 0.35, ease }} className="fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border/60 bg-surface shadow-2xl xl:relative xl:z-10 xl:shadow-none">
              <Sidebar onClose={() => setSidebarOpen(false)} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <main className="flex h-full min-h-0 min-w-0 flex-1 flex-col xl:mr-[352px]">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/60 bg-surface/90 px-3 backdrop-blur-xl sm:px-5">
          <div className="flex min-w-0 items-center gap-3">
            <ToolbarIcon label="Open navigation">
              <Menu size={18} />
            </ToolbarIcon>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold tracking-[-0.02em]">Introduction to Molecular Chemistry</p>
              <p className="hidden text-[11px] text-muted sm:block">Chapter 1 · Molecular structure</p>
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
              <ToolbarIcon label="More options"><MoreHorizontal size={17} /></ToolbarIcon>
            </div>
            <ThemeToggle className="ml-1" />
            <button className="ml-2 flex items-center gap-2 rounded-full bg-foreground px-3 py-1.5 text-xs font-semibold text-background transition-transform hover:-translate-y-px active:translate-y-0">
              <Sparkles size={14} /> <span className="hidden sm:inline">Ask ChemMind</span>
            </button>
          </div>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto px-3 py-6 sm:px-7 sm:py-8 lg:px-10">
          <article className="mx-auto w-full max-w-[48rem] rounded-[18px] border border-border/60 bg-surface px-6 py-8 shadow-[0_10px_30px_rgba(29,29,31,0.05)] sm:rounded-[22px] sm:px-11 sm:py-10">
            <Document />
          </article>
        </div>
      </main>
    </div>
  );
}

function Document() {
  return (
    <div className="mx-auto max-w-[39rem]">
      <div className="flex items-center justify-between border-b border-border/50 pb-5">
        <div>
          <p className="text-[11px] font-semibold tracking-[0.14em] text-accent uppercase">Molecular chemistry</p>
          <p className="mt-1 text-xs text-muted">ChemMind study edition</p>
        </div>
        <span className="text-xs tabular-nums text-muted">01</span>
      </div>
      <h1 className="mt-8 text-3xl font-bold tracking-[-0.045em] sm:text-4xl">Molecular Structure</h1>
      <p className="mt-5 text-[1.02rem] leading-8 text-muted">The physical and chemical properties of a molecule are determined by its three-dimensional structure and the specific arrangement of its constituent atoms. Understanding molecular geometry is fundamental to predicting how substances interact.</p>
      <div className="my-8 h-px bg-border/50" />
      <h2 className="text-2xl font-semibold tracking-[-0.035em]">VSEPR Theory</h2>
      <p className="mt-4 text-[1.02rem] leading-8 text-muted">Valence Shell Electron Pair Repulsion theory provides a simple model for predicting molecular shapes. Electron pairs around a central atom arrange themselves to minimize repulsion, creating stable three-dimensional geometries.</p>
      <div className="my-7 grid gap-3 sm:grid-cols-2">
        {[["Linear", "180°"], ["Trigonal planar", "120°"], ["Tetrahedral", "109.5°"], ["Octahedral", "90°"]].map(([shape, angle]) => (
          <div key={shape} className="flex items-center justify-between rounded-xl border border-border/60 bg-background/55 px-4 py-3">
            <span className="text-sm font-medium">{shape}</span>
            <span className="text-xs font-semibold text-accent">{angle}</span>
          </div>
        ))}
      </div>
      <figure className="mt-8 overflow-hidden rounded-2xl border border-border/60 bg-background/55 p-6 sm:p-7">
        <div className="flex h-28 items-center justify-center">
          <div className="relative size-20">
            <span className="absolute left-1/2 top-1/2 size-9 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent shadow-[0_0_0_10px_rgba(0,102,204,0.08)]" />
            <i className="absolute left-1/2 top-0 size-4 -translate-x-1/2 rounded-full bg-foreground/60" />
            <i className="absolute bottom-0 left-1/2 size-4 -translate-x-1/2 rounded-full bg-foreground/60" />
            <i className="absolute left-0 top-1/2 size-4 -translate-y-1/2 rounded-full bg-foreground/60" />
            <i className="absolute right-0 top-1/2 size-4 -translate-y-1/2 rounded-full bg-foreground/60" />
          </div>
        </div>
        <figcaption className="mt-4 text-center text-xs leading-5 text-muted">Figure 1.1 · Electron-pair arrangements determine molecular geometry.</figcaption>
      </figure>
      <p className="mt-8 text-[1.02rem] leading-8 text-muted">These structural considerations extend beyond simple molecules to complex macromolecules, influencing biological function in proteins and nucleic acids.</p>
    </div>
  );
}

function ToolbarIcon({ children, label, onClick }: { children: React.ReactNode; label: string; onClick?: () => void }) {
  return (
    <button type="button" onClick={onClick} aria-label={label} className="flex size-8 items-center justify-center rounded-lg text-muted transition-colors hover:bg-background hover:text-foreground">
      {children}
    </button>
  );
}

function Sidebar({ onClose }: { onClose: () => void }) { return <><div className="flex items-center justify-between px-5 py-5"><Link href="/" className="text-[15px] font-bold tracking-[-0.04em]">CHEMMIND</Link><ToolbarIcon label="Close navigation" onClick={onClose}><PanelLeftClose size={17}/></ToolbarIcon></div><div className="px-4"><button className="flex w-full items-center justify-center gap-2 rounded-xl bg-foreground px-4 py-2.5 text-sm font-semibold text-background transition-transform hover:-translate-y-px active:translate-y-0"><Plus size={16}/> New conversation</button></div><nav className="mt-6 px-3"><p className="px-3 text-[10px] font-semibold tracking-[0.14em] text-muted uppercase">Workspace</p><div className="mt-2 space-y-1"><NavItem active icon={<Sparkles size={16}/>} label="Home"/><NavItem icon={<FileText size={16}/>} label="Documents"/><NavItem icon={<Search size={16}/>} label="Search"/></div></nav><div className="mt-7 flex-1 overflow-y-auto px-3"><p className="px-3 text-[10px] font-semibold tracking-[0.14em] text-muted uppercase">Recent conversations</p><div className="mt-2 space-y-1"><Conversation label="Organic chemistry" active/><Conversation label="Physics notes"/><Conversation label="Exam preparation"/><Conversation label="Research paper"/></div></div><div className="border-t border-border/60 p-4"><Link href="/" className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-muted transition-colors hover:bg-background hover:text-foreground"><BookOpen size={16}/> Return to ChemMind</Link></div></>; }
function NavItem({ icon, label, active = false }: { icon: React.ReactNode; label: string; active?: boolean }) { return <button className={cn("flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors", active ? "bg-background text-foreground" : "text-muted hover:bg-background hover:text-foreground")}>{icon}{label}</button>; }
function Conversation({ label, active = false }: { label: string; active?: boolean }) { return <button className={cn("w-full truncate rounded-lg px-3 py-2 text-left text-sm transition-colors", active ? "bg-accent/8 font-medium text-foreground" : "text-muted hover:bg-background hover:text-foreground")}>{label}</button>; }
