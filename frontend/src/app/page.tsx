"use client";

import Link from "next/link";
import { Footer } from "@/components/layout/Footer";
import { Navbar } from "@/components/layout/Navbar";

export default function LandingPage() {
  return (
    <div className="min-h-screen overflow-x-clip bg-background selection:bg-accent/20">
      <Navbar />
      <main>
        {/* Stages will build out this content */}
      </main>
      <Footer />
    </div>
  );
}
