"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { cn } from "@/lib/utils";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 18);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-all duration-500",
        scrolled
          ? "border-b border-border/50 bg-background/80 py-3 backdrop-blur-2xl"
          : "py-5 sm:py-6"
      )}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-12">
        <Link href="/" className="group flex items-center gap-2.5">
          <div className="flex size-8 items-center justify-center rounded-lg bg-foreground text-background transition-transform duration-300 group-hover:scale-105">
            <span className="text-sm font-bold">C</span>
          </div>
          <span className="text-[15px] font-semibold tracking-[-0.02em] sm:text-base">ChemMind</span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          <Link href="#features" className="text-[13px] font-medium text-muted transition-colors duration-200 hover:text-foreground">Features</Link>
          <Link href="/projects" className="text-[13px] font-medium text-muted transition-colors duration-200 hover:text-foreground">Projects</Link>
          <Link href="#how-it-works" className="text-[13px] font-medium text-muted transition-colors duration-200 hover:text-foreground">How it works</Link>
        </nav>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Link
            href="/projects"
            className="group inline-flex items-center gap-1.5 rounded-full bg-foreground px-5 py-2 text-[13px] font-semibold text-background transition-all duration-300 hover:-translate-y-px hover:shadow-lg active:translate-y-0"
          >
            Start learning
            <svg className="size-3.5 transition-transform duration-300 group-hover:translate-x-0.5" fill="none" viewBox="0 0 16 16" stroke="currentColor" strokeWidth={2}>
              <path d="M3 8h10M9 4l4 4-4 4" />
            </svg>
          </Link>
        </div>
      </div>
    </motion.header>
  );
}
