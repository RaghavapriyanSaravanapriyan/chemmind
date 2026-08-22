"use client";

import { ChevronLeft, ChevronRight, Menu, MoreHorizontal, Sparkles, ZoomIn, ZoomOut } from "lucide-react";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export default function WorkspacePage() {
  return (
    <div className="flex h-[100dvh] overflow-hidden bg-background text-foreground">
      <main className="flex h-full min-h-0 min-w-0 flex-1 flex-col">
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
