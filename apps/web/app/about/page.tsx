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
  Globe,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import ThemeToggle from "@/components/ui/theme-toggle";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import { useEffect, useRef, useState } from "react";

const plex = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});
const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const milestones = [
  {
    title: "Identifying market data asymmetry",
    desc: "We mapped the broken Sri Lankan import chain and proved the price opacity was systemic, not accidental.",
  },
  {
    title: "Engineering the Python FastAPI Tax Engine",
    desc: "A Gazette Parsing Engine that extracts rules from government PDFs and computes deterministic CIF and duty values.",
  },
  {
    title: "Securing financial routing with PayHere",
    desc: "End-to-end encrypted settlement with split payments and auditable payment traces.",
  },
  {
    title: "Deploying a high-frequency Next.js terminal",
    desc: "A real-time auction and clearance dashboard built to feel like a trading desk.",
  },
];

const team = [
  {
    name: "Malith De Silva",
    role: "Backend & Security Lead",
    tag: "CORE-INFRA",
    accent: "#9ddcff",
    accent2: "#4a9bff",
  },
  {
    name: "Lehan Methyuga",
    role: "Frontend & Mobile Lead",
    tag: "CLIENT-TERMINAL",
    accent: "#7cc7ff",
    accent2: "#3a86ff",
  },
  {
    name: "Pavara Mandara",
    role: "AI/ML & KYC Lead",
    tag: "VOLATILE-LOGIC",
    accent: "#62b0ff",
    accent2: "#2f6fe8",
  },
  {
    name: "Parindra Chamikara",
    role: "Vehicle Systems & DevOps Lead",
    tag: "SYS-OPS",
    accent: "#5fb6ff",
    accent2: "#4b7cff",
  },
  {
    name: "Tharin De Silva",
    role: "Order & Payment Lead",
    tag: "FIN-ROUTING",
    accent: "#8cc9ff",
    accent2: "#2f78ff",
  },
  {
    name: "Kalidu Indeera",
    role: "Shipping & Appendices Lead",
    tag: "LOGISTICS-NET",
    accent: "#a9dcff",
    accent2: "#4f8bff",
  },
];

const techNodes = [
  {
    title: "Next.js 14 (Turbopack)",
    desc: "High-speed, SEO-optimized client delivery with streaming UI.",
    icon: Cpu,
  },
  {
    title: "FastAPI & Python",
    desc: "Asynchronous data crunching and live tax calculations at scale.",
    icon: FileSearch,
  },
  {
    title: "Document AI / OCR",
    desc: "Extracting Sri Lankan Gazette rules and verifying KYC automatically.",
    icon: Lock,
  },
  {
    title: "Volatile AI Logic",
    desc: "Privacy-first chatbot logic that answers without storing user data.",
    icon: ShieldCheck,
  },
];

const pipelineNodes = [
  {
    title: "Auctions",
    desc: "USS Tokyo and JAA feeds",
    icon: Globe,
  },
  {
    title: "Tax Engine",
    desc: "CIF + Customs duty",
    icon: FileSearch,
  },
  {
    title: "Client Terminal",
    desc: "Next.js live UI",
    icon: Terminal,
  },
  {
    title: "PayHere",
    desc: "Secure payment rail",
    icon: ShieldCheck,
  },
];

const manifestoLines = [
  "initializing transparency protocol...",
  "bypassing legacy agent networks...",
  "extracting government tax gazettes...",
  "STATUS: MIDDLEMAN ELIMINATED.",
];

