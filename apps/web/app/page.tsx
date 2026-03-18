"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAppSelector } from "@/lib/store/store";
import { getAccessToken, getRefreshToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { AuctionTicker } from "@/components/ui/ticker";
import ThemeToggle from "@/components/ui/theme-toggle";
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
  Terminal,
} from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const hasSession = Boolean(getAccessToken() || getRefreshToken());
  const [searchTerm, setSearchTerm] = useState("");
  const handleSearch = () => {
    const trimmed = searchTerm.trim();
    if (!trimmed) return;
    router.push(`/dashboard/vehicles?search=${encodeURIComponent(trimmed)}`);
  };

  return (
    <div className="min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans flex flex-col">
      {/* --- NAVIGATION --- */}
      <nav className="border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link
            href={isAuthenticated || hasSession ? "/dashboard" : "/"}
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
            <Link href="#" className="hover:text-[#393d3f] transition-colors">
              Logistics
            </Link>
            <Link href="#" className="hover:text-[#393d3f] transition-colors">
              Tax Calculator
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
      <section className="relative pt-20 pb-24 px-6 overflow-hidden flex-1 flex flex-col justify-center">
        <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#62929e]/8 rounded-[100%] blur-[120px] pointer-events-none animate-float-slower" />
        <div className="absolute -top-24 right-[-160px] w-[420px] h-[420px] rounded-full border border-[#62929e]/25 animate-orbit-slow pointer-events-none" />
        <div className="absolute -bottom-32 left-[-140px] w-[340px] h-[340px] rounded-full border border-[#62929e]/20 animate-orbit-slow pointer-events-none" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
        <div className="absolute right-[8%] top-[18%] hidden md:block rounded-full border border-[#546a7b]/40 bg-[#fdfdff]/80 px-4 py-2 text-[10px] font-mono text-[#546a7b] shadow-[0_12px_30px_rgba(0,0,0,0.12)] backdrop-blur animate-float-slow">
          LIVE PIPELINE :: TOKYO → HAMBANTOTA
        </div>

        <div className="relative z-10 max-w-5xl mx-auto text-center space-y-8">
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-[#c6c5b9]/20 border border-[#546a7b]/65 text-xs font-mono text-[#62929e] animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#62929e] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#62929e]"></span>
            </span>
            DIRECT MARKET ACCESS (DMA) :: v2.4.0
          </div>

          <h1 className="text-5xl md:text-8xl font-bold tracking-tighter text-[#393d3f] leading-[0.9]">
            IMPORT{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#62929e] to-[#c6c5b9]">
              DIRECT.
            </span>
            <br />
            PAY ZERO MARKUP.
          </h1>

          <p className="text-lg md:text-xl text-[#546a7b] max-w-2xl mx-auto leading-relaxed">
            The first{" "}
            <span className="text-[#393d3f] font-medium">Direct-to-Consumer</span>{" "}
            import terminal in Sri Lanka. Access USS Tokyo, JAA, and CAI
            auctions in real-time.
            <span className="block mt-2 text-[#546a7b] text-sm font-mono">
              AUTOMATED CIF CALCULATION // INSTANT LC OPENING // CLEARING @
              HAMBANTOTA
            </span>
          </p>

          <div className="max-w-2xl mx-auto mt-12 p-1 rounded-xl bg-gradient-to-b from-white/15 to-white/5 backdrop-blur-xl border border-[#546a7b]/65 shadow-2xl group">
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
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 divide-x divide-white/10">
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
              className="p-8 flex items-start gap-4 group hover:bg-[#c6c5b9]/20 transition-all duration-200 cursor-default hover:-translate-y-1 hover:shadow-[0_18px_36px_rgba(0,0,0,0.12)]"
            >
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

      {/* --- CATEGORIES --- */}
      <section className="py-24 px-6 bg-[#fdfdff]">
        <div className="max-w-7xl mx-auto">
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
              },
              {
                name: "SUVs & 4x4",
                count: "8,150+",
                icon: Anchor,
                bg: "from-[#62929e]/25 to-[#546a7b]/15",
                code: "CAT-SUV",
              },
              {
                name: "Commercial / Van",
                count: "2,300+",
                icon: Truck,
                bg: "from-[#393d3f]/20 to-[#546a7b]/20",
                code: "CAT-COM",
              },
              {
                name: "Kei & Compact",
                count: "5,600+",
                icon: Zap,
                bg: "from-[#c6c5b9]/20 to-[#62929e]/15",
                code: "CAT-KEI",
              },
            ].map((cat, i) => (
              <div
                key={i}
                className={`group relative h-72 rounded-xl border border-[#546a7b]/65 bg-gradient-to-br ${cat.bg} p-6 flex flex-col justify-between overflow-hidden hover:border-[#62929e]/50 transition-all duration-200 cursor-pointer hover:-translate-y-1 hover:shadow-[0_22px_45px_rgba(0,0,0,0.14)]`}
              >
                <div className="absolute inset-0 bg-[#fdfdff]/45 group-hover:bg-transparent transition-colors duration-500" />
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 bg-[radial-gradient(circle_at_top,rgba(98,146,158,0.18),transparent_55%)] transition-opacity duration-300" />

                <div className="relative z-10 flex justify-between items-start">
                  <Badge
                    variant="outline"
                    className="border-[#546a7b]/65 text-[#393d3f]/50 font-mono text-[10px]"
                  >
                    {cat.code}
                  </Badge>
                  <cat.icon className="w-8 h-8 text-[#393d3f]/40 group-hover:text-[#393d3f] transition-colors" />
                </div>

                <div className="relative z-10">
                  <h3 className="text-2xl font-bold text-[#393d3f] group-hover:translate-x-1 transition-transform">
                    {cat.name}
                  </h3>
                  <p className="text-sm text-[#546a7b] mt-1 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#62929e] animate-pulse" />
                    {cat.count} Live Units
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- HOW IT WORKS --- */}
      <section className="py-24 px-6 border-t border-[#546a7b]/40 relative bg-[#fdfdff]">
        <div className="max-w-7xl mx-auto relative z-10">
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
                className="relative z-10 flex flex-col items-center text-center group"
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

      {/* --- FOOTER --- */}
      <footer className="border-t border-[#546a7b]/65 py-16 bg-[#fdfdff]">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12">
          <div className="space-y-6">
            <div className="font-bold text-xl tracking-tighter text-[#393d3f] flex items-center gap-2">
              <Terminal className="w-5 h-5 text-[#62929e]" />
              ClearDrive<span className="text-[#62929e]">.lk</span>
            </div>
            <p className="text-sm text-[#546a7b] leading-relaxed">
              The first tech-enabled vehicle import platform in Sri Lanka.
              Replacing brokers with code, ensuring 100% financial transparency.
            </p>
          </div>

          <div>
            <h4 className="font-bold text-[#393d3f] mb-6">Market Data</h4>
            <ul className="space-y-3 text-sm text-[#546a7b] font-mono">
              <li className="hover:text-[#62929e] cursor-pointer flex items-center gap-2">
                {" "}
                <ArrowRight className="w-3 h-3" /> USS Tokyo Live
              </li>
              <li className="hover:text-[#62929e] cursor-pointer flex items-center gap-2">
                {" "}
                <ArrowRight className="w-3 h-3" /> JAA Condition Sheets
              </li>
              <li className="hover:text-[#62929e] cursor-pointer flex items-center gap-2">
                {" "}
                <ArrowRight className="w-3 h-3" /> Cost Calculator
              </li>
              <li className="hover:text-[#62929e] cursor-pointer flex items-center gap-2">
                {" "}
                <ArrowRight className="w-3 h-3" /> Past Sales (2025)
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-[#393d3f] mb-6">Company</h4>
            <ul className="space-y-3 text-sm text-[#546a7b]">
              <li className="hover:text-[#62929e] cursor-pointer">About Us</li>
              <li className="hover:text-[#62929e] cursor-pointer">Careers</li>
              <li className="hover:text-[#62929e] cursor-pointer">
                Terms of Service
              </li>
              <li className="hover:text-[#62929e] cursor-pointer">
                Privacy Policy
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-[#393d3f] mb-6">Support</h4>
            <ul className="space-y-3 text-sm text-[#546a7b]">
              <li className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500" /> Systems
                Operational
              </li>
              <li>Colombo 03, Sri Lanka</li>
              <li>support@cleardrive.lk</li>
              <li>+94 77 123 4567</li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 mt-16 pt-8 border-t border-[#546a7b]/40 flex flex-col md:flex-row justify-between items-center text-xs text-[#393d3f] font-mono">
          <p>© 2026 CLEARDRIVE INC. ALL RIGHTS RESERVED.</p>
          <p>DESIGNED FOR HIGH-FREQUENCY TRADING</p>
        </div>
      </footer>
    </div>
  );
}

