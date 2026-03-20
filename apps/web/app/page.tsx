"use client";

import Link from "next/link";
import { IBM_Plex_Sans, Playfair_Display } from "next/font/google";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useAppSelector } from "@/lib/store/store";
import { getAccessToken, getRefreshToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { AuctionTicker } from "@/components/ui/ticker";
import ThemeToggle from "@/components/ui/theme-toggle";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import {
  Search,
  Zap,
  Globe,
  TrendingUp,
  Car,
  Truck,
  Anchor,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";

const plex = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});
const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const AUCTION_LOT_CELLS = Array.from({ length: 20 }, (_, index) => index);

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const hasSession = Boolean(getAccessToken() || getRefreshToken());
  const [searchTerm, setSearchTerm] = useState("");
  const [mounted, setMounted] = useState(false);
  const heroRef = useRef<HTMLElement | null>(null);
  const heroRafRef = useRef<number | null>(null);
  const laneSurfaceRef = useRef<HTMLDivElement | null>(null);
  const laneRafRef = useRef<number | null>(null);
  const handleSearch = () => {
    const trimmed = searchTerm.trim();
    if (!trimmed) return;
    router.push(`/dashboard/vehicles?search=${encodeURIComponent(trimmed)}`);
  };

  const handleHeroMove = (event: React.MouseEvent<HTMLElement>) => {
    const node = heroRef.current;
    if (!node) return;
    const rect = node.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;
    if (heroRafRef.current !== null) {
      cancelAnimationFrame(heroRafRef.current);
    }
    heroRafRef.current = requestAnimationFrame(() => {
      node.style.setProperty("--mx", `${x}%`);
      node.style.setProperty("--my", `${y}%`);
    });
  };

  const resetHeroSpotlight = () => {
    const node = heroRef.current;
    if (!node) return;
    node.style.setProperty("--mx", "50%");
    node.style.setProperty("--my", "20%");
  };

  useEffect(() => {
    setMounted(true);
    return () => {
      if (heroRafRef.current !== null) {
        cancelAnimationFrame(heroRafRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const duration = 7500;

    const animateLane = (timestamp: number) => {
      const progress = (timestamp % duration) / duration;
      laneSurfaceRef.current?.style.setProperty(
        "--lane-progress",
        progress.toFixed(4),
      );
      laneRafRef.current = requestAnimationFrame(animateLane);
    };

    laneRafRef.current = requestAnimationFrame(animateLane);

    return () => {
      if (laneRafRef.current !== null) {
        cancelAnimationFrame(laneRafRef.current);
      }
    };
  }, []);

  const handleLaneMove = (event: React.MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    if (!rect.width) return;
    const focusX = ((event.clientX - rect.left) / rect.width) * 100;
    event.currentTarget.style.setProperty("--lane-focus", `${focusX}%`);
  };

  const resetLaneMove = (event: React.MouseEvent<HTMLDivElement>) => {
    event.currentTarget.style.setProperty("--lane-focus", "50%");
  };

  const navHref =
    mounted && (isAuthenticated || hasSession) ? "/dashboard" : "/";

  return (
    <div
      className={`${plex.className} min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] flex flex-col`}
    >
      {/* --- NAVIGATION --- */}
      <nav className="border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="cd-container h-16 flex items-center justify-between">
          <Link
            href={navHref}
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
              className="hover:text-[#393d3f] transition-colors"
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

      {/* --- HERO SECTION --- */}
      <section
        ref={heroRef}
        onMouseMove={handleHeroMove}
        onMouseLeave={resetHeroSpotlight}
        className="relative pt-20 pb-24 overflow-hidden flex-1 flex flex-col justify-center group"
      >
        <div className="hero-spotlight absolute inset-0 pointer-events-none" />
        <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#62929e]/8 rounded-[100%] blur-[120px] pointer-events-none animate-float-slower transition-transform duration-500 group-hover:scale-[1.02]" />
        <div className="absolute -top-24 right-[-160px] w-[420px] h-[420px] rounded-full border border-[#62929e]/25 animate-orbit-slow pointer-events-none transition-transform duration-500 group-hover:translate-y-4" />
        <div className="absolute -bottom-32 left-[-140px] w-[340px] h-[340px] rounded-full border border-[#62929e]/20 animate-orbit-slow pointer-events-none transition-transform duration-500 group-hover:-translate-y-4" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 z-[2] hidden lg:block opacity-45"
        >
          <div
            className="absolute inset-0 opacity-90"
            style={{
              background:
                "radial-gradient(340px circle at var(--mx, 50%) var(--my, 20%), rgba(98,146,158,0.08), transparent 66%)",
            }}
          />

          <div
            className="absolute left-[5%] top-[13%] h-[17.5rem] w-[28rem] rounded-[1.8rem] border border-[#62929e]/30 shadow-[0_24px_50px_rgba(6,12,18,0.24)] backdrop-blur-[2px] transition-transform duration-300 group-hover:-translate-y-1"
            style={{ backgroundColor: "rgba(253,253,255,0.02)" }}
          >
            <div className="absolute inset-x-4 top-5 h-px bg-gradient-to-r from-transparent via-[#62929e]/55 to-transparent" />
            <div className="absolute inset-x-4 bottom-5 h-px bg-gradient-to-r from-transparent via-[#62929e]/40 to-transparent" />
            <svg
              viewBox="0 0 520 260"
              className="absolute inset-0 h-full w-full opacity-90"
            >
              <defs>
                <linearGradient id="chassisStroke" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="rgba(198,197,185,0.64)" />
                  <stop offset="55%" stopColor="rgba(98,146,158,0.86)" />
                  <stop offset="100%" stopColor="rgba(84,106,123,0.7)" />
                </linearGradient>
              </defs>
              <path
                d="M56 170 L102 170 L138 127 L220 118 L260 94 L343 94 L392 123 L448 131 L468 151 L468 170 L442 170 L420 170 L400 170 L384 170 L136 170 L112 170 L90 170 L56 170 Z"
                fill="rgba(15,25,32,0.2)"
                stroke="url(#chassisStroke)"
                strokeWidth="2.2"
              />
              <path
                d="M170 127 L214 118 L260 95 L333 95 L366 119 L188 120 Z"
                fill="rgba(98,146,158,0.11)"
                stroke="rgba(198,197,185,0.45)"
                strokeWidth="1.3"
              />
              <line
                x1="136"
                y1="170"
                x2="136"
                y2="128"
                stroke="rgba(98,146,158,0.5)"
                strokeWidth="1.2"
              />
              <line
                x1="384"
                y1="170"
                x2="384"
                y2="124"
                stroke="rgba(98,146,158,0.5)"
                strokeWidth="1.2"
              />
              <circle
                cx="168"
                cy="170"
                r="31"
                fill="rgba(15,20,23,0.34)"
                stroke="rgba(198,197,185,0.64)"
                strokeWidth="2"
              />
              <circle
                cx="168"
                cy="170"
                r="13"
                fill="rgba(98,146,158,0.4)"
                stroke="rgba(198,197,185,0.45)"
              />
              <circle
                cx="353"
                cy="170"
                r="31"
                fill="rgba(15,20,23,0.34)"
                stroke="rgba(198,197,185,0.64)"
                strokeWidth="2"
              />
              <circle
                cx="353"
                cy="170"
                r="13"
                fill="rgba(98,146,158,0.4)"
                stroke="rgba(198,197,185,0.45)"
              />
              <circle
                cx="220"
                cy="118"
                r="4"
                fill="rgba(198,197,185,0.82)"
                className="animate-pulse"
              />
              <circle
                cx="343"
                cy="94"
                r="4"
                fill="rgba(198,197,185,0.82)"
                className="animate-pulse"
                style={{ animationDelay: "0.5s" }}
              />
              <path
                d="M102 170 C147 124, 309 71, 448 131"
                fill="none"
                stroke="rgba(98,146,158,0.42)"
                strokeWidth="1.4"
                strokeDasharray="5 6"
              />
            </svg>
            <div className="absolute left-[42%] top-[52%] h-20 w-20 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#62929e]/30 animate-[spin_12s_linear_infinite]" />
          </div>

          <div
            className="absolute right-[6%] top-[18%] h-[21rem] w-[20rem] rounded-[1.7rem] border border-[#546a7b]/45 p-4 shadow-[0_22px_46px_rgba(7,12,18,0.24)] backdrop-blur-[2px] transition-transform duration-300 group-hover:translate-y-1"
            style={{ backgroundColor: "rgba(253,253,255,0.025)" }}
          >
            <div className="absolute inset-0 rounded-[1.7rem] bg-[radial-gradient(circle_at_20%_15%,rgba(98,146,158,0.2),transparent_45%)]" />
            <div className="relative grid grid-cols-4 gap-2">
              {AUCTION_LOT_CELLS.map((cell) => (
                <div
                  key={cell}
                  className="h-9 rounded-md border border-[#62929e]/30 bg-[#c6c5b9]/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.24)]"
                >
                  <div
                    className="h-full w-full rounded-md bg-gradient-to-r from-transparent via-[#62929e]/30 to-transparent animate-[pulse_2.7s_ease-in-out_infinite]"
                    style={{ animationDelay: `${(cell % 7) * 0.19}s` }}
                  />
                </div>
              ))}
            </div>
            <div className="absolute inset-x-6 bottom-6 h-12 rounded-full border border-[#62929e]/38 bg-[#62929e]/10">
              <div className="absolute left-3 top-1/2 h-6 w-6 -translate-y-1/2 rounded-full border border-[#c6c5b9]/70 bg-[#62929e]/45 shadow-[0_0_16px_rgba(98,146,158,0.52)] animate-[pulse_1.8s_ease-in-out_infinite]" />
              <div className="absolute left-0 top-1/2 h-0.5 w-full -translate-y-1/2 bg-[linear-gradient(90deg,transparent,rgba(198,197,185,0.68),transparent)]" />
            </div>
          </div>

          <div className="absolute left-1/2 top-[30%] h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#62929e]/40 transition-[left,top] duration-150" />
          <div
            className="absolute h-20 w-20 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#c6c5b9]/65 shadow-[0_0_26px_rgba(98,146,158,0.48)] transition-[left,top] duration-150"
            style={{ left: "var(--mx, 50%)", top: "var(--my, 20%)" }}
          >
            <div className="absolute inset-[17px] rounded-full bg-[#62929e]/45 animate-ping" />
          </div>

          <div
            className="absolute bottom-[12%] left-1/2 h-[7rem] w-[32rem] -translate-x-1/2 rounded-[3rem] border border-[#62929e]/28"
            style={{ backgroundColor: "rgba(198,197,185,0.03)" }}
          >
            <div className="absolute inset-x-8 top-1/2 h-px -translate-y-1/2 bg-[repeating-linear-gradient(90deg,rgba(198,197,185,0.55)_0_12px,transparent_12px_24px)]" />
            <div className="absolute left-10 top-1/2 h-4 w-4 -translate-y-1/2 rounded-full bg-[#62929e] shadow-[0_0_20px_rgba(98,146,158,0.7)] animate-[pulse_1.4s_ease-in-out_infinite]" />
            <div className="absolute right-10 top-1/2 h-4 w-4 -translate-y-1/2 rounded-full bg-[#c6c5b9] shadow-[0_0_20px_rgba(198,197,185,0.65)] animate-[pulse_1.7s_ease-in-out_infinite]" />
          </div>
        </div>

        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 bottom-[18%] z-[2] px-6 lg:hidden opacity-40"
        >
          <div
            className="mx-auto h-24 max-w-md rounded-3xl border border-[#62929e]/30 p-4 backdrop-blur-sm"
            style={{ backgroundColor: "rgba(253,253,255,0.03)" }}
          >
            <div className="grid grid-cols-6 gap-2">
              {AUCTION_LOT_CELLS.slice(0, 12).map((cell) => (
                <div
                  key={cell}
                  className="h-5 rounded-sm border border-[#62929e]/30 bg-[#c6c5b9]/12 animate-pulse"
                  style={{ animationDelay: `${(cell % 6) * 0.15}s` }}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="relative z-10 cd-container text-center space-y-8">
          <div className="absolute right-6 top-[-40px] hidden md:block rounded-full border border-[#546a7b]/40 bg-[#fdfdff]/80 px-4 py-2 text-[10px] font-mono text-[#546a7b] shadow-[0_12px_30px_rgba(0,0,0,0.12)] backdrop-blur animate-float-slow">
            LIVE PIPELINE :: TOKYO -&gt; HAMBANTOTA
          </div>
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-[#c6c5b9]/20 border border-[#546a7b]/65 text-xs font-mono text-[#62929e] animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#62929e] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#62929e]"></span>
            </span>
            Direct Market Access • Verified Live Feeds
          </div>

          <h1
            className={`${playfair.className} text-5xl md:text-7xl font-semibold tracking-tight text-[#393d3f] leading-[1.05]`}
          >
            Direct Import.{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#62929e] to-[#c6c5b9]">
              Zero Markup.
            </span>
            <br />
            Built for Sri Lanka.
          </h1>

          <p className="text-lg md:text-xl text-[#546a7b] max-w-2xl mx-auto leading-relaxed">
            Sri Lanka&apos;s direct-to-consumer vehicle import terminal. Access
            USS Tokyo, JAA, and CAI auctions in real time, with automated CIF
            calculation, instant LC opening, and clearance at Hambantota.
            <span className="block mt-3 text-[#546a7b] text-xs font-mono uppercase tracking-[0.2em]">
              CIF automation · instant LC · Hambantota clearance
            </span>
          </p>

          <div className="max-w-2xl mx-auto mt-12 p-1 rounded-xl bg-gradient-to-b from-white/15 to-white/5 backdrop-blur-xl border border-[#546a7b]/65 shadow-2xl group hover-glow focus-within:ring-1 focus-within:ring-[#62929e]/40">
            <div className="pointer-events-none absolute inset-0 rounded-xl ring-1 ring-[#62929e]/30 opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="pointer-events-none absolute inset-y-0 -left-1/3 w-1/2 bg-[linear-gradient(90deg,transparent,rgba(98,146,158,0.35),transparent)] animate-scanline" />
            <div className="relative flex items-center bg-[#fdfdff] rounded-lg p-1.5">
              <Search className="w-5 h-5 text-[#546a7b] ml-4" />
              <Input
                className="border-0 bg-transparent text-[#393d3f] placeholder:text-[#393d3f] focus-visible:ring-0 h-12 text-lg font-mono"
                placeholder="Search make, model, or chassis..."
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    handleSearch();
                  }
                }}
              />
              <div className="hidden md:flex items-center gap-2 pr-4">
                <Badge
                  variant="secondary"
                  className="bg-[#fdfdff] text-[#546a7b] hover:bg-[#c6c5b9]/20"
                >
                  Make/Model
                </Badge>
                <Badge
                  variant="secondary"
                  className="bg-[#fdfdff] text-[#546a7b] hover:bg-[#c6c5b9]/20"
                >
                  Chassis
                </Badge>
              </div>
              <Button
                onClick={handleSearch}
                className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold h-11 px-8 rounded-md"
              >
                Search Vehicles
              </Button>
            </div>
          </div>

          <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-4xl mx-auto">
            {[
              {
                label: "Live Bids",
                value: "2,148",
                icon: TrendingUp,
                tone: "from-[#62929e]/25 to-[#fdfdff]",
              },
              {
                label: "Duty Est.",
                value: "Auto-calculated",
                icon: CheckCircle2,
                tone: "from-[#546a7b]/20 to-[#fdfdff]",
              },
              {
                label: "Port Status",
                value: "Fast-Track",
                icon: Anchor,
                tone: "from-[#c6c5b9]/30 to-[#fdfdff]",
              },
            ].map((item) => (
              <div
                key={item.label}
                className={`group relative overflow-hidden rounded-xl border border-[#546a7b]/50 bg-gradient-to-br ${item.tone} p-4 text-left shadow-[0_12px_28px_rgba(0,0,0,0.12)] transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_18px_36px_rgba(0,0,0,0.18)]`}
              >
                <div className="absolute inset-0 bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.45),transparent)] opacity-0 group-hover:opacity-100 animate-shimmer" />
                <div className="relative flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#62929e]/10 text-[#62929e] group-hover:bg-[#62929e] group-hover:text-[#fdfdff] transition-colors">
                    <item.icon className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-[#546a7b]">
                      {item.label}
                    </p>
                    <p className="text-sm font-semibold text-[#393d3f]">
                      {item.value}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-8 flex flex-wrap justify-center gap-6 text-sm text-[#546a7b] font-mono">
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#62929e]" /> VERIFIED
              CONDITION SHEETS
            </span>
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#62929e]" /> REAL-TIME
              ODOMETER CHECK
            </span>
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#62929e]" /> JEVIC
              CERTIFIED
            </span>
          </div>
        </div>
      </section>

      {/* --- LIVE TICKER --- */}
      <AuctionTicker />

      {/* --- LIVE STATS STRIP --- */}
      <div className="border-b border-[#546a7b]/65 bg-[#fdfdff]">
        <div className="cd-container grid grid-cols-2 md:grid-cols-4 divide-x divide-white/10">
          {[
            {
              label: "Auction Access",
              value: "USS, JAA, CAI",
              icon: Globe,
              sub: "Direct API Link",
            },
            {
              label: "Exchange Rate",
              value: "2.25 LKR/JPY",
              icon: TrendingUp,
              sub: "Live Bank Rate",
            },
            {
              label: "Active Listings",
              value: "45,240+",
              icon: Car,
              sub: "Updated 2s ago",
            },
            {
              label: "Clearance Time",
              value: "~14 Days",
              icon: Zap,
              sub: "Fast-Track available",
            },
          ].map((stat, i) => (
            <div
              key={i}
              className="relative p-8 flex items-start gap-4 group hover:bg-[#c6c5b9]/20 transition-all duration-200 cursor-default hover-glow"
            >
              <div className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(98,146,158,0.12),transparent_60%)]" />
              </div>
              <div className="mt-1 p-2 rounded-md bg-[#62929e]/10 text-[#62929e] group-hover:bg-[#62929e] group-hover:text-[#fdfdff] transition-colors">
                <stat.icon className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xl font-bold text-[#393d3f] tracking-tight">
                  {stat.value}
                </div>
                <div className="text-xs text-[#546a7b] font-medium uppercase tracking-wider mt-1">
                  {stat.label}
                </div>
                <div className="text-[10px] text-[#393d3f] font-mono mt-1">
                  {stat.sub}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* --- LIVE ROUTE --- */}
      <section
        id="lane"
        className="relative py-12 bg-[#fdfdff] border-b border-[#546a7b]/40 overflow-hidden group"
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_30%,rgba(98,146,158,0.12),transparent_55%)] animate-halo" />
        <div className="cd-container relative">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-[#546a7b]">
                Live Shipping Lane
              </p>
              <h3 className="text-2xl font-bold text-[#393d3f]">
                Tokyo -&gt; Hambantota
              </h3>
              <p className="text-sm text-[#546a7b] mt-2">
                Real-time route tracking with automated clearance milestones.
              </p>
            </div>
            <div
              ref={laneSurfaceRef}
              onMouseMove={handleLaneMove}
              onMouseLeave={resetLaneMove}
              className="lane-surface relative w-full md:w-[55%] h-14 rounded-full border border-[#546a7b]/40 bg-[#fdfdff]/80 overflow-hidden transition-shadow duration-200 group-hover:shadow-[0_10px_30px_rgba(15,23,42,0.15)]"
            >
              <div className="absolute inset-0 bg-[repeating-linear-gradient(90deg,rgba(98,146,158,0.18)_0_6px,transparent_6px_16px)] opacity-60 lane-flow" />
              <div className="absolute inset-y-0 left-0 w-24 bg-[linear-gradient(90deg,transparent,rgba(98,146,158,0.18),transparent)] animate-scanline" />
              <div className="lane-vehicle-wrap absolute inset-y-0 left-0 w-full">
                <div className="lane-vehicle">
                  <div className="lane-vehicle-body" />
                  <div className="lane-vehicle-cab">
                    <Truck className="h-4 w-4" />
                  </div>
                  <span className="lane-wheel lane-wheel--front" />
                  <span className="lane-wheel lane-wheel--rear" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --- CATEGORIES --- */}
      <section id="inventory" className="py-24 bg-[#fdfdff]">
        <div className="cd-container">
          <div className="flex flex-col md:flex-row justify-between items-end mb-12 gap-4">
            <div>
              <h2 className="text-3xl font-bold text-[#393d3f] tracking-tight">
                Browse Inventory
              </h2>
              <p className="text-[#546a7b] mt-2 text-lg">
                Select your vehicle class to view live auction data.
              </p>
            </div>
            <Button
              asChild
              variant="outline"
              className="border-[#546a7b]/65 hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] gap-2"
            >
              <Link href="/dashboard/vehicles">
                View All 45,000+ Units <ArrowRight className="w-4 h-4" />
              </Link>
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              {
                name: "Sedan / Saloon",
                count: "12,200+",
                icon: Car,
                bg: "from-[#546a7b]/30 to-[#393d3f]/10",
                code: "CAT-SDN",
                tagline:
                  "Comfort-first daily drivers with tight auction spreads.",
                avgBid: "¥ 1.9M",
                eta: "Clearance ~4 days",
                popular: ["Toyota Premio", "Honda Civic", "Nissan Sylphy"],
              },
              {
                name: "SUVs & 4x4",
                count: "8,150+",
                icon: Anchor,
                bg: "from-[#62929e]/25 to-[#546a7b]/15",
                code: "CAT-SUV",
                tagline: "High-demand imports with strong resale velocity.",
                avgBid: "¥ 3.1M",
                eta: "Clearance ~6 days",
                popular: ["Toyota Harrier", "Honda Vezel", "Nissan X-Trail"],
              },
              {
                name: "Commercial / Van",
                count: "2,300+",
                icon: Truck,
                bg: "from-[#393d3f]/20 to-[#546a7b]/20",
                code: "CAT-COM",
                tagline: "Business-ready units with low maintenance cost.",
                avgBid: "¥ 2.4M",
                eta: "Clearance ~5 days",
                popular: ["Toyota Hiace", "Nissan NV200", "Mazda Bongo"],
              },
              {
                name: "Kei & Compact",
                count: "5,600+",
                icon: Zap,
                bg: "from-[#c6c5b9]/20 to-[#62929e]/15",
                code: "CAT-KEI",
                tagline: "Urban-friendly lots with excellent fuel economy.",
                avgBid: "¥ 980K",
                eta: "Clearance ~3 days",
                popular: ["Suzuki Alto", "Daihatsu Mira", "Honda N-Box"],
              },
            ].map((cat, i) => {
              const accents = [
                "from-[#62929e] via-[#546a7b] to-[#c6c5b9]",
                "from-[#c6c5b9] via-[#62929e] to-[#546a7b]",
                "from-[#546a7b] via-[#62929e] to-[#c6c5b9]",
                "from-[#62929e] via-[#c6c5b9] to-[#546a7b]",
              ];
              return (
                <div
                  key={i}
                  className={`group relative min-h-[22rem] rounded-2xl border border-[#546a7b]/70 bg-[linear-gradient(140deg,rgba(255,255,255,0.85),rgba(198,197,185,0.35))] dark:bg-[linear-gradient(140deg,rgba(28,38,44,0.92),rgba(15,20,23,0.85))] p-6 flex flex-col justify-between overflow-hidden transition-all duration-200 cursor-pointer hover-tilt shadow-[0_18px_40px_rgba(15,23,42,0.2)] hover:shadow-[0_26px_60px_rgba(15,23,42,0.26)] hover:border-[#62929e]/60`}
                >
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(98,146,158,0.18),transparent_55%)] opacity-70 group-hover:opacity-100 transition-opacity duration-300" />
                  <div
                    className={`absolute left-0 top-0 h-1 w-full bg-gradient-to-r ${accents[i % accents.length]}`}
                  />
                  <div className="absolute -right-16 -top-16 h-40 w-40 rounded-full bg-[#62929e]/15 blur-2xl opacity-70 group-hover:opacity-100 transition-opacity" />
                  <div className="absolute inset-x-4 bottom-4 h-1 rounded-full bg-[#c6c5b9]/40 overflow-hidden">
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 flex items-center gap-2 text-[#62929e] transition-transform duration-700 group-hover:translate-x-[65%]">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#62929e]" />
                      <Car className="h-4 w-4" />
                    </div>
                    <div className="absolute inset-y-0 left-0 w-12 bg-[linear-gradient(90deg,transparent,rgba(98,146,158,0.55),transparent)] opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  </div>
                  <div className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="absolute inset-0 bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.35),transparent)] animate-shimmer" />
                  </div>

                  <div className="relative z-10 flex justify-between items-start">
                    <Badge
                      variant="outline"
                      className="border-[#546a7b]/70 text-[#393d3f]/70 font-mono text-[10px] bg-[#fdfdff]/70 backdrop-blur"
                    >
                      {cat.code}
                    </Badge>
                    <div className="h-10 w-10 rounded-xl border border-[#546a7b]/50 bg-[#fdfdff]/70 backdrop-blur flex items-center justify-center shadow-[0_10px_25px_rgba(15,23,42,0.12)] group-hover:border-[#62929e]/60 transition-colors">
                      <cat.icon className="w-5 h-5 text-[#393d3f]/70 group-hover:text-[#393d3f] transition-colors" />
                    </div>
                  </div>

                  <div className="relative z-10 pb-8">
                    <p className="text-[10px] uppercase tracking-[0.4em] text-[#546a7b] font-mono mb-3">
                      Inventory Class
                    </p>
                    <h3 className="text-2xl font-bold text-[#393d3f] group-hover:translate-x-1 transition-transform">
                      {cat.name}
                    </h3>
                    <p className="text-sm text-[#546a7b] mt-2 leading-relaxed">
                      {cat.tagline}
                    </p>
                    <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-[#62929e]/30 bg-[#62929e]/10 px-3 py-1 text-xs font-semibold text-[#393d3f] shadow-[0_8px_18px_rgba(15,23,42,0.12)]">
                      <span className="h-2 w-2 rounded-full bg-[#62929e] animate-pulse" />
                      {cat.count} Live Units
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-[#546a7b] font-mono">
                      <div className="rounded-lg border border-[#546a7b]/30 bg-[#fdfdff]/70 px-3 py-2">
                        <p className="uppercase tracking-[0.2em] text-[9px] text-[#546a7b]">
                          Avg Bid
                        </p>
                        <p className="text-sm font-semibold text-[#393d3f]">
                          {cat.avgBid}
                        </p>
                      </div>
                      <div className="rounded-lg border border-[#546a7b]/30 bg-[#fdfdff]/70 px-3 py-2">
                        <p className="uppercase tracking-[0.2em] text-[9px] text-[#546a7b]">
                          Clearance
                        </p>
                        <p className="text-sm font-semibold text-[#393d3f]">
                          {cat.eta}
                        </p>
                      </div>
                    </div>
                    <div className="mt-4">
                      <p className="text-[10px] uppercase tracking-[0.28em] text-[#546a7b] font-mono">
                        Top Picks
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {cat.popular.map((item) => (
                          <span
                            key={item}
                            className="rounded-full border border-[#546a7b]/30 bg-[#fdfdff]/70 px-3 py-1 text-[11px] text-[#393d3f]"
                          >
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* --- HOW IT WORKS --- */}
      <section
        id="process"
        className="py-24 border-t border-[#546a7b]/40 relative bg-[#fdfdff]"
      >
        <div className="cd-container relative z-10">
          <div className="text-center mb-16 max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold text-[#393d3f] tracking-tight">
              The ClearDrive Process
            </h2>
            <p className="text-[#546a7b] mt-4 text-lg">
              We&apos;ve automated the middleman out of existence. From the
              auction floor in Tokyo to your garage in Colombo.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            <div className="hidden md:block absolute top-12 left-[16%] right-[16%] h-px bg-gradient-to-r from-transparent via-[#62929e]/50 to-transparent border-t border-dashed border-[#546a7b]/65 z-0" />

            {[
              {
                step: "01",
                title: "Bid & Win",
                desc: "Place a refundable deposit. Our agents at USS Tokyo inspect the car and bid on your behalf.",
                stat: "Deposit: 100k LKR",
              },
              {
                step: "02",
                title: "Pay & Ship",
                desc: "Receive the invoice. Pay CIF value directly to Japan. We handle LC opening and freight.",
                stat: "Turnaround: 48hrs",
              },
              {
                step: "03",
                title: "Clear & Deliver",
                desc: "Vehicle arrives at Hambantota. We handle Excise Duty, VAT, and Port clearance.",
                stat: "Customs: ~4 Days",
              },
            ].map((item, i) => (
              <div
                key={i}
                className="relative z-10 flex flex-col items-center text-center group hover-glow"
              >
                <div className="w-24 h-24 rounded-full bg-[#fdfdff] border border-[#546a7b]/65 flex items-center justify-center mb-6 shadow-2xl relative group-hover:-translate-y-1 transition-transform animate-float-slow">
                  <div className="absolute inset-0 bg-[#62929e]/10 rounded-full blur-xl group-hover:bg-[#62929e]/20 transition-all" />
                  <span className="text-2xl font-bold text-[#393d3f] font-mono">
                    {item.step}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-[#393d3f] mb-3">
                  {item.title}
                </h3>
                <p className="text-[#546a7b] leading-relaxed text-sm max-w-xs">
                  {item.desc}
                </p>
                <Badge
                  variant="secondary"
                  className="mt-4 bg-[#fdfdff] text-[#62929e] border border-[#62929e]/20 font-mono"
                >
                  {item.stat}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
