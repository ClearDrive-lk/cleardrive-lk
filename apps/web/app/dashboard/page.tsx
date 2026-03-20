"use client";

import AuthGuard from "@/components/auth/AuthGuard";
import { useAppSelector } from "@/lib/store/store";
import Link from "next/link";
import {
  Package,
  Car,
  User,
  FileText,
  ShieldCheck,
  TrendingUp,
  CheckCircle2,
  Ship,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useLogout } from "@/lib/hooks/useLogout";
import { normalizeRole } from "@/lib/roles";
import ThemeToggle from "@/components/ui/theme-toggle";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import { useRef, useEffect } from "react";

/**
 * Dashboard Page - Exact homepage template with enhanced interactivity
 */
export default function DashboardPage() {
  const { user } = useAppSelector((state) => state.auth);
  const { logout, isLoading } = useLogout();
  const role = normalizeRole(user?.role);
  const showExporterEntry = role === "EXPORTER" || role === "ADMIN";

  const heroRef = useRef<HTMLElement | null>(null);
  const heroRafRef = useRef<number | null>(null);

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
    return () => {
      if (heroRafRef.current !== null) {
        cancelAnimationFrame(heroRafRef.current);
      }
    };
  }, []);

  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans flex flex-col">
        {/* --- NAVIGATION (Same as Homepage) --- */}
        <nav className="border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md sticky top-0 z-50">
          <div className="cd-container h-16 flex items-center justify-between">
            <Link
              href="/"
              className="font-bold text-xl tracking-tighter flex items-center gap-2 group"
            >
              <BrandMark className="h-8 w-8 rounded-md border border-[#62929e]/20 bg-[#62929e]/10 group-hover:bg-[#62929e]/20 transition-colors" />
              <BrandWordmark />
            </Link>
            <div className="hidden md:flex gap-8 text-sm font-medium text-[#546a7b]">
              <Link
                href="/dashboard"
                className="text-[#393d3f] transition-colors flex items-center gap-2"
              >
                Dashboard{" "}
                <Badge
                  variant="outline"
                  className="text-[10px] border-[#62929e]/20 text-[#62929e] h-4 px-1"
                >
                  ACTIVE
                </Badge>
              </Link>
              <Link
                href="/dashboard/orders"
                className="hover:text-[#393d3f] transition-colors"
              >
                Orders
              </Link>
              <Link
                href="/dashboard/vehicles"
                className="hover:text-[#393d3f] transition-colors"
              >
                Vehicles
              </Link>
              <Link
                href="/dashboard/kyc"
                className="hover:text-[#393d3f] transition-colors"
              >
                KYC
              </Link>
              <Link
                href="/dashboard/shipping"
                className="hover:text-[#393d3f] transition-colors"
              >
                Shipping
              </Link>
              <Link
                href="/dashboard/profile"
                className="hover:text-[#393d3f] transition-colors"
              >
                Profile
              </Link>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <Button
                onClick={logout}
                disabled={isLoading}
                className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
              >
                {isLoading ? "Signing Out..." : "Sign Out"}
              </Button>
            </div>
          </div>
        </nav>

        {/* Content Section with Interactive Spotlight */}
        <section
          ref={heroRef}
          onMouseMove={handleHeroMove}
          onMouseLeave={resetHeroSpotlight}
          className="relative pt-20 pb-20 overflow-hidden flex-1 flex flex-col group"
        >
          {/* Spotlight & Background Effects */}
          <div className="hero-spotlight absolute inset-0 pointer-events-none" />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
          <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#62929e]/5 rounded-[100%] blur-[120px] pointer-events-none animate-float-slower transition-transform duration-500 group-hover:scale-[1.02]" />

          <div className="relative z-10 cd-container">
            <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-[#c6c5b9]/20 border border-[#546a7b]/65 text-xs font-mono text-[#62929e] mb-8 animate-in fade-in slide-in-from-bottom-4 duration-1000 shadow-sm backdrop-blur-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#62929e] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#62929e]"></span>
              </span>
              DASHBOARD TERMINAL :: {new Date().toLocaleDateString()}
            </div>

            <h1 className="text-5xl md:text-8xl font-bold tracking-tighter text-[#393d3f] leading-[0.9] mb-6 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-100">
              WELCOME{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#62929e] to-[#c6c5b9] animate-shimmer bg-[size:200%_auto]">
                {user?.name?.toUpperCase() || "USER"}.
              </span>
            </h1>

            <p className="text-lg md:text-xl text-[#546a7b] max-w-2xl mb-12 animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-200">
              Your personal import terminal dashboard. Monitor clearances, track
              shipments, and manage orders in real-time.
            </p>

            {showExporterEntry && (
              <div className="mb-10 flex flex-wrap items-center gap-4 animate-in fade-in duration-1000 delay-300">
                <Button
                  asChild
                  className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold gap-2 shadow-[0_8px_20px_rgba(98,146,158,0.25)] hover:shadow-[0_12px_28px_rgba(98,146,158,0.4)] transition-all"
                >
                  <Link href="/exporter">
                    <Ship className="w-4 h-4" />
                    Open Exporter Terminal
                  </Link>
                </Button>
                <Badge
                  variant="outline"
                  className="border-[#62929e]/30 text-[#62929e] font-mono bg-[#62929e]/5"
                >
                  EXPORTER ACCESS
                </Badge>
              </div>
            )}

            {/* Quick Links Grid - High Interactivity */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 mb-16 animate-in fade-in slide-in-from-bottom-16 duration-1000 delay-300">
              {[
                {
                  title: "Orders",
                  href: "/dashboard/orders",
                  icon: Package,
                  code: "ORD-SYS",
                },
                {
                  title: "Vehicles",
                  href: "/dashboard/vehicles",
                  icon: Car,
                  code: "VEH-TRK",
                },
                {
                  title: "Profile",
                  href: "/dashboard/profile",
                  icon: User,
                  code: "USR-ACC",
                },
                {
                  title: "KYC",
                  href: "/dashboard/kyc",
                  icon: ShieldCheck,
                  code: "KYC-ID",
                },
                {
                  title: "Shipping",
                  href: "/dashboard/shipping",
                  icon: Package,
                  code: "SHP-SUB",
                },
                {
                  title: "Documents",
                  href: "/dashboard/documents",
                  icon: FileText,
                  code: "DOC-MGT",
                },
              ].map((item, i) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={i}
                    href={item.href}
                    className="group relative min-h-[16rem] rounded-2xl border border-[#546a7b]/70 bg-[linear-gradient(140deg,rgba(253,253,255,0.85),rgba(198,197,185,0.35))] dark:bg-[linear-gradient(140deg,rgba(28,38,44,0.92),rgba(15,20,23,0.85))] p-6 flex flex-col justify-between overflow-hidden transition-all duration-300 cursor-pointer hover-tilt shadow-[0_12px_28px_rgba(0,0,0,0.08)] hover:shadow-[0_26px_60px_rgba(15,23,42,0.24)] hover:border-[#62929e]/60 z-10"
                  >
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(98,146,158,0.18),transparent_55%)] opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                    <div className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="absolute inset-0 bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.15),transparent)] animate-shimmer" />
                    </div>

                    <div className="relative z-10 flex justify-between items-start">
                      <Badge
                        variant="outline"
                        className="border-[#546a7b]/65 text-[#393d3f]/60 font-mono text-[10px] bg-[#fdfdff]/40 backdrop-blur"
                      >
                        {item.code}
                      </Badge>
                      <div className="h-10 w-10 rounded-xl border border-[#546a7b]/50 bg-[#fdfdff]/50 backdrop-blur flex items-center justify-center shadow-[0_4px_12px_rgba(0,0,0,0.05)] group-hover:border-[#62929e]/60 transition-colors">
                        <Icon className="w-5 h-5 text-[#393d3f]/60 group-hover:text-[#393d3f] transition-colors" />
                      </div>
                    </div>

                    <div className="relative z-10">
                      <h3 className="text-2xl font-bold text-[#393d3f] group-hover:translate-x-1 transition-transform">
                        {item.title}
                      </h3>
                      <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-[#62929e]/30 bg-[#62929e]/10 px-3 py-1 text-[10px] uppercase font-semibold text-[#393d3f] shadow-[0_4px_12px_rgba(15,23,42,0.08)]">
                        <span className="h-1.5 w-1.5 rounded-full bg-[#62929e] animate-pulse" />
                        Live Access
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>

            {/* Stats Bar */}
            <div className="border-y border-[#546a7b]/65 bg-[#fdfdff] rounded-2xl overflow-hidden shadow-[0_8px_30px_rgba(0,0,0,0.04)] animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-500">
              <div className="grid grid-cols-2 lg:grid-cols-4 divide-x divide-white/5 dark:divide-[#546a7b]/30">
                {[
                  {
                    label: "Active Orders",
                    value: "0",
                    icon: Package,
                    sub: "In Progress",
                  },
                  {
                    label: "In Transit",
                    value: "0",
                    icon: Car,
                    sub: "En Route",
                  },
                  {
                    label: "Completed",
                    value: "0",
                    icon: TrendingUp,
                    sub: "This Month",
                  },
                  {
                    label: "Avg. Time",
                    value: "~14 Days",
                    icon: CheckCircle2,
                    sub: "Clearance",
                  },
                ].map((stat, i) => (
                  <div
                    key={i}
                    className="relative p-6 lg:p-8 flex flex-col sm:flex-row items-start sm:items-center gap-4 group hover-glow bg-transparent transition-all duration-300 cursor-default"
                  >
                    <div className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(98,146,158,0.12),transparent_70%)]" />
                    </div>
                    <div className="relative z-10 p-2.5 rounded-xl bg-[#62929e]/10 border border-[#62929e]/20 text-[#62929e] group-hover:bg-[#62929e] group-hover:text-[#fdfdff] group-hover:scale-110 transition-all shadow-sm">
                      <stat.icon className="w-5 h-5" />
                    </div>
                    <div className="relative z-10">
                      <div className="text-2xl font-bold text-[#393d3f] tracking-tight group-hover:text-[#62929e] transition-colors">
                        {stat.value}
                      </div>
                      <div className="text-[10px] text-[#546a7b] font-semibold uppercase tracking-widest mt-0.5">
                        {stat.label}
                      </div>
                      <div className="text-[9px] text-[#393d3f]/80 font-mono mt-1 bg-[#c6c5b9]/20 px-2 py-0.5 rounded-sm w-fit">
                        {stat.sub}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </AuthGuard>
  );
}
