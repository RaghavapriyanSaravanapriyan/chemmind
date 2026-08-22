"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

import { cn } from "@/lib/utils";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => { const onScroll = () => setScrolled(window.scrollY > 18); onScroll(); window.addEventListener("scroll", onScroll, { passive: true }); return () => window.removeEventListener("scroll", onScroll); }, []);
  return <header className={cn("fixed inset-x-0 top-0 z-50 transition-all duration-500", scrolled ? "border-b border-border/60 bg-background/80 py-3 backdrop-blur-xl" : "py-5 sm:py-6")}><div className="mx-auto flex max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-12"><Link href="/" className="text-[15px] font-bold tracking-[-0.04em] sm:text-base">CHEMMIND</Link><nav className="hidden items-center gap-8 md:flex"><Link href="#features" className="text-sm font-medium text-muted transition-colors hover:text-foreground">Product</Link><Link href="/workspace" className="text-sm font-medium text-muted transition-colors hover:text-foreground">Workspace</Link><Link href="#about" className="text-sm font-medium text-muted transition-colors hover:text-foreground">About</Link></nav><div className="flex items-center gap-3"><button type="button" title="Sign in is coming soon" className="hidden text-sm font-medium text-muted transition-colors hover:text-foreground sm:inline-flex">Sign In</button><Link href="/workspace"><Button size="sm" className="rounded-full px-4 sm:px-5">Get started</Button></Link></div></div></header>;
}
