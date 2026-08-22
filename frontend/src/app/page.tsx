"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import { Footer } from "@/components/layout/Footer";
import { Navbar } from "@/components/layout/Navbar";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <div className="min-h-screen overflow-x-clip bg-background selection:bg-accent/20">
      <Navbar />
      <main>
        <section className="relative pt-36 sm:pt-44 lg:pt-52"><div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-12"><motion.div initial={{ opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }} className="mx-auto max-w-5xl text-center"><p className="mb-6 text-sm font-semibold tracking-[0.16em] text-accent uppercase">ChemMind</p><h1 className="text-balance text-[3.4rem] font-bold leading-[0.96] tracking-[-0.065em] text-foreground sm:text-7xl md:text-8xl lg:text-[7.5rem]">Think Smarter.<br /><span className="text-muted">Learn Deeper.</span></h1><p className="mx-auto mt-8 max-w-2xl text-pretty text-lg leading-8 text-muted sm:mt-10 sm:text-2xl sm:leading-9">Your reading, research, and reasoning—together in one calm, intelligent workspace.</p><div className="mt-9 flex flex-col items-stretch justify-center gap-3 sm:mt-11 sm:flex-row sm:items-center"><Link href="/workspace" className="sm:w-auto"><Button size="lg" className="group w-full rounded-full px-7 shadow-[0_8px_24px_rgba(29,29,31,0.12)] sm:w-auto">Open workspace <ArrowUpRight className="ml-1 size-4 transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5" /></Button></Link><Link href="#features" className="sm:w-auto"><Button size="lg" variant="secondary" className="w-full rounded-full px-7 sm:w-auto">Explore ChemMind</Button></Link></div></motion.div></div></section>
      </main>
      <Footer />
    </div>
  );
}
