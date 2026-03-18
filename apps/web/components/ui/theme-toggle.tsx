"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

type ThemeMode = "light" | "dark";
type ThemeToggleSize = "nav" | "sm" | "md";

const STORAGE_KEY = "cleardrive-theme";

function getSystemPreference() {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

const sizeStyles: Record<ThemeToggleSize, string> = {
  nav: "h-9 px-3 text-[9px] tracking-[0.2em]",
  sm: "h-8 px-2 text-[8px] tracking-[0.2em]",
  md: "h-10 px-4 text-[10px] tracking-[0.3em]",
};

const iconStyles: Record<ThemeToggleSize, string> = {
  nav: "h-7 w-7",
  sm: "h-6 w-6",
  md: "h-8 w-8",
};

export default function ThemeToggle({
  className,
  size = "nav",
}: {
  className?: string;
  size?: ThemeToggleSize;
}) {
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
    }, 180);
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
        "group inline-flex items-center gap-2 rounded-full border border-border bg-card/90 text-foreground shadow-[0_10px_22px_rgba(0,0,0,0.15)] backdrop-blur-md transition-[transform,box-shadow,background-color,color] duration-200 hover:bg-accent hover:shadow-[0_14px_28px_rgba(0,0,0,0.22)] hover:-translate-y-[1px] active:translate-y-[1px] dark:bg-card/80",
        sizeStyles[size],
        className,
      )}
    >
      <span
        className={cn(
          "flex items-center justify-center rounded-full border border-[hsl(var(--steel))] bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.7),transparent_60%)] text-[hsl(var(--steel))] shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] transition group-hover:scale-[1.04] dark:border-[hsl(var(--steel-soft))] dark:text-[hsl(var(--steel-soft))]",
          iconStyles[size],
        )}
      >
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
