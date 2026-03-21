"use client";

import type { ComponentType, ReactNode } from "react";
import { cn } from "@/lib/utils";

type ShellWidth = "wide" | "narrow" | "tight";

type ExporterPageShellProps = {
  eyebrow: string;
  title: string;
  accent: string;
  description: string;
  icon: ComponentType<{ className?: string }>;
  actions?: ReactNode;
  children: ReactNode;
  width?: ShellWidth;
};

export function ExporterPageShell({
  eyebrow,
  title,
  accent,
  description,
  icon: Icon,
  actions,
  children,
  width = "wide",
}: ExporterPageShellProps) {
  const containerClass =
    width === "narrow"
      ? "cd-container-narrow"
      : width === "tight"
        ? "cd-container-tight"
        : "cd-container";

  return (
    <section className="relative flex-1 overflow-hidden pb-16 pt-10 md:pt-12">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(84,106,123,0.07)_1px,transparent_1px),linear-gradient(to_bottom,rgba(84,106,123,0.07)_1px,transparent_1px)] bg-[size:34px_34px] dark:bg-[linear-gradient(to_right,rgba(143,163,177,0.09)_1px,transparent_1px),linear-gradient(to_bottom,rgba(143,163,177,0.09)_1px,transparent_1px)]" />
        <div className="absolute left-1/2 top-[-10%] h-[420px] w-[780px] -translate-x-1/2 rounded-[100%] bg-[#62929e]/12 blur-[110px] dark:bg-[#88d6e4]/15" />
      </div>

      <div className={cn("relative z-10 space-y-8", containerClass)}>
        <header className="rounded-3xl border border-[#546a7b]/45 bg-[#fdfdff]/74 p-6 shadow-[0_18px_42px_rgba(15,23,42,0.1)] dark:border-[#8fa3b1]/30 dark:bg-[#121d23]/74 dark:shadow-[0_18px_42px_rgba(0,0,0,0.32)] md:p-8">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#546a7b]/45 bg-[#c6c5b9]/20 px-4 py-1.5 font-mono text-xs uppercase tracking-[0.2em] text-[#62929e] dark:border-[#8fa3b1]/35 dark:bg-[#22313c] dark:text-[#88d6e4]">
            <Icon className="h-3.5 w-3.5" />
            {eyebrow}
          </div>

          <div className="flex flex-wrap items-end justify-between gap-5">
            <div className="max-w-3xl">
              <h1 className="text-4xl font-bold tracking-tight text-[#1f2937] dark:text-[#edf2f7] md:text-6xl">
                {title}{" "}
                <span className="bg-gradient-to-r from-[#62929e] to-[#546a7b] bg-clip-text text-transparent dark:from-[#88d6e4] dark:to-[#9fb8c9]">
                  {accent}
                </span>
              </h1>
              <p className="mt-4 text-base text-[#546a7b] dark:text-[#bdcad4] md:text-lg">
                {description}
              </p>
            </div>
            {actions ? (
              <div className="flex flex-wrap gap-3">{actions}</div>
            ) : null}
          </div>
        </header>

        {children}
      </div>
    </section>
  );
}

export function ExporterPanel({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-[#546a7b]/45 bg-[#fdfdff]/74 p-5 transition-[transform,box-shadow,border-color] duration-200 hover:-translate-y-[1px] hover:border-[#62929e]/35 hover:shadow-[0_16px_34px_rgba(15,23,42,0.12)] dark:border-[#8fa3b1]/30 dark:bg-[#131d23]/74 dark:hover:border-[#88d6e4]/35 dark:hover:shadow-[0_16px_34px_rgba(0,0,0,0.24)] md:p-6",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function ExporterEmptyState({
  icon: Icon,
  title,
  description,
}: {
  icon: ComponentType<{ className?: string }>;
  title: string;
  description: string;
}) {
  return (
    <ExporterPanel className="p-12 text-center">
      <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full border border-[#62929e]/25 bg-[#62929e]/10 text-[#62929e] dark:border-[#88d6e4]/30 dark:bg-[#88d6e4]/15 dark:text-[#88d6e4]">
        <Icon className="h-6 w-6" />
      </div>
      <h2 className="text-2xl font-semibold text-[#1f2937] dark:text-[#edf2f7]">
        {title}
      </h2>
      <p className="mx-auto mt-2 max-w-xl text-sm text-[#546a7b] dark:text-[#bdcad4]">
        {description}
      </p>
    </ExporterPanel>
  );
}
