"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X, Loader2, RotateCcw, Download } from "lucide-react";

export function VisualiseModal({ onClose }: { onClose: () => void }) {
  const [prompt, setPrompt] = useState("CH4 methane molecule tetrahedral geometry");
  const [loading, setLoading] = useState(false);
  const [generated, setGenerated] = useState(false);

  const handleGenerate = () => {
    setLoading(true);
    setTimeout(() => { setLoading(false); setGenerated(true); }, 2500);
  };

  return (
    <motion.div className="visualise-modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
      <motion.div className="visualise-modal" initial={{ scale: 0.92, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.92, opacity: 0 }} transition={{ duration: 0.3 }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-border/60 px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="flex size-8 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 text-white text-xs font-bold">3D</span>
            <div>
              <h3 className="text-sm font-semibold">AI 3D Visualiser</h3>
              <p className="text-[11px] text-muted">Generate molecular structures</p>
            </div>
          </div>
          <button onClick={onClose} className="flex size-8 items-center justify-center rounded-lg text-muted hover:bg-background hover:text-foreground transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="p-6">
          <label className="text-xs font-semibold text-muted mb-2 block">Describe the molecule or structure</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={2}
            className="w-full rounded-xl border border-border/70 bg-background px-4 py-3 text-sm outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-400/20 resize-none"
            placeholder="e.g. Water molecule H2O, benzene ring..."
          />

          <button
            onClick={handleGenerate}
            disabled={loading || !prompt.trim()}
            className="mt-3 w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-5 py-3 text-sm font-semibold text-white transition-all hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <><Loader2 size={16} className="animate-spin" /> Generating...</> : "Generate 3D Model"}
          </button>

          {/* Preview area */}
          <div className="mt-5 rounded-2xl border border-border/60 bg-background overflow-hidden">
            <div className="flex h-[280px] items-center justify-center relative">
              {!generated && !loading && (
                <div className="text-center">
                  <div className="mx-auto mb-3 flex size-16 items-center justify-center rounded-2xl bg-violet-50 text-violet-500 dark:bg-violet-900/30 dark:text-violet-400">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/></svg>
                  </div>
                  <p className="text-sm text-muted">Enter a prompt and generate</p>
                </div>
              )}
              {loading && (
                <div className="text-center">
                  <Loader2 size={32} className="mx-auto animate-spin text-violet-500 mb-3" />
                  <p className="text-sm text-muted">Creating 3D model...</p>
                </div>
              )}
              {generated && !loading && (
                <>
                  {/* Simulated 3D molecule preview */}
                  <div className="relative w-full h-full flex items-center justify-center">
                    <div className="relative" style={{ perspective: "600px" }}>
                      <motion.div animate={{ rotateY: 360 }} transition={{ duration: 8, repeat: Infinity, ease: "linear" }} style={{ transformStyle: "preserve-3d" }} className="relative size-32">
                        {/* Central atom */}
                        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 size-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 shadow-lg shadow-blue-500/30" />
                        {/* Surrounding atoms */}
                        <div className="absolute left-1/2 top-0 -translate-x-1/2 size-6 rounded-full bg-gradient-to-br from-gray-200 to-gray-400 shadow-md" />
                        <div className="absolute left-1/2 bottom-0 -translate-x-1/2 size-6 rounded-full bg-gradient-to-br from-gray-200 to-gray-400 shadow-md" />
                        <div className="absolute top-1/2 left-0 -translate-y-1/2 size-6 rounded-full bg-gradient-to-br from-gray-200 to-gray-400 shadow-md" />
                        <div className="absolute top-1/2 right-0 -translate-y-1/2 size-6 rounded-full bg-gradient-to-br from-gray-200 to-gray-400 shadow-md" />
                        {/* Bonds */}
                        <div className="absolute left-1/2 top-[15%] w-0.5 h-[22%] bg-foreground/30 -translate-x-1/2" />
                        <div className="absolute left-1/2 bottom-[15%] w-0.5 h-[22%] bg-foreground/30 -translate-x-1/2" />
                        <div className="absolute top-1/2 left-[15%] h-0.5 w-[22%] bg-foreground/30 -translate-y-1/2" />
                        <div className="absolute top-1/2 right-[15%] h-0.5 w-[22%] bg-foreground/30 -translate-y-1/2" />
                      </motion.div>
                    </div>
                    <div className="absolute bottom-3 left-3 text-[10px] text-muted bg-surface/80 px-2 py-1 rounded-md backdrop-blur">
                      Drag to rotate · Scroll to zoom
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {generated && (
            <div className="mt-3 flex gap-2">
              <button onClick={() => { setGenerated(false); }} className="flex-1 flex items-center justify-center gap-2 rounded-xl border border-border/70 px-4 py-2.5 text-xs font-medium text-muted hover:text-foreground hover:border-border transition-colors">
                <RotateCcw size={14} /> Regenerate
              </button>
              <button className="flex-1 flex items-center justify-center gap-2 rounded-xl border border-border/70 px-4 py-2.5 text-xs font-medium text-muted hover:text-foreground hover:border-border transition-colors">
                <Download size={14} /> Export
              </button>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}