export default function AboutPage() {
  const timelineRef = useRef<HTMLDivElement | null>(null);
  const manifestoRef = useRef<HTMLDivElement | null>(null);
  const [timelineActive, setTimelineActive] = useState(false);
  const [manifestoActive, setManifestoActive] = useState(false);

  useEffect(() => {
    const timelineNode = timelineRef.current;
    const manifestoNode = manifestoRef.current;
    if (!timelineNode && !manifestoNode) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          if (entry.target === timelineNode) {
            setTimelineActive(true);
            observer.unobserve(entry.target);
          }
          if (entry.target === manifestoNode) {
            setManifestoActive(true);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.35 },
    );

    if (timelineNode) observer.observe(timelineNode);
    if (manifestoNode) observer.observe(manifestoNode);

    return () => observer.disconnect();
  }, []);

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
              <BrandMark className="h-8 w-8 rounded-md border border-[#62929e]/20 bg-[#62929e]/10" />
              <BrandWordmark />
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
        <section className="cd-container pt-24 pb-20 relative">
          <div className="hero-spotlight absolute inset-0 pointer-events-none" />
          <div className="grid gap-12 lg:grid-cols-[1.1fr_0.9fr] items-center">
            <div>
              <div className="inline-flex items-center gap-3 rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-4 py-2 text-xs font-mono uppercase tracking-[0.35em] text-[#62929e]">
                <Terminal className="h-4 w-4" />
                The Hook
              </div>
              <h1
                className={`${playfair.className} mt-8 text-4xl md:text-6xl lg:text-7xl font-semibold tracking-tight text-[#393d3f]`}
              >
                Replacing Middlemen with Code.
              </h1>
              <p className="mt-4 text-xl text-[#546a7b] font-semibold">
                Engineering Absolute Transparency.
              </p>
              <p className="mt-6 text-lg text-[#546a7b] leading-relaxed">
                We are not just selling cars. We are dismantling a broken,
                opaque import pipeline and replacing it with direct, auditable
                software. ClearDrive.lk is the terminal that makes the
                Tokyo-to-Colombo lane visible end-to-end.
              </p>

              <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                  {
                    label: "Direct-to-Consumer",
                    value: "No brokers, no markup",
                  },
                  {
                    label: "Live Import Lane",
                    value: "Tokyo to Colombo",
                  },
                  {
                    label: "Verified Math",
                    value: "Deterministic CIF",
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

            <div className="radar-panel">
              <div className="radar-grid" />
              <div className="radar-sweep" />
              <div className="radar-rings" />
              <div className="radar-route" />
              <div className="radar-point radar-point--tokyo" />
              <div className="radar-point radar-point--colombo" />
              <div className="radar-label radar-label--tokyo">Tokyo</div>
              <div className="radar-label radar-label--colombo">Colombo</div>
              <div className="radar-caption">
                Radar Feed: Tokyo to Colombo shipping lane
              </div>
            </div>
          </div>
        </section>

        {/* Scope & Problem */}
        <section className="cd-container pb-20">
          <div className="max-w-2xl">
            <p className="text-xs font-mono uppercase tracking-[0.4em] text-[#546a7b]">
              Scope & Problem
            </p>
            <h2
              className={`${playfair.className} mt-4 text-3xl md:text-4xl font-semibold text-[#393d3f]`}
            >
              The old market is a black box. We made it glass.
            </h2>
          </div>

          <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-box legacy-box">
              <div className="glass-box__header">
                <span>Legacy Market</span>
                <span className="glass-box__chip">Hidden Broker Fees</span>
              </div>
              <div className="glass-box__body legacy-box__body">
                <p className="legacy-text">Broker fee + 240,000 LKR</p>
                <p className="legacy-text">Manual customs adjustment</p>
                <p className="legacy-text">Missing CIF variance report</p>
                <p className="legacy-text">Shipping ETA unknown</p>
                <p className="legacy-text">Invoice issued by agent</p>
                <p className="legacy-text">Markup nested in exchange rate</p>
              </div>
              <p className="mt-4 text-sm text-[#546a7b]">
                Buyers face black-box pricing, hidden commissions, manual and
                outdated customs calculations, and zero visibility into where
                their money goes.
              </p>
            </div>

            <div className="glass-box pipeline-box">
              <div className="glass-box__header">
                <span>ClearDrive Pipeline</span>
                <span className="glass-box__chip">Rupee Breakdown</span>
              </div>
              <div className="glass-box__body pipeline-box__body">
                <div className="pipeline-row">
                  <span>FOB (JPY)</span>
                  <span>1,850,000</span>
                </div>
                <div className="pipeline-row">
                  <span>Freight + Insurance</span>
                  <span>238,000</span>
                </div>
                <div className="pipeline-row">
                  <span>CIF (LKR)</span>
                  <span>4,920,000</span>
                </div>
                <div className="pipeline-row">
                  <span>Customs Duty</span>
                  <span>1,360,000</span>
                </div>
                <div className="pipeline-row">
                  <span>VAT + Ports</span>
                  <span>410,000</span>
                </div>
                <div className="pipeline-row pipeline-row--total">
                  <span>Total Landed</span>
                  <span>6,690,000</span>
                </div>
              </div>
              <p className="mt-4 text-sm text-[#546a7b]">
                We bypass agents via direct APIs to USS Tokyo, JAA, and CAI,
                then calculate exact CIF and duty with a Gazette Parsing Engine.
              </p>
            </div>
          </div>
        </section>

        {/* Academic Journey */}
        <section className="cd-container pb-20" ref={timelineRef}>
          <div className="max-w-2xl">
            <p className="text-xs font-mono uppercase tracking-[0.4em] text-[#546a7b]">
              Academic Journey
            </p>
            <h2
              className={`${playfair.className} mt-4 text-3xl md:text-4xl font-semibold text-[#393d3f]`}
            >
              A national-scale architecture built by IIT and Westminster
              undergraduates.
            </h2>
            <p className="mt-4 text-lg text-[#546a7b]">
              This is a university project that behaves like production-grade
              infrastructure. We treated the import pipeline as a real trading
              system and engineered every layer to survive real-world scale.
            </p>
          </div>

          <div className="timeline mt-12">
            <div
              className={`timeline-line ${
                timelineActive ? "timeline-line--active" : ""
              }`}
            />
            <div
              className={`timeline-laser ${
                timelineActive ? "timeline-laser--active" : ""
              }`}
            />
            <div className="grid gap-8">
              {milestones.map((item, index) => (
                <div
                  key={item.title}
                  className={`timeline-node ${
                    timelineActive ? "timeline-node--active" : ""
                  }`}
                  style={
                    {
                      "--delay": `${index * 0.2}s`,
                    } as React.CSSProperties
                  }
                >
                  <div className="timeline-dot" />
                  <div>
                    <h3 className="text-xl font-semibold text-[#393d3f]">
                      {item.title}
                    </h3>
                    <p className="mt-2 text-[#546a7b]">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Core Infrastructure Team */}
        <section className="cd-container pb-20">
          <div className="max-w-2xl">
            <p className="text-xs font-mono uppercase tracking-[0.4em] text-[#546a7b]">
              Core Infrastructure Team
            </p>
            <h2
              className={`${playfair.className} mt-4 text-3xl md:text-4xl font-semibold text-[#393d3f]`}
            >
              The roster behind the terminal.
            </h2>
          </div>

          <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {team.map((member) => {
              const initial = member.name.charAt(0).toUpperCase();
              return (
                <div
                  key={member.name}
                  className="terminal-card"
                  style={
                    {
                      "--terminal-accent": member.accent,
                      "--terminal-accent-2": member.accent2,
                    } as React.CSSProperties
                  }
                >
                  <div className="terminal-card__glow" />
                  <div className="terminal-card__inner">
                    <div className="terminal-avatar">
                      <span>{initial}</span>
                    </div>
                    <div>
                      <p className="terminal-name">{member.name}</p>
                      <p className="terminal-role">{member.role}</p>
                      <span className="terminal-tag">[ {member.tag} ]</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Tech Arsenal */}
        <section className="cd-container pb-20">
          <div className="max-w-2xl">
            <p className="text-xs font-mono uppercase tracking-[0.4em] text-[#546a7b]">
              Tech Arsenal
            </p>
            <h2
              className={`${playfair.className} mt-4 text-3xl md:text-4xl font-semibold text-[#393d3f]`}
            >
              The architecture stack and live pipeline.
            </h2>
          </div>

          <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-6">
            {techNodes.map((node) => (
              <div key={node.title} className="tech-card">
                <div className="tech-card__icon">
                  <node.icon className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-[#393d3f]">
                    {node.title}
                  </h3>
                  <p className="mt-2 text-[#546a7b]">{node.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 relative">
            <div className="pipeline-track hidden md:block">
              <div className="pipeline-line" />
              <div className="pipeline-packet" />
              <div className="pipeline-packet pipeline-packet--delay" />
            </div>
            <div className="pipeline-track-vertical md:hidden">
              <div className="pipeline-line-vertical" />
              <div className="pipeline-packet-vertical" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative z-10">
              {pipelineNodes.map((node) => (
                <div key={node.title} className="pipeline-node">
                  <div className="pipeline-node__icon">
                    <node.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-xs font-mono uppercase tracking-[0.3em] text-[#546a7b]">
                      {node.title}
                    </p>
                    <p className="mt-2 text-sm font-semibold text-[#393d3f]">
                      {node.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Terminal Manifesto */}
        <section className="cd-container pb-20">
          <div className="max-w-2xl">
            <p className="text-xs font-mono uppercase tracking-[0.4em] text-[#546a7b]">
              Terminal Manifesto
            </p>
            <h2
              className={`${playfair.className} mt-4 text-3xl md:text-4xl font-semibold text-[#393d3f]`}
            >
              Boot sequence: transparency protocol.
            </h2>
          </div>

          <div
            ref={manifestoRef}
            className={`terminal-window ${
              manifestoActive ? "terminal-window--active" : ""
            }`}
          >
            <div className="terminal-header">
              <span className="terminal-dot terminal-dot--red" />
              <span className="terminal-dot terminal-dot--yellow" />
              <span className="terminal-dot terminal-dot--green" />
              <p className="terminal-title">clear-drive://boot</p>
            </div>
            <div className="terminal-body">
              {manifestoLines.map((line, index) => {
                const displayLine = `> ${line}`;
                return (
                  <div
                    key={line}
                    className={`terminal-line ${
                      manifestoActive ? "terminal-line--active" : ""
                    }`}
                    style={
                      {
                        "--delay": `${index * 0.45}s`,
                        "--chars": displayLine.length,
                      } as React.CSSProperties
                    }
                  >
                    {displayLine}
                  </div>
                );
              })}
              <div className="terminal-metrics">
                {[
                  { label: "Lane Status", value: "TOKYO → COLOMBO : STABLE" },
                  { label: "Auctions", value: "USS / JAA / CAI :: LINKED" },
                  { label: "Tax Engine", value: "GAZETTE PARSE :: OK" },
                  { label: "Payments", value: "PAYHERE ROUTE :: SECURE" },
                  { label: "Visibility", value: "CIF + DUTY :: VERIFIED" },
                  { label: "Protocol", value: "TRANSPARENCY MODE : ON" },
                ].map((item) => (
                  <div key={item.label} className="terminal-metric">
                    <span>{item.label}</span>
                    <span>{item.value}</span>
                  </div>
                ))}
              </div>
              <span className="terminal-cursor" />
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
