"use client";

import Link from "next/link";
import { IBM_Plex_Sans, Playfair_Display } from "next/font/google";
import {
  ArrowRight,
  Terminal,
  ShieldCheck,
  Cpu,
  Lock,
  FileSearch,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import ThemeToggle from "@/components/ui/theme-toggle";

const plex = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});
const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

export default function AboutPage() {
  return (
    <main
      className={`${plex.className} min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] relative`}
    >
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
      <div className="absolute inset-x-0 top-0 h-72 bg-[radial-gradient(circle_at_top,rgba(98,146,158,0.12),transparent_65%)] pointer-events-none" />

      <div className="relative z-10">
        <nav className="border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md sticky top-0 z-50">
          <div className="cd-container h-16 flex items-center justify-between">
            <Link
              href="/"
              className="font-bold text-xl tracking-tighter flex items-center gap-2"
            >
              <div className="w-8 h-8 bg-[#62929e]/10 border border-[#62929e]/20 rounded-md flex items-center justify-center">
                <Terminal className="w-4 h-4 text-[#62929e]" />
              </div>
              ClearDrive<span className="text-[#62929e]">.lk</span>
            </Link>
            <div className="hidden md:flex gap-8 text-sm font-medium text-[#546a7b]">
              <Link
                href="/dashboard/vehicles"
                className="hover:text-[#393d3f] transition-colors flex items-center gap-2"
              >
                Auctions{" "}
                <Badge
                  variant="outline"
                  className="text-[10px] border-[#62929e]/20 text-[#62929e] h-4 px-1"
                >
                  LIVE
                </Badge>
              </Link>
              <Link
                href="/#process"
                className="hover:text-[#393d3f] transition-colors"
              >
                How It Works
              </Link>
              <Link
                href="/#lane"
                className="hover:text-[#393d3f] transition-colors"
              >
                Live Shipping Lane
              </Link>
              <Link
                href="/about"
                className="hover:text-[#393d3f] transition-colors text-[#393d3f]"
              >
                About Us
              </Link>
            </div>
            <div className="flex gap-3 items-center">
              <ThemeToggle />
              <Link href="/login">
                <Button
                  variant="ghost"
                  className="text-[#546a7b] hover:text-[#393d3f] hover:bg-[#c6c5b9]/20 font-mono"
                >
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold">
                  Get Access
                </Button>
              </Link>
            </div>
          </div>
        </nav>

        {/* Hero */}
        <section className="cd-container pt-24 pb-16 relative">
          <div className="hero-spotlight absolute inset-0 pointer-events-none" />
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-3 rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-4 py-2 text-xs font-mono uppercase tracking-[0.35em] text-[#62929e]">
              <Terminal className="h-4 w-4" />
              Manifest :: Terminal Layer
            </div>
            <h1
              className={`${playfair.className} mt-8 text-4xl md:text-6xl font-semibold tracking-tight text-[#393d3f]`}
            >
              Engineering Absolute Transparency.
            </h1>
            <p className="mt-6 text-lg text-[#546a7b] leading-relaxed">
              ClearDrive.lk is Sri Lanka&apos;s first direct-to-consumer vehicle
              import terminal, bypassing traditional agent markups through direct
              API integrations with Japanese auction houses.
            </p>

            <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                {
                  label: "Direct API",
                  value: "USS Tokyo - JAA - CAI",
                },
                {
                  label: "Tax Engine",
                  value: "CIF + Duty = Deterministic",
                },
                {
                  label: "Shipment",
                  value: "Lane Visibility 24/7",
                },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="relative overflow-hidden rounded-xl border border-[#546a7b]/70 bg-[#fdfdff]/90 dark:bg-[rgba(255,255,255,0.08)] dark:border-white/20 px-4 py-4 shadow-[0_16px_34px_rgba(15,23,42,0.14)]"
                >
                  <div className="absolute inset-0 bg-[linear-gradient(120deg,transparent,rgba(98,146,158,0.18),transparent)] opacity-0 hover:opacity-100 transition-opacity" />
                  <p className="text-[10px] font-mono uppercase tracking-[0.3em] text-[#546a7b] dark:text-white/70">
                    {stat.label}
                  </p>
                  <p className="mt-2 text-sm font-semibold text-[#393d3f] dark:text-white/95">
                    {stat.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Core Problem vs Architecture */}
        <section className="cd-container pb-16">
          <div>
            <div className="max-w-2xl">
              <p className="text-xs font-mono uppercase tracking-[0.4em] text-[#546a7b]">
                Problem / Architecture
              </p>
              <h2
                className={`${playfair.className} mt-4 text-3xl md:text-4xl font-semibold text-[#393d3f]`}
              >
                Replace opacity with machine-verifiable math.
              </h2>
            </div>

            <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="relative overflow-hidden rounded-2xl border border-[#546a7b]/70 bg-[#fdfdff]/95 dark:bg-[rgba(255,255,255,0.08)] dark:border-white/20 p-6 shadow-[0_20px_40px_rgba(15,23,42,0.16)]">
                <div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-[#546a7b] via-[#62929e] to-[#c6c5b9]" />
                <p className="text-xs font-mono uppercase tracking-[0.35em] text-[#62929e] dark:text-[#b7d7de]">
                  The Old Way
                </p>
                <p className="mt-4 text-[#546a7b] dark:text-white/80 leading-relaxed">
                  Opaque pricing, hidden agent commissions, manual and outdated
                  customs calculations, and zero visibility on shipping lanes.
                </p>
              </div>
              <div className="relative overflow-hidden rounded-2xl border border-[#62929e]/60 bg-[#fdfdff]/95 dark:bg-[rgba(255,255,255,0.08)] dark:border-white/20 p-6 shadow-[0_24px_48px_rgba(98,146,158,0.28)]">
                <div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-[#62929e] via-[#546a7b] to-[#c6c5b9]" />
                <p className="text-xs font-mono uppercase tracking-[0.35em] text-[#62929e] dark:text-[#b7d7de]">
                  The ClearDrive Pipeline
                </p>
                <p className="mt-4 text-[#546a7b] dark:text-white/80 leading-relaxed">
                  Direct market access to USS Tokyo, JAA, and CAI. We built a
                  proprietary Tax Engine that extracts live government gazettes
                  to calculate exact CIF and Customs Duty in real-time. What you
                  see is mathematically guaranteed.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Tech Stack */}
        <section className="cd-container pb-16">
          <div>
            <div className="max-w-2xl">
              <p className="text-xs font-mono uppercase tracking-[0.4em] text-[#546a7b]">
                The Stack
              </p>
              <h2
                className={`${playfair.className} mt-4 text-3xl md:text-4xl font-semibold text-[#393d3f]`}
              >
                Built like an exchange terminal.
              </h2>
            </div>

            <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                {
                  icon: Cpu,
                  title:
                    "Built on a high-speed Next.js 14 architecture with a FastAPI Python engine.",
                },
                {
                  icon: ShieldCheck,
                  title:
                    "Live financial routing via PayHere with end-to-end payload encryption.",
                },
                {
                  icon: Lock,
                  title: "Volatile AI infrastructure for privacy-first user assistance.",
                },
                {
                  icon: FileSearch,
                  title:
                    "Automated Document AI for KYC and Bill of Lading verification.",
                },
              ].map((itemData, index) => (
                <div
                  key={index}
                  className="relative overflow-hidden rounded-2xl border border-[#546a7b]/65 bg-[#fdfdff]/95 dark:bg-[rgba(255,255,255,0.08)] dark:border-white/20 p-6 flex gap-4 shadow-[0_16px_34px_rgba(15,23,42,0.14)]"
                >
                  <div className="absolute left-0 top-0 h-full w-1 bg-gradient-to-b from-[#62929e] via-[#546a7b] to-[#c6c5b9]" />
                  <div className="h-11 w-11 rounded-xl bg-[#62929e]/10 text-[#62929e] flex items-center justify-center">
                    <itemData.icon className="h-5 w-5" />
                  </div>
                  <p className="text-[#546a7b] dark:text-white/80 leading-relaxed">
                    {itemData.title}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="cd-container pb-8">
          <div className="rounded-2xl border border-[#546a7b]/70 bg-[#fdfdff]/95 dark:bg-[rgba(255,255,255,0.08)] dark:border-white/20 px-8 py-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-[0_22px_46px_rgba(15,23,42,0.16)]">
            <div>
              <p className="text-xs font-mono uppercase tracking-[0.4em] text-[#546a7b] dark:text-white/60">
                Access Terminal
              </p>
              <h3
                className={`${playfair.className} mt-3 text-3xl font-semibold text-[#393d3f] dark:text-white/90`}
              >
                Stop guessing landed costs. Access the terminal.
              </h3>
            </div>
            <Button
              asChild
              className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-semibold gap-2"
            >
              <Link href="/register">
                Create Free Account <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </section>
      </div>
    </main>
  );
}
