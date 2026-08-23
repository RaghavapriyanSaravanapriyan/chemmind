"use client";

import { useEffect, useRef } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

function RenderMath({ tex, display = false }: { tex: string; display?: boolean }) {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (ref.current) {
      katex.render(tex, ref.current, { displayMode: display, throwOnError: false });
    }
  }, [tex, display]);
  return <span ref={ref} />;
}

export function LatexDocument() {
  return (
    <div className="latex-doc">
      <p className="text-[11px] font-semibold tracking-[0.14em] text-accent uppercase" style={{ fontFamily: "var(--font-sans)" }}>
        Molecular Chemistry
      </p>
      <h1 style={{ marginTop: "0.5rem" }}>1. Molecular Structure</h1>
      <p className="text-xs text-muted" style={{ fontFamily: "var(--font-sans)", textAlign: "left", marginBottom: "1.5rem" }}>
        ChemMind Study Edition · Chapter 1
      </p>

      <p>
        The physical and chemical properties of a molecule are determined by its three-dimensional
        structure and the specific arrangement of its constituent atoms. Understanding molecular
        geometry is fundamental to predicting how substances interact.
      </p>

      <h2>1.1 VSEPR Theory</h2>
      <p>
        Valence Shell Electron Pair Repulsion (VSEPR) theory provides a model for predicting
        molecular shapes. Electron pairs around a central atom arrange themselves to minimize
        repulsion, creating stable three-dimensional geometries.
      </p>

      <p>The electron pair geometry is defined by:</p>
      <div className="equation-block">
        <RenderMath display tex="\theta_{\min} = \arg\min_{\theta} \sum_{i<j} \frac{1}{|\mathbf{r}_i - \mathbf{r}_j|}" />
        <span className="eq-num">(1.1)</span>
      </div>

      <div className="theorem">
        <div className="theorem-title">Definition 1.1 (Molecular Geometry)</div>
        <p style={{ marginBottom: 0 }}>
          The arrangement of atoms in three-dimensional space, determined by the positions
          of bonding and lone pairs around the central atom.
        </p>
      </div>

      <h3>Common Molecular Geometries</h3>
      <table>
        <thead>
          <tr>
            <th>Geometry</th>
            <th>Bond Angle</th>
            <th>Example</th>
            <th>Formula</th>
          </tr>
        </thead>
        <tbody>
          {[
            ["Linear", "180°", "CO₂", "AX_2"],
            ["Trigonal Planar", "120°", "BF₃", "AX_3"],
            ["Tetrahedral", "109.5°", "CH₄", "AX_4"],
            ["Octahedral", "90°", "SF₆", "AX_6"],
          ].map(([geo, angle, ex, formula]) => (
            <tr key={geo}>
              <td>{geo}</td>
              <td>{angle}</td>
              <td>{ex}</td>
              <td><RenderMath tex={formula!} /></td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>1.2 Chemical Bonding</h2>
      <p>
        Chemical bonds form when atoms share or transfer electrons. The type of bond
        depends on the electronegativity difference between atoms. The bond energy can be
        approximated as:
      </p>
      <div className="equation-block">
        <RenderMath display tex="E_{\text{bond}} = D_e \left[1 - e^{-\beta(r - r_e)}\right]^2" />
        <span className="eq-num">(1.2)</span>
      </div>
      <p>
        where <RenderMath tex="D_e" /> is the dissociation energy, <RenderMath tex="r_e" /> is
        the equilibrium bond length, and <RenderMath tex="\beta" /> is a parameter related to the
        bond stiffness.
      </p>

      <div className="theorem">
        <div className="theorem-title">Theorem 1.1 (Electronegativity Principle)</div>
        <p style={{ marginBottom: 0 }}>
          When <RenderMath tex="\Delta\chi > 1.7" />, the bond is predominantly ionic.
          When <RenderMath tex="\Delta\chi < 0.4" />, the bond is predominantly covalent.
        </p>
      </div>

      <h2>1.3 Orbital Hybridization</h2>
      <p>
        The hybridization of atomic orbitals explains molecular geometry. The wave function
        for an <RenderMath tex="sp^3" /> hybrid orbital is expressed as:
      </p>
      <div className="equation-block">
        <RenderMath display tex="\psi_{sp^3} = \frac{1}{2}(s + p_x + p_y + p_z)" />
        <span className="eq-num">(1.3)</span>
      </div>
      <p>
        These structural considerations extend beyond simple molecules to complex
        macromolecules, influencing biological function in proteins and nucleic acids.
      </p>
    </div>
  );
}
