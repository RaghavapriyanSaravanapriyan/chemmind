import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border/50 bg-background">
      {/* Large brand display */}
      <div className="mx-auto max-w-7xl px-6 pt-20 pb-8 sm:px-8 lg:px-12">
        <div className="flex items-center justify-center pb-16">
          <p className="heading-serif text-[clamp(3rem,10vw,8rem)] leading-none text-foreground/[0.06] select-none">
            ChemMind
          </p>
        </div>

        <div className="flex flex-col gap-10 md:flex-row md:justify-between">
          <div>
            <Link href="/" className="group flex items-center gap-2.5">
              <div className="flex size-7 items-center justify-center rounded-md bg-foreground text-background">
                <span className="text-xs font-bold">C</span>
              </div>
              <span className="text-sm font-semibold tracking-[-0.02em]">ChemMind</span>
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-6 text-muted">
              A calmer place to read, reason, and understand your material.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-x-16 gap-y-8 sm:grid-cols-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">Product</p>
              <ul className="mt-4 space-y-3">
                <li><Link href="#features" className="text-sm text-foreground/70 transition-colors hover:text-foreground">Features</Link></li>
                <li><Link href="/workspace" className="text-sm text-foreground/70 transition-colors hover:text-foreground">Workspace</Link></li>
                <li><Link href="#how-it-works" className="text-sm text-foreground/70 transition-colors hover:text-foreground">How it works</Link></li>
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">Resources</p>
              <ul className="mt-4 space-y-3">
                <li><span className="text-sm text-foreground/40 cursor-default">Documentation</span></li>
                <li><span className="text-sm text-foreground/40 cursor-default">Changelog</span></li>
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">Legal</p>
              <ul className="mt-4 space-y-3">
                <li><span className="text-sm text-foreground/40 cursor-default">Privacy</span></li>
                <li><span className="text-sm text-foreground/40 cursor-default">Terms</span></li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-border/50 pt-6 sm:flex-row">
          <p className="text-xs text-muted">© 2026 ChemMind. All rights reserved.</p>
          <p className="text-xs text-muted/60">Built for learners, by learners.</p>
        </div>
      </div>
    </footer>
  );
}
