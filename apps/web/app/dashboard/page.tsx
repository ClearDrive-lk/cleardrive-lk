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
  ArrowUpRight,
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

  const quickActions = [
    {
      label: "Upload Pending Docs",
      detail: "Finish clearance paperwork first",
      href: "/dashboard/documents",
      icon: FileText,
      toneClass:
        "border-[#62929e]/45 bg-gradient-to-br from-[#62929e]/25 to-[#62929e]/8 hover:border-[#62929e]/70",
    },
    {
      label: "Plan Delivery Route",
      detail: "Set shipment details and destination",
      href: "/dashboard/shipping",
      icon: Ship,
      toneClass:
        "border-[#7d8fa3]/45 bg-gradient-to-br from-[#7d8fa3]/25 to-[#7d8fa3]/8 hover:border-[#7d8fa3]/70",
    },
    {
      label: "Complete Profile Setup",
      detail: "Confirm account and identity details",
      href: "/dashboard/profile",
      icon: User,
      toneClass:
        "border-[#c18f55]/45 bg-gradient-to-br from-[#c18f55]/25 to-[#c18f55]/8 hover:border-[#c18f55]/70",
    },
  ];

  const modules = [
    {
      title: "Orders",
      href: "/dashboard/orders",
      icon: Package,
      code: "ORD-SYS",
      description: "View payments, milestones, and shipment readiness.",
      status: "3 Milestones",
      cta: "Review Timeline",
      statusClass:
        "border-[#62929e]/35 bg-[#62929e]/12 text-[#2f5862] dark:text-[#8fdae8]",
    },
    {
      title: "Vehicles",
      href: "/dashboard/vehicles",
      icon: Car,
      code: "VEH-TRK",
      description: "Search inventory and shortlist eligible imports.",
      status: "Inventory Live",
      cta: "Explore Catalog",
      statusClass:
        "border-[#6b8fa9]/35 bg-[#6b8fa9]/14 text-[#36536a] dark:text-[#b6d5eb]",
    },
    {
      title: "Profile",
      href: "/dashboard/profile",
      icon: User,
      code: "USR-ACC",
      description: "Manage account details and identity information.",
      status: "2 Fields Pending",
      cta: "Finish Profile",
      statusClass:
        "border-[#c18f55]/35 bg-[#c18f55]/15 text-[#6b4a23] dark:text-[#f0cf9e]",
    },
    {
      title: "KYC",
      href: "/dashboard/kyc",
      icon: ShieldCheck,
      code: "KYC-ID",
      description: "Submit documents and monitor verification status.",
      status: "Verification Needed",
      cta: "Start Verification",
      statusClass:
        "border-[#b8778b]/35 bg-[#b8778b]/14 text-[#6f3f50] dark:text-[#f0bece]",
    },
    {
      title: "Shipping",
      href: "/dashboard/shipping",
      icon: Package,
      code: "SHP-SUB",
      description: "Provide delivery details and shipping instructions.",
      status: "No Route Confirmed",
      cta: "Set Delivery Plan",
      statusClass:
        "border-[#4d8f8a]/35 bg-[#4d8f8a]/14 text-[#2f5e5a] dark:text-[#93d6d1]",
    },
    {
      title: "Documents",
      href: "/dashboard/documents",
      icon: FileText,
      code: "DOC-MGT",
      description: "Upload and review required clearance paperwork.",
      status: "1 File Missing",
      cta: "Upload Documents",
      statusClass:
        "border-[#7182b5]/35 bg-[#7182b5]/14 text-[#3a4870] dark:text-[#c1cbf0]",
    },
  ];

  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#fdfdff] dark:bg-[#0f1417] text-[#1f2937] dark:text-[#edf2f7] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans flex flex-col">
        {/* --- NAVIGATION (Same as Homepage) --- */}
        <nav className="border-b border-[#546a7b]/45 dark:border-[#8fa3b1]/35 bg-[#fdfdff]/80 dark:bg-[#10191e]/80 backdrop-blur-md sticky top-0 z-50">
          <div className="cd-container h-16 flex items-center justify-between">
            <Link
              href="/"
              className="font-bold text-xl tracking-tighter flex items-center gap-2 group text-[#1f2937] dark:text-[#edf2f7]"
            >
              <BrandMark className="h-8 w-8 rounded-md border border-[#62929e]/20 bg-[#62929e]/10 group-hover:bg-[#62929e]/20 transition-colors" />
              <BrandWordmark />
            </Link>
            <div className="hidden md:flex gap-8 text-sm font-medium text-[#546a7b] dark:text-[#b8c7d4]">
              <Link
                href="/dashboard"
                className="text-[#1f2937] dark:text-[#edf2f7] transition-colors flex items-center gap-2"
              >
                Dashboard{" "}
                <Badge
                  variant="outline"
                  className="text-[10px] border-[#62929e]/30 text-[#3f7480] dark:text-[#88d6e4] h-4 px-1"
                >
                  ACTIVE
                </Badge>
              </Link>
              <Link
                href="/dashboard/orders"
                className="hover:text-[#2f4250] dark:hover:text-[#edf2f7] transition-colors"
              >
                Orders
              </Link>
              <Link
                href="/dashboard/vehicles"
                className="hover:text-[#2f4250] dark:hover:text-[#edf2f7] transition-colors"
              >
                Vehicles
              </Link>
              <Link
                href="/dashboard/kyc"
                className="hover:text-[#2f4250] dark:hover:text-[#edf2f7] transition-colors"
              >
                KYC
              </Link>
              <Link
                href="/dashboard/shipping"
                className="hover:text-[#2f4250] dark:hover:text-[#edf2f7] transition-colors"
              >
                Shipping
              </Link>
              <Link
                href="/dashboard/profile"
                className="hover:text-[#2f4250] dark:hover:text-[#edf2f7] transition-colors"
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

            <h1 className="text-5xl md:text-8xl font-bold tracking-tighter text-[#1f2937] dark:text-[#edf2f7] leading-[0.9] mb-6 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-100">
              WELCOME{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#62929e] to-[#c6c5b9] animate-shimmer bg-[size:200%_auto]">
                {user?.name?.toUpperCase() || "USER"}.
              </span>
            </h1>

            <p className="text-lg md:text-xl text-[#42596b] dark:text-[#bdcad4] max-w-2xl mb-12 animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-200">
              Your personal import terminal dashboard. Monitor clearances, track
              shipments, and manage orders in real-time.
            </p>

            <div className="mb-10 grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-3xl animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-250">
              {quickActions.map((action) => {
                const ActionIcon = action.icon;
                return (
                  <Link
                    key={action.href}
                    href={action.href}
                    className={`group rounded-xl border px-4 py-3 backdrop-blur-sm shadow-[0_6px_18px_rgba(0,0,0,0.06)] transition-all dark:shadow-[0_8px_20px_rgba(0,0,0,0.28)] ${action.toneClass}`}
                  >
                    <span className="flex items-start justify-between gap-3">
                      <span>
                        <span className="block text-sm font-semibold text-[#1f2937] dark:text-[#edf2f7]">
                          {action.label}
                        </span>
                        <span className="mt-1 block text-xs text-[#4f6576] dark:text-[#b6c4cf]">
                          {action.detail}
                        </span>
                      </span>
                      <span className="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[#fdfdff]/35 bg-[#fdfdff]/35 dark:bg-[#0f1417]/30">
                        <ActionIcon className="h-4 w-4 text-[#1f2937] dark:text-[#e6edf3]" />
                      </span>
                    </span>
                    <span className="mt-2 inline-flex items-center gap-1 text-[11px] uppercase tracking-[0.14em] font-semibold text-[#1f2937] dark:text-[#e6edf3]">
                      Continue
                      <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                    </span>
                  </Link>
                );
              })}
            </div>

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
              {modules.map((item, i) => {
                const Icon = item.icon;
                const centeredRowClass =
                  i === 4 ? "lg:col-start-2" : i === 5 ? "lg:col-start-3" : "";
                return (
                  <Link
                    key={i}
                    href={item.href}
                    className={`group relative min-h-[16rem] rounded-2xl border border-[#546a7b]/70 bg-[linear-gradient(140deg,rgba(253,253,255,0.85),rgba(198,197,185,0.35))] dark:bg-[linear-gradient(140deg,rgba(28,38,44,0.92),rgba(15,20,23,0.85))] p-6 flex flex-col justify-between overflow-hidden transition-all duration-300 cursor-pointer hover-tilt shadow-[0_12px_28px_rgba(0,0,0,0.08)] hover:shadow-[0_26px_60px_rgba(15,23,42,0.24)] hover:border-[#62929e]/60 z-10 ${centeredRowClass}`}
                  >
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(98,146,158,0.18),transparent_55%)] opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                    <div className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="absolute inset-0 bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.15),transparent)] animate-shimmer" />
                    </div>

                    <div className="relative z-10 flex justify-between items-start">
                      <Badge
                        variant="outline"
                        className="border-[#546a7b]/55 dark:border-[#b4c2ce]/40 text-[#324655] dark:text-[#c8d6e1] font-mono text-[10px] bg-[#fdfdff]/40 dark:bg-[#0f1417]/45 backdrop-blur"
                      >
                        {item.code}
                      </Badge>
                      <div className="h-10 w-10 rounded-xl border border-[#546a7b]/50 dark:border-[#93a7b8]/45 bg-[#fdfdff]/55 dark:bg-[#0f1417]/45 backdrop-blur flex items-center justify-center shadow-[0_4px_12px_rgba(0,0,0,0.05)] group-hover:border-[#62929e]/60 transition-colors">
                        <Icon className="w-5 h-5 text-[#293d4a] dark:text-[#e2ebf2] group-hover:text-[#1c2f3b] dark:group-hover:text-[#f2f7fb] transition-colors" />
                      </div>
                    </div>

                    <div className="relative z-10">
                      <h3 className="text-2xl font-bold text-[#1f2937] dark:text-[#f1f5f9] group-hover:translate-x-1 transition-transform">
                        {item.title}
                      </h3>
                      <p className="mt-2 max-w-[26ch] text-sm leading-relaxed text-[#2e4657] dark:text-[#d2dde6]">
                        {item.description}
                      </p>
                      <div
                        className={`mt-3 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.12em] font-semibold shadow-[0_4px_12px_rgba(15,23,42,0.08)] ${item.statusClass}`}
                      >
                        <span className="h-1.5 w-1.5 rounded-full bg-current/80 animate-pulse" />
                        {item.status}
                      </div>
                      <div className="mt-4 inline-flex items-center gap-1.5 text-[11px] uppercase tracking-wider font-semibold text-[#325665] dark:text-[#9edcec]">
                        {item.cta}
                        <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>

            {/* Stats Bar */}
            <div className="border-y border-[#546a7b]/55 dark:border-[#8ea3b4]/35 bg-[#fdfdff] dark:bg-[#111b21] rounded-2xl overflow-hidden shadow-[0_8px_30px_rgba(0,0,0,0.04)] dark:shadow-[0_12px_30px_rgba(0,0,0,0.35)] animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-500">
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
                      <div className="text-2xl font-bold text-[#1f2937] dark:text-[#eef3f8] tracking-tight group-hover:text-[#62929e] dark:group-hover:text-[#88d6e4] transition-colors">
                        {stat.value}
                      </div>
                      <div className="text-[10px] text-[#4f6576] dark:text-[#b4c3cf] font-semibold uppercase tracking-widest mt-0.5">
                        {stat.label}
                      </div>
                      <div className="text-[9px] text-[#2a3e4b] dark:text-[#d7e2ea] font-mono mt-1 bg-[#c6c5b9]/20 dark:bg-[#2a353d] px-2 py-0.5 rounded-sm w-fit">
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
