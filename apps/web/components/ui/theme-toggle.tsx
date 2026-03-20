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
  nav: "h-9 w-9 p-0",
  sm: "h-8 w-8 p-0",
  md: "h-10 w-10 p-0",
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
      aria-label={
        theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
      }
      title={theme === "dark" ? "Light mode" : "Dark mode"}
      className={cn(
        "group inline-flex items-center justify-center rounded-full border border-[#546a7b]/60 bg-[#fdfdff]/90 text-[#1f2937] shadow-[0_10px_22px_rgba(0,0,0,0.15)] backdrop-blur-md transition-[transform,box-shadow,background-color,color,border-color] duration-200 hover:-translate-y-[1px] hover:bg-[#f7fafc] hover:shadow-[0_14px_28px_rgba(0,0,0,0.22)] active:translate-y-[1px] dark:border-[#8fa3b1]/45 dark:bg-[#132028]/90 dark:text-[#e6eef5] dark:hover:bg-[#1b2b35]",
        sizeStyles[size],
        className,
      )}
    >
      <span
        className={cn(
          "flex items-center justify-center rounded-full border border-[hsl(var(--steel))] bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.78),transparent_60%)] text-[hsl(var(--steel))] shadow-[inset_0_1px_0_rgba(255,255,255,0.65)] transition group-hover:scale-[1.04] dark:border-[#9bb5c4] dark:text-[#cfe0ea]",
          iconStyles[size],
        )}
      >
        {theme === "dark" ? (
          <Sun className="h-4 w-4" />
        ) : (
          <Moon className="h-4 w-4" />
        )}
      </span>
    </button>
  );
}
