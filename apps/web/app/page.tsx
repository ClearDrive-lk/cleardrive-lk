import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { AuctionTicker } from "@/components/ui/ticker";
import {
  Search,
<<<<<<< HEAD
=======
  ShieldCheck,
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
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
  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-[#FE7743] selection:text-black font-sans flex flex-col">
      {/* --- NAVIGATION --- */}
      <nav className="border-b border-white/10 bg-[#050505]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="font-bold text-xl tracking-tighter flex items-center gap-2">
            <div className="w-8 h-8 bg-[#FE7743]/10 border border-[#FE7743]/20 rounded-md flex items-center justify-center">
              <Terminal className="w-4 h-4 text-[#FE7743]" />
            </div>
            ClearDrive<span className="text-[#FE7743]">.lk</span>
          </div>
          <div className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
            <Link
              href="#"
              className="hover:text-white transition-colors flex items-center gap-2"
            >
              Auctions{" "}
              <Badge
                variant="outline"
                className="text-[10px] border-[#FE7743]/20 text-[#FE7743] h-4 px-1"
              >
                LIVE
              </Badge>
            </Link>
            <Link href="#" className="hover:text-white transition-colors">
              Logistics
            </Link>
            <Link href="#" className="hover:text-white transition-colors">
              Tax Calculator
            </Link>
          </div>
          <div className="flex gap-4">
            <Link href="/login">
              <Button
                variant="ghost"
                className="text-gray-400 hover:text-white hover:bg-white/5 font-mono"
              >
                Sign In
              </Button>
            </Link>
            <Link href="/register">
              <Button className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90 font-bold">
                Get Access
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* --- HERO SECTION --- */}
      <section className="relative pt-20 pb-20 px-6 overflow-hidden flex-1 flex flex-col justify-center">
        <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#FE7743]/5 rounded-[100%] blur-[120px] pointer-events-none" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

        <div className="relative z-10 max-w-5xl mx-auto text-center space-y-8">
          <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-[#FE7743] animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FE7743] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#FE7743]"></span>
            </span>
            DIRECT MARKET ACCESS (DMA) :: v2.4.0
          </div>

          <h1 className="text-5xl md:text-8xl font-bold tracking-tighter text-white leading-[0.9]">
            IMPORT{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FE7743] to-orange-200">
              DIRECT.
            </span>
            <br />
            PAY ZERO MARKUP.
          </h1>

          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
            The first{" "}
            <span className="text-white font-medium">Direct-to-Consumer</span>{" "}
            import terminal in Sri Lanka. Access USS Tokyo, JAA, and CAI
            auctions in real-time.
            <span className="block mt-2 text-gray-500 text-sm font-mono">
<<<<<<< HEAD
              AUTOMATED CIF CALCULATION // INSTANT LC OPENING // CLEARING @
=======
              AUTOMATED CIF CALCULATION INSTANT LC OPENING // CLEARING @
>>>>>>> 0162e2e977b9ad541379e696dbf240da260a5f98
              HAMBANTOTA
            </span>
          </p>

          <div className="max-w-2xl mx-auto mt-12 p-1 rounded-xl bg-gradient-to-b from-white/10 to-white/5 backdrop-blur-xl border border-white/10 shadow-2xl">
            <div className="relative flex items-center bg-[#0A0A0A] rounded-lg p-1.5">
              <Search className="w-5 h-5 text-gray-500 ml-4" />
              <Input
                className="border-0 bg-transparent text-white placeholder:text-gray-600 focus-visible:ring-0 h-12 text-lg font-mono"
                placeholder="Search Chassis ID (e.g. CBA-ZE2-102030)..."
              />
              <div className="hidden md:flex items-center gap-2 pr-4">
                <Badge
                  variant="secondary"
                  className="bg-[#1A1A1A] text-gray-500 hover:bg-[#1A1A1A]"
                >
                  VIN
                </Badge>
                <Badge
                  variant="secondary"
                  className="bg-[#1A1A1A] text-gray-500 hover:bg-[#1A1A1A]"
                >
                  Lot #
                </Badge>
              </div>
              <Button className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90 font-bold h-11 px-8 rounded-md">
                Track Vehicle
              </Button>
            </div>
          </div>

          <div className="pt-8 flex flex-wrap justify-center gap-6 text-sm text-gray-500 font-mono">
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#FE7743]" /> VERIFIED
              CONDITION SHEETS
            </span>
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#FE7743]" /> REAL-TIME
              ODOMETER CHECK
            </span>
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#FE7743]" /> JEVIC
              CERTIFIED
            </span>
          </div>
        </div>
      </section>

      {/* --- LIVE TICKER --- */}
      <AuctionTicker />

      {/* --- LIVE STATS STRIP --- */}
      <div className="border-b border-white/10 bg-[#0A0A0A]">
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
              className="p-8 flex items-start gap-4 group hover:bg-white/5 transition-colors cursor-default"
            >
              <div className="mt-1 p-2 rounded-md bg-[#FE7743]/10 text-[#FE7743] group-hover:bg-[#FE7743] group-hover:text-black transition-colors">
                <stat.icon className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xl font-bold text-white tracking-tight">
                  {stat.value}
                </div>
                <div className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-1">
                  {stat.label}
                </div>
                <div className="text-[10px] text-gray-600 font-mono mt-1">
                  {stat.sub}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* --- CATEGORIES --- */}
      <section className="py-24 px-6 bg-[#050505]">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-end mb-12 gap-4">
            <div>
              <h2 className="text-3xl font-bold text-white tracking-tight">
                Browse Inventory
              </h2>
              <p className="text-gray-400 mt-2 text-lg">
                Select your vehicle class to view live auction data.
              </p>
            </div>
            <Button
              variant="outline"
              className="border-white/10 hover:bg-white/5 hover:text-white gap-2"
            >
              View All 45,000+ Units <ArrowRight className="w-4 h-4" />
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              {
                name: "Sedan / Saloon",
                count: "12,200+",
                icon: Car,
                bg: "from-blue-900/20 to-purple-900/20",
                code: "CAT-SDN",
              },
              {
                name: "SUVs & 4x4",
                count: "8,150+",
                icon: Anchor,
                bg: "from-orange-900/20 to-red-900/20",
                code: "CAT-SUV",
              },
              {
                name: "Commercial / Van",
                count: "2,300+",
                icon: Truck,
                bg: "from-green-900/20 to-emerald-900/20",
                code: "CAT-COM",
              },
              {
                name: "Kei & Compact",
                count: "5,600+",
                icon: Zap,
                bg: "from-yellow-900/20 to-orange-900/20",
                code: "CAT-KEI",
              },
            ].map((cat, i) => (
              <div
                key={i}
                className={`group relative h-72 rounded-xl border border-white/10 bg-gradient-to-br ${cat.bg} p-6 flex flex-col justify-between overflow-hidden hover:border-[#FE7743]/50 transition-all cursor-pointer`}
              >
                <div className="absolute inset-0 bg-black/40 group-hover:bg-transparent transition-colors duration-500" />

                <div className="relative z-10 flex justify-between items-start">
                  <Badge
                    variant="outline"
                    className="border-white/20 text-white/50 font-mono text-[10px]"
                  >
                    {cat.code}
                  </Badge>
                  <cat.icon className="w-8 h-8 text-white/40 group-hover:text-white transition-colors" />
                </div>

                <div className="relative z-10">
                  <h3 className="text-2xl font-bold text-white group-hover:translate-x-1 transition-transform">
                    {cat.name}
                  </h3>
                  <p className="text-sm text-gray-400 mt-1 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#FE7743] animate-pulse" />
                    {cat.count} Live Units
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- HOW IT WORKS --- */}
      <section className="py-24 px-6 border-t border-white/5 relative bg-[#020202]">
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="text-center mb-16 max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold text-white tracking-tight">
              The ClearDrive Process
            </h2>
            <p className="text-gray-400 mt-4 text-lg">
              We&apos;ve automated the middleman out of existence. From the
              auction floor in Tokyo to your garage in Colombo.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            <div className="hidden md:block absolute top-12 left-[16%] right-[16%] h-px bg-gradient-to-r from-transparent via-[#FE7743]/50 to-transparent border-t border-dashed border-white/20 z-0" />

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
                className="relative z-10 flex flex-col items-center text-center"
              >
                <div className="w-24 h-24 rounded-full bg-[#0A0A0A] border border-white/10 flex items-center justify-center mb-6 shadow-2xl relative group">
                  <div className="absolute inset-0 bg-[#FE7743]/10 rounded-full blur-xl group-hover:bg-[#FE7743]/20 transition-all" />
                  <span className="text-2xl font-bold text-white font-mono">
                    {item.step}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">
                  {item.title}
                </h3>
                <p className="text-gray-400 leading-relaxed text-sm max-w-xs">
                  {item.desc}
                </p>
                <Badge
                  variant="secondary"
                  className="mt-4 bg-[#1A1A1A] text-[#FE7743] border border-[#FE7743]/20 font-mono"
                >
                  {item.stat}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- FOOTER --- */}
      <footer className="border-t border-white/10 py-16 bg-[#050505]">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12">
          <div className="space-y-6">
            <div className="font-bold text-xl tracking-tighter text-white flex items-center gap-2">
              <Terminal className="w-5 h-5 text-[#FE7743]" />
              ClearDrive<span className="text-[#FE7743]">.lk</span>
            </div>
            <p className="text-sm text-gray-500 leading-relaxed">
              The first tech-enabled vehicle import platform in Sri Lanka.
              Replacing brokers with code, ensuring 100% financial transparency.
            </p>
          </div>

          <div>
            <h4 className="font-bold text-white mb-6">Market Data</h4>
            <ul className="space-y-3 text-sm text-gray-500 font-mono">
              <li className="hover:text-[#FE7743] cursor-pointer flex items-center gap-2">
                {" "}
                <ArrowRight className="w-3 h-3" /> USS Tokyo Live
              </li>
              <li className="hover:text-[#FE7743] cursor-pointer flex items-center gap-2">
                {" "}
                <ArrowRight className="w-3 h-3" /> JAA Condition Sheets
              </li>
              <li className="hover:text-[#FE7743] cursor-pointer flex items-center gap-2">
                {" "}
                <ArrowRight className="w-3 h-3" /> Cost Calculator
              </li>
              <li className="hover:text-[#FE7743] cursor-pointer flex items-center gap-2">
                {" "}
                <ArrowRight className="w-3 h-3" /> Past Sales (2025)
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-white mb-6">Company</h4>
            <ul className="space-y-3 text-sm text-gray-500">
              <li className="hover:text-[#FE7743] cursor-pointer">About Us</li>
              <li className="hover:text-[#FE7743] cursor-pointer">Careers</li>
              <li className="hover:text-[#FE7743] cursor-pointer">
                Terms of Service
              </li>
              <li className="hover:text-[#FE7743] cursor-pointer">
                Privacy Policy
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-white mb-6">Support</h4>
            <ul className="space-y-3 text-sm text-gray-500">
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
        <div className="max-w-7xl mx-auto px-6 mt-16 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center text-xs text-gray-600 font-mono">
          <p>© 2026 CLEARDRIVE INC. ALL RIGHTS RESERVED.</p>
          <p>DESIGNED FOR HIGH-FREQUENCY TRADING</p>
        </div>
      </footer>
    </div>
  );
}
