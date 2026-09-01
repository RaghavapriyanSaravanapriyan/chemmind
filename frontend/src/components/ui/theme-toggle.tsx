"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

const storageKey = "chemmind-theme";

function applyTheme(theme: "light" | "dark") {
  const root = document.documentElement;
  root.classList.add("theme-transition");
  root.classList.toggle("dark", theme === "dark");
  root.style.colorScheme = theme;
  window.setTimeout(() => root.classList.remove("theme-transition"), 240);
}

export function ThemeToggle({ className = "" }: { className?: string }) {
  const [mounted, setMounted] = useState(false);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const isDarkOnLoad = document.documentElement.classList.contains("dark");
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsDark(isDarkOnLoad);
    setMounted(true);
  }, []);

  const toggle = () => {
    const nextTheme = isDark ? "light" : "dark";
    applyTheme(nextTheme);
    localStorage.setItem(storageKey, nextTheme);
    setIsDark(!isDark);
  };

  if (!mounted) {
    return (
      <div className={`group flex size-8 items-center justify-center rounded-full border border-border/70 bg-surface text-muted shadow-sm ${className}`} />
    );
  }

  return <button type="button" onClick={toggle} aria-label={`Switch to ${isDark ? "light" : "dark"} mode`} title={`Switch to ${isDark ? "light" : "dark"} mode`} className={`group flex size-8 items-center justify-center rounded-full border border-border/70 bg-surface text-muted shadow-sm transition-[transform,background-color,color,border-color] duration-300 hover:-translate-y-px hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 ${className}`}>
    <span className="relative flex size-4 items-center justify-center transition-transform duration-300 group-hover:rotate-12">{isDark ? <Sun className="absolute size-4" /> : <Moon className="absolute size-4" />}</span>
  </button>;
}
