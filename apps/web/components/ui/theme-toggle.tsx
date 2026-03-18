"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

type ThemeMode = "light" | "dark";

const STORAGE_KEY = "cleardrive-theme";

function getSystemPreference() {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export default function ThemeToggle({ className }: { className?: string }) {
  const [mounted, setMounted] = useState(false);
  const [theme, setTheme] = useState<ThemeMode>("light");

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    const initial =
      stored === "light" || stored === "dark"
        ? (stored as ThemeMode)
        : getSystemPreference();
    setTheme(initial);
    const root = document.documentElement;
    root.classList.toggle("dark", initial === "dark");
    setMounted(true);
  }, []);

  const applyTheme = (next: ThemeMode) => {
    const root = document.documentElement;
    root.classList.add("theme-transition");
    root.classList.toggle("dark", next === "dark");
    window.setTimeout(() => {
      root.classList.remove("theme-transition");
    }, 260);
    localStorage.setItem(STORAGE_KEY, next);
  };

  const handleToggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
  };

  if (!mounted) return null;

  return (
    <button
      type="button"
      onClick={handleToggle}
      aria-label="Toggle color theme"
      className={cn(
        "group inline-flex items-center gap-3 rounded-full border border-[hsl(var(--steel))] bg-[linear-gradient(135deg,rgba(255,255,255,0.65),rgba(255,255,255,0.15))] px-4 py-2 text-[10px] font-semibold uppercase tracking-[0.3em] text-foreground shadow-[0_12px_30px_rgba(0,0,0,0.25)] backdrop-blur-md transition hover:shadow-[0_16px_40px_rgba(0,0,0,0.35)] dark:bg-[linear-gradient(135deg,rgba(255,255,255,0.08),rgba(255,255,255,0.02))]",
        className,
      )}
    >
      <span className="flex h-8 w-8 items-center justify-center rounded-full border border-[hsl(var(--bronze))] bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.7),transparent_60%)] text-[hsl(var(--bronze))] shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] transition group-hover:scale-[1.04]">
        {theme === "dark" ? (
          <Sun className="h-4 w-4" />
        ) : (
          <Moon className="h-4 w-4" />
        )}
      </span>
      <span className="hidden sm:inline">
        {theme === "dark" ? "Light Mode" : "Dark Mode"}
      </span>
    </button>
  );
}
