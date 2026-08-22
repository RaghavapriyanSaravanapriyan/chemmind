"use client";

import { useRef } from "react";
import Link from "next/link";
import { motion, useScroll, useTransform, useInView } from "framer-motion";
import { ArrowUpRight, FileText, Sparkles, BookOpen, Brain, MessageSquare } from "lucide-react";
import { Footer } from "@/components/layout/Footer";
import { Navbar } from "@/components/layout/Navbar";

const ease = [0.16, 1, 0.3, 1] as const;

function Reveal({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 40 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.9, ease, delay }} className={className}>
      {children}
    </motion.div>
  );
}

export default function LandingPage() {
  const heroRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const heroOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 0.5], [1, 0.96]);
  const mockupY = useTransform(scrollYProgress, [0, 0.6], [0, -60]);

  return (
    <div className="min-h-screen overflow-x-clip bg-background selection:bg-foreground/10">
      <Navbar />
      <main>
        {/* ─── HERO ─── */}
        <section ref={heroRef} className="relative flex min-h-[100svh] flex-col items-center justify-center px-5 pt-28 pb-20 sm:px-8">
          <motion.div style={{ opacity: heroOpacity, scale: heroScale }} className="mx-auto max-w-4xl text-center">
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease, delay: 0.1 }}>
              <span className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-surface px-4 py-1.5 text-xs font-medium text-muted shadow-sm">
                <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Now in public beta
              </span>
            </motion.div>

            <motion.h1 initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1, ease, delay: 0.2 }} className="mt-8 text-[clamp(2.8rem,7vw,6rem)] font-bold leading-[0.95] tracking-[-0.04em]">
              Think smarter.
              <br />
              <span className="heading-serif text-muted">Learn deeper.</span>
            </motion.h1>

            <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, ease, delay: 0.4 }} className="mx-auto mt-7 max-w-xl text-pretty text-lg leading-7 text-muted sm:text-xl sm:leading-8">
              Your reading, research, and reasoning — together in one calm, intelligent workspace.
            </motion.p>

            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease, delay: 0.55 }} className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link href="/workspace" className="group inline-flex items-center gap-2 rounded-full bg-foreground px-7 py-3.5 text-sm font-semibold text-background shadow-[0_8px_30px_rgba(0,0,0,0.12)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_12px_40px_rgba(0,0,0,0.18)] active:translate-y-0">
                Open workspace
                <ArrowUpRight className="size-4 transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
              </Link>
              <Link href="#features" className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-surface/80 px-7 py-3.5 text-sm font-medium text-foreground shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-border hover:shadow-md">
                Explore features
              </Link>
            </motion.div>
          </motion.div>

          {/* Workspace mockup */}
          <motion.div style={{ y: mockupY }} initial={{ opacity: 0, y: 60 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1.2, ease, delay: 0.6 }} className="relative mx-auto mt-16 w-full max-w-[1100px] px-2 sm:mt-20">
            <div className="mockup-glow rounded-2xl sm:rounded-3xl">
              <WorkspacePreview />
            </div>
          </motion.div>
        </section>

        {/* ─── MARQUEE ─── */}
        <section className="overflow-hidden py-5">
          <div className="animate-marquee flex whitespace-nowrap">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="flex shrink-0 items-center gap-12 px-6">
                {["Document reader", "AI assistant", "Knowledge graphs", "Molecular structures", "Research papers", "Study notes", "VSEPR theory", "Chemical bonds"].map((t) => (
                  <span key={`${i}-${t}`} className="text-sm font-medium text-muted/50">{t}</span>
                ))}
              </div>
            ))}
          </div>
        </section>

        {/* ─── FEATURES ─── */}
        <section id="features" className="py-24 sm:py-32 lg:py-40">
          <div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-12">
            <Reveal>
              <div className="mx-auto max-w-2xl text-center">
                <p className="text-xs font-semibold uppercase tracking-[0.15em] text-muted">Features</p>
                <h2 className="mt-4 text-4xl font-bold tracking-[-0.035em] sm:text-5xl lg:text-6xl">
                  Everything you need,
                  <br />
                  <span className="heading-serif text-muted">nothing you don&apos;t.</span>
                </h2>
              </div>
            </Reveal>

            <div className="mt-20 grid gap-6 lg:grid-cols-3">
              {[
                { icon: BookOpen, title: "Focused reading", desc: "Your documents get the room they need. A distraction-free reader that keeps the material front and center.", color: "bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400" },
                { icon: Brain, title: "AI that understands context", desc: "Ask questions grounded in what you're reading. Get explanations, summaries, and insights — all document-aware.", color: "bg-violet-50 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400" },
                { icon: MessageSquare, title: "Natural conversations", desc: "Talk to your documents naturally. Follow-up questions, deeper dives, simpler explanations — just ask.", color: "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" },
              ].map((f, i) => (
                <Reveal key={f.title} delay={i * 0.1}>
                  <div className="group relative rounded-2xl border border-border/50 bg-surface p-8 transition-all duration-500 hover:-translate-y-1 hover:border-border hover:shadow-[0_20px_60px_-15px_rgba(0,0,0,0.08)]">
                    <div className={`inline-flex size-12 items-center justify-center rounded-xl ${f.color} transition-transform duration-300 group-hover:scale-110`}>
                      <f.icon size={22} />
                    </div>
                    <h3 className="mt-6 text-lg font-semibold tracking-[-0.02em]">{f.title}</h3>
                    <p className="mt-3 text-sm leading-6 text-muted">{f.desc}</p>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* ─── FEATURE STORIES ─── */}
        <section className="py-24 sm:py-32 lg:py-40">
          <div className="mx-auto max-w-7xl space-y-28 px-5 sm:px-8 lg:space-y-40 lg:px-12">
            <FeatureStory eyebrow="Your workspace, in context" title="Every source. One uninterrupted flow." body="Keep your library, the page you are reading, and the conversation it inspires in a single considered view." visual={<LibraryVisual />} />
            <FeatureStory reverse eyebrow="Understanding, on demand" title="The assistant knows what you're looking at." body="Ask for a simpler explanation, a sharper summary, or the idea behind the idea — without leaving the document." visual={<ChatVisual />} />
            <FeatureStory eyebrow="A reading experience, refined" title="The page stays at the center." body="ChemMind gives your documents the room they need, then brings assistance close only when it is useful." visual={<ReaderVisual />} />
          </div>
        </section>

        {/* ─── HOW IT WORKS ─── */}
        <section id="how-it-works" className="py-24 sm:py-32 lg:py-40">
          <div className="mx-auto max-w-6xl px-6 sm:px-8 lg:px-12">
            <Reveal>
              <div className="text-center">
                <p className="text-xs font-semibold uppercase tracking-[0.15em] text-muted">How it works</p>
                <h2 className="mt-4 text-4xl font-bold tracking-[-0.035em] sm:text-5xl">
                  From source material
                  <br />
                  <span className="heading-serif text-muted">to clarity.</span>
                </h2>
              </div>
            </Reveal>

            <div className="mt-20 grid gap-px overflow-hidden rounded-2xl border border-border/50 bg-border/50 md:grid-cols-3">
              {[
                ["01", "Bring your knowledge", "Add the material you want to understand — notes, papers, textbooks."],
                ["02", "Follow your curiosity", "Ask natural questions as you read. The AI stays grounded in your content."],
                ["03", "Make it yours", "Turn raw context into lasting understanding through conversation."],
              ].map(([num, title, body], i) => (
                <Reveal key={num} delay={i * 0.12}>
                  <div className="flex flex-col bg-surface p-8 sm:p-10">
                    <span className="heading-serif text-3xl text-muted/30">{num}</span>
                    <h3 className="mt-5 text-xl font-semibold tracking-[-0.02em]">{title}</h3>
                    <p className="mt-3 text-sm leading-6 text-muted">{body}</p>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* ─── FINAL CTA ─── */}
        <section className="relative overflow-hidden">
          <div className="cta-glow py-28 sm:py-40 lg:py-48">
            <Reveal>
              <div className="mx-auto max-w-3xl px-6 text-center">
                <h2 className="text-4xl font-bold tracking-[-0.04em] sm:text-5xl lg:text-6xl">
                  A calmer way
                  <br />
                  <span className="heading-serif text-muted">to think.</span>
                </h2>
                <p className="mt-7 text-lg leading-7 text-muted sm:text-xl sm:leading-8">
                  Step into a more focused relationship with your knowledge.
                </p>
                <Link href="/workspace" className="group mt-10 inline-flex items-center gap-2 rounded-full bg-foreground px-8 py-4 text-base font-semibold text-background shadow-[0_8px_30px_rgba(0,0,0,0.12)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_16px_50px_rgba(0,0,0,0.18)] active:translate-y-0">
                  Launch ChemMind
                  <ArrowUpRight className="size-4 transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
                </Link>
              </div>
            </Reveal>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}

/* ─── SUB-COMPONENTS ─── */

function WorkspacePreview() {
  return (
    <div className="overflow-hidden rounded-2xl border border-border/60 bg-surface shadow-[0_30px_90px_rgba(0,0,0,0.12)] sm:rounded-3xl">
      <div className="flex h-10 items-center border-b border-border/50 bg-surface px-4 sm:h-11 sm:px-5">
        <div className="flex gap-1.5"><i className="size-2.5 rounded-full bg-[#FF5F57]"/><i className="size-2.5 rounded-full bg-[#FEBC2E]"/><i className="size-2.5 rounded-full bg-[#28C840]"/></div>
        <div className="mx-auto hidden rounded-md bg-background/80 px-14 py-1 text-[9px] text-muted sm:block">chemmind.app</div>
      </div>
      <div className="flex h-[clamp(240px,42vw,480px)]">
        <aside className="hidden w-[22%] border-r border-border/40 bg-surface/80 p-4 md:block">
          <p className="text-[10px] font-bold tracking-[0.1em] text-muted/70">CHEMMIND</p>
          <div className="mt-6 rounded-lg bg-foreground px-3 py-2 text-[10px] font-semibold text-background">+ New conversation</div>
          <div className="mt-5 space-y-1 text-[10px] text-muted"><p className="rounded-md bg-foreground/5 px-2 py-2 font-medium text-foreground">Home</p><p className="px-2 py-2">Documents</p><p className="px-2 py-2">Recent</p></div>
        </aside>
        <article className="min-w-0 flex-1 bg-background/50 px-6 py-6 sm:px-12 sm:py-8">
          <div className="mx-auto max-w-md">
            <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-muted/60">Molecular chemistry</p>
            <h3 className="mt-3 text-lg font-bold tracking-[-0.03em] sm:text-xl">1. Molecular Structure</h3>
            <div className="mt-5 space-y-2"><Skel w="100%"/><Skel w="93%"/><Skel w="76%"/></div>
            <h4 className="mt-6 text-sm font-semibold">VSEPR Theory</h4>
            <div className="mt-3 space-y-2"><Skel w="100%"/><Skel w="100%"/><Skel w="84%"/></div>
          </div>
        </article>
        <aside className="hidden w-[28%] min-w-[200px] border-l border-border/40 bg-surface/80 lg:flex lg:flex-col">
          <div className="border-b border-border/40 px-4 py-3"><div className="flex items-center gap-2 text-xs font-semibold"><span className="flex size-5 items-center justify-center rounded-full bg-foreground text-[9px] text-background">✦</span>ChemMind</div><p className="mt-1 text-[9px] text-muted">Grounded in this document</p></div>
          <div className="flex-1 space-y-3 p-4"><div className="ml-auto max-w-[85%] rounded-2xl rounded-tr-md bg-foreground/5 px-3 py-2 text-[10px] leading-4">Explain VSEPR theory simply.</div><div className="max-w-[90%] rounded-2xl rounded-tl-md border border-border/30 px-3 py-2 text-[10px] leading-4">Electron pairs naturally spread out around an atom, because like charges repel.</div></div>
          <div className="m-3 rounded-xl border border-border/50 px-3 py-2 text-[10px] text-muted">Ask about this page…</div>
        </aside>
      </div>
    </div>
  );
}

function Skel({ w }: { w: string }) { return <div className="h-1.5 rounded-full bg-foreground/[0.06]" style={{ width: w }} />; }

function FeatureStory({ eyebrow, title, body, visual, reverse = false }: { eyebrow: string; title: string; body: string; visual: React.ReactNode; reverse?: boolean }) {
  return (
    <div className={`grid items-center gap-12 lg:grid-cols-2 lg:gap-20 ${reverse ? "lg:[&>div:first-child]:order-2" : ""}`}>
      <Reveal>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-muted">{eyebrow}</p>
          <h3 className="mt-5 max-w-lg text-3xl font-bold tracking-[-0.035em] sm:text-4xl lg:text-[2.6rem] lg:leading-[1.1]">{title}</h3>
          <p className="mt-5 max-w-lg text-base leading-7 text-muted">{body}</p>
        </div>
      </Reveal>
      <Reveal delay={0.15}>
        {visual}
      </Reveal>
    </div>
  );
}

function Frame({ children }: { children: React.ReactNode }) {
  return <div className="aspect-[16/10] overflow-hidden rounded-2xl border border-border/50 bg-surface p-6 shadow-[0_16px_50px_-12px_rgba(0,0,0,0.08)] transition-shadow duration-500 hover:shadow-[0_24px_70px_-12px_rgba(0,0,0,0.12)] sm:p-8">{children}</div>;
}

function LibraryVisual() {
  return (
    <Frame>
      <div className="flex h-full gap-5">
        <div className="w-1/3 border-r border-border/40 pr-4">
          <p className="text-xs font-bold">Library</p>
          <div className="mt-5 space-y-1.5">{["Chemistry", "Physics", "Research"].map((t, i) => <p key={t} className={`rounded-lg px-2 py-2 text-xs ${i === 0 ? "bg-foreground/5 font-medium" : "text-muted"}`}>{t}</p>)}</div>
        </div>
        <div className="flex-1">
          <p className="text-xs font-semibold text-muted">Recently opened</p>
          <div className="mt-4 space-y-2.5">{["Organic chemistry notes", "Molecular geometry", "Protein folding"].map((t, i) => <div key={t} className="flex items-center gap-3 rounded-xl border border-border/40 p-2.5 transition-colors hover:border-border"><span className={`flex size-7 items-center justify-center rounded-lg ${i === 1 ? "bg-foreground/5" : "bg-foreground/[0.03]"} text-muted`}><FileText size={13}/></span><div><p className="text-xs font-medium">{t}</p><p className="text-[10px] text-muted/60">Updated today</p></div></div>)}</div>
        </div>
      </div>
    </Frame>
  );
}

function ChatVisual() {
  return (
    <Frame>
      <div className="flex h-full flex-col">
        <div className="flex items-center gap-2 border-b border-border/40 pb-3 text-sm font-semibold"><span className="flex size-5 items-center justify-center rounded-full bg-foreground text-background"><Sparkles size={10}/></span>ChemMind</div>
        <div className="flex flex-1 flex-col justify-end gap-3 py-4">
          <p className="ml-auto max-w-[70%] rounded-2xl rounded-tr-md bg-foreground/5 px-3.5 py-2.5 text-xs leading-5">What are the key differences between ionic and covalent bonds?</p>
          <div className="max-w-[85%] rounded-2xl rounded-tl-md border border-border/30 px-3.5 py-2.5 text-xs leading-5"><p>It comes down to what happens to electrons.</p><p className="mt-1.5 text-muted">Ionic bonds transfer them; covalent bonds share them.</p></div>
        </div>
        <div className="rounded-xl border border-border/50 px-3.5 py-2.5 text-xs text-muted">Ask a follow-up question…</div>
      </div>
    </Frame>
  );
}

function ReaderVisual() {
  return (
    <Frame>
      <div className="grid h-full grid-cols-[1.3fr_0.7fr] gap-4">
        <div className="rounded-xl border border-border/40 p-4">
          <p className="text-xs font-semibold">Molecular structure</p>
          <div className="mt-4 space-y-2"><Skel w="100%"/><Skel w="100%"/><Skel w="80%"/></div>
          <div className="mt-4 rounded-lg bg-foreground/[0.03] p-3"><p className="text-[10px] leading-4 text-muted">Electron pairs arrange themselves to minimize repulsion around the central atom.</p></div>
        </div>
        <div className="flex flex-col gap-2.5 rounded-xl bg-background/80 p-3">
          <p className="text-[10px] font-semibold text-muted">Key concepts</p>
          {["Electron pairs", "Molecular shape", "Bond angles"].map((t) => <p key={t} className="rounded-lg bg-surface px-2.5 py-2 text-[10px] shadow-sm">{t}</p>)}
        </div>
      </div>
    </Frame>
  );
}
