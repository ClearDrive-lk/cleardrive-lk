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
  Terminal,
  Ship,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useLogout } from "@/lib/hooks/useLogout";
import { normalizeRole } from "@/lib/roles";

/**
 * Dashboard Page - Exact homepage template
 */
export default function DashboardPage() {
  const { user } = useAppSelector((state) => state.auth);
  const { logout, isLoading } = useLogout();
  const role = normalizeRole(user?.role);
  const showExporterEntry = role === "EXPORTER" || role === "ADMIN";

  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans flex flex-col">
        {/* --- NAVIGATION (Same as Homepage) --- */}
        <nav className="border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
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
            <Button
              onClick={logout}
              disabled={isLoading}
              className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
            >
              {isLoading ? "Signing Out..." : "Sign Out"}
            </Button>
          </div>
        </nav>

        {/* Grid Background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
        <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#62929e]/5 rounded-[100%] blur-[120px] pointer-events-none" />

        {/* Content */}
        <section className="relative pt-20 pb-20 px-6 overflow-hidden flex-1">
          <div className="relative z-10 max-w-7xl mx-auto">
            <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-[#c6c5b9]/20 border border-[#546a7b]/65 text-xs font-mono text-[#62929e] mb-8">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#62929e] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#62929e]"></span>
              </span>
              DASHBOARD TERMINAL :: {new Date().toLocaleDateString()}
            </div>

            <h1 className="text-5xl md:text-8xl font-bold tracking-tighter text-[#393d3f] leading-[0.9] mb-6">
              WELCOME{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#62929e] to-[#c6c5b9]">
                {user?.name?.toUpperCase() || "USER"}.
              </span>
            </h1>

            <p className="text-lg md:text-xl text-[#546a7b] max-w-2xl mb-12">
              Your personal import terminal dashboard. Monitor clearances, track
              shipments, and manage orders in real-time.
            </p>

            {showExporterEntry && (
              <div className="mb-10 flex flex-wrap items-center gap-4">
                <Button
                  asChild
                  className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold gap-2"
                >
                  <Link href="/exporter">
                    <Ship className="w-4 h-4" />
                    Open Exporter Terminal
                  </Link>
                </Button>
                <Badge
                  variant="outline"
                  className="border-[#62929e]/30 text-[#62929e] font-mono"
                >
                  EXPORTER ACCESS
                </Badge>
              </div>
            )}

            {/* Quick Links Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
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
                    className="group relative h-72 rounded-xl border border-[#546a7b]/65 bg-gradient-to-br from-white/5 to-white/[0.02] p-6 flex flex-col justify-between overflow-hidden hover:border-[#62929e]/50 transition-all cursor-pointer"
                  >
                    <div className="absolute inset-0 bg-[#fdfdff]/40 group-hover:bg-transparent transition-colors duration-500" />
                    <div className="relative z-10 flex justify-between items-start">
                      <Badge
                        variant="outline"
                        className="border-[#546a7b]/65 text-[#393d3f]/50 font-mono text-[10px]"
                      >
                        {item.code}
                      </Badge>
                      <Icon className="w-8 h-8 text-[#393d3f]/40 group-hover:text-[#393d3f] transition-colors" />
                    </div>
                    <div className="relative z-10">
                      <h3 className="text-2xl font-bold text-[#393d3f] group-hover:translate-x-1 transition-transform">
                        {item.title}
                      </h3>
                      <p className="text-sm text-[#546a7b] mt-1 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#62929e] animate-pulse" />
                        Live Access
                      </p>
                    </div>
                  </Link>
                );
              })}
            </div>

            {/* Stats Bar */}
            <div className="border-b border-[#546a7b]/65 bg-[#fdfdff]">
              <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-white/10">
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
                    className="p-8 flex items-start gap-4 group hover:bg-[#c6c5b9]/20 transition-colors cursor-default"
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
          </div>
        </section>

        {/* Footer (Same as Homepage) */}
        <footer className="border-t border-[#546a7b]/65 py-16 bg-[#fdfdff]">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12">
            <div className="space-y-6">
              <div className="font-bold text-xl tracking-tighter text-[#393d3f] flex items-center gap-2">
                <Terminal className="w-5 h-5 text-[#62929e]" />
                ClearDrive<span className="text-[#62929e]">.lk</span>
              </div>
              <p className="text-sm text-[#546a7b] leading-relaxed">
                The first tech-enabled vehicle import platform in Sri Lanka.
              </p>
            </div>
            <div>
              <h4 className="font-bold text-[#393d3f] mb-6">Quick Links</h4>
              <ul className="space-y-3 text-sm text-[#546a7b]">
                <li className="hover:text-[#62929e] cursor-pointer">
                  Dashboard
                </li>
                <li className="hover:text-[#62929e] cursor-pointer">Orders</li>
                <li className="hover:text-[#62929e] cursor-pointer">
                  Vehicles
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-[#393d3f] mb-6">Company</h4>
              <ul className="space-y-3 text-sm text-[#546a7b]">
                <li className="hover:text-[#62929e] cursor-pointer">
                  About Us
                </li>
                <li className="hover:text-[#62929e] cursor-pointer">
                  Terms of Service
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
                <li>support@cleardrive.lk</li>
              </ul>
            </div>
          </div>
          <div className="max-w-7xl mx-auto px-6 mt-16 pt-8 border-t border-[#546a7b]/40 flex flex-col md:flex-row justify-between items-center text-xs text-[#393d3f] font-mono">
            <p>© 2026 CLEARDRIVE INC. ALL RIGHTS RESERVED.</p>
            <p>DESIGNED FOR HIGH-FREQUENCY TRADING</p>
          </div>
        </footer>
      </div>
    </AuthGuard>
  );
}

