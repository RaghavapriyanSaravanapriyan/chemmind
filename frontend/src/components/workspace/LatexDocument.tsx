"use client";

import React, { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import { FileText, Upload } from "lucide-react";

interface LatexDocumentProps {
  content?: string;
  title?: string;
  subtitle?: string;
}

function LatexParser({ content }: { content: string }) {
  return useMemo(() => {
    const blocks = content.split('\n\n');
    return blocks.map((block, i) => {
      block = block.trim();
      if (!block) return null;

      // Parse headings
      if (block.startsWith('\\section{')) {
        const title = block.match(/\\section{(.*?)}/)?.[1] || "";
        return <h1 key={i} className="text-3xl font-bold tracking-[-0.045em] sm:text-4xl mt-8 mb-5 text-foreground">{title}</h1>;
      }
      if (block.startsWith('\\subsection{')) {
        const title = block.match(/\\subsection{(.*?)}/)?.[1] || "";
        return <h2 key={i} className="text-2xl font-semibold tracking-[-0.035em] mt-8 mb-4 border-b border-border/50 pb-2 text-foreground">{title}</h2>;
      }
      
      // Parse block math
      if (block.startsWith('$$') && block.endsWith('$$')) {
        const math = block.slice(2, -2);
        const html = katex.renderToString(math, { displayMode: true, throwOnError: false });
        return <div key={i} className="my-6 overflow-x-auto rounded-xl bg-background/50 p-4 border border-border/50" dangerouslySetInnerHTML={{ __html: html }} />;
      }

      // Parse text with inline math and bold
      let html = block;
      
      // bold
      html = html.replace(/\\textbf{(.*?)}/g, '<strong class="font-semibold text-foreground">$1</strong>');
      // line breaks
      html = html.replace(/\\\\/g, '<br/>');
      
      // inline math
      html = html.replace(/\$([^\$]+)\$/g, (match, math) => {
        try {
          return katex.renderToString(math, { displayMode: false, throwOnError: false });
        } catch (e) {
          return match;
        }
      });

      return <p key={i} className="mt-4 text-[1.02rem] leading-8 text-muted" dangerouslySetInnerHTML={{ __html: html }} />;
    });
  }, [content]);
}

function EmptyDocumentState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="flex size-20 items-center justify-center rounded-2xl bg-surface border border-border/60">
        <FileText size={36} className="text-muted" />
      </div>
      <h2 className="mt-6 text-xl font-bold tracking-[-0.03em]">No Document Selected</h2>
      <p className="mt-2 max-w-sm text-sm text-muted leading-6">
        Upload a document from the sidebar to view it here, or use the AI assistant to explore chemistry topics.
      </p>
      <div className="mt-6 flex items-center gap-2 rounded-xl border border-dashed border-border/80 bg-background/50 px-5 py-3">
        <Upload size={16} className="text-muted" />
        <span className="text-xs text-muted">Upload .pdf, .tex, .csv, .md files</span>
      </div>
    </div>
  );
}

export function LatexDocument({ content, title, subtitle }: LatexDocumentProps) {
  if (!content) {
    return (
      <div className="latex-doc" style={{ fontFamily: "var(--font-sans)" }}>
        <EmptyDocumentState />
      </div>
    );
  }

  return (
    <div className="latex-doc" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center justify-between border-b border-border/50 pb-5">
        <div>
          <p className="text-[11px] font-semibold tracking-[0.14em] text-accent uppercase">{title || "Document"}</p>
          <p className="mt-1 text-xs text-muted">{subtitle || "ChemMind study edition"}</p>
        </div>
      </div>
      
      <div className="mt-2">
        <LatexParser content={content} />
      </div>
    </div>
  );
}
