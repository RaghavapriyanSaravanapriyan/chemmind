"use client";

import React, { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

const RAW_LATEX_DOCUMENT = `
\\section{1. Molecular Structure}

The physical and chemical properties of a molecule are determined by its three-dimensional structure and the specific arrangement of its constituent atoms. Understanding molecular geometry is fundamental to predicting how substances interact.

\\subsection{1.1 VSEPR Theory}

Valence Shell Electron Pair Repulsion (VSEPR) theory provides a model for predicting molecular shapes. Electron pairs around a central atom arrange themselves to minimize repulsion, creating stable three-dimensional geometries.

The electron pair geometry is defined by:

$$ \\theta_{\\min} = \\arg\\min_{\\theta} \\sum_{i<j} \\frac{1}{|\\mathbf{r}_i - \\mathbf{r}_j|} $$

\\textbf{Definition 1.1 (Molecular Geometry)}\\\\
The arrangement of atoms in three-dimensional space, determined by the positions of bonding and lone pairs around the central atom.

\\subsection{1.2 Chemical Bonding}

Chemical bonds form when atoms share or transfer electrons. The type of bond depends on the electronegativity difference between atoms. The bond energy can be approximated as:

$$ E_{\\text{bond}} = D_e \\left[1 - e^{-\\beta(r - r_e)}\\right]^2 $$

where $D_e$ is the dissociation energy, $r_e$ is the equilibrium bond length, and $\\beta$ is a parameter related to the bond stiffness.

\\textbf{Theorem 1.1 (Electronegativity Principle)}\\\\
When $\\Delta\\chi > 1.7$, the bond is predominantly ionic. When $\\Delta\\chi < 0.4$, the bond is predominantly covalent.

\\subsection{1.3 Orbital Hybridization}

The hybridization of atomic orbitals explains molecular geometry. The wave function for an $sp^3$ hybrid orbital is expressed as:

$$ \\psi_{sp^3} = \\frac{1}{2}(s + p_x + p_y + p_z) $$

These structural considerations extend beyond simple molecules to complex macromolecules, influencing biological function in proteins and nucleic acids.
`;

function LatexParser({ content }: { content: string }) {
  return useMemo(() => {
    // Basic parser to satisfy the full LaTeX document requirement
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

export function LatexDocument() {
  return (
    <div className="latex-doc" style={{ fontFamily: "var(--font-sans)" }}>
      <div className="flex items-center justify-between border-b border-border/50 pb-5">
        <div>
          <p className="text-[11px] font-semibold tracking-[0.14em] text-accent uppercase">Molecular chemistry</p>
          <p className="mt-1 text-xs text-muted">ChemMind study edition</p>
        </div>
        <span className="text-xs tabular-nums text-muted">01</span>
      </div>
      
      <div className="mt-2">
        <LatexParser content={RAW_LATEX_DOCUMENT} />
      </div>
    </div>
  );
}
