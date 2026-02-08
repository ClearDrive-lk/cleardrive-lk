"use client";

import AuthGuard from "@/components/auth/AuthGuard";
import { useAppSelector } from "@/lib/store/store";
import Link from "next/link";
import { Package, Car, User, FileText, TrendingUp, CheckCircle2, Terminal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useLogout } from "@/lib/hooks/useLogout";

/**
 * Dashboard Page - Exact homepage template
 */
export default function DashboardPage() {
    const { user } = useAppSelector((state) => state.auth);
    const { logout, isLoading } = useLogout();

    return (
        <AuthGuard>
            <div className="min-h-screen bg-[#050505] text-white selection:bg-[#FE7743] selection:text-black font-sans flex flex-col">
                {/* --- NAVIGATION (Same as Homepage) --- */}
                <nav className="border-b border-white/10 bg-[#050505]/80 backdrop-blur-md sticky top-0 z-50">
                    <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                        <Link href="/" className="font-bold text-xl tracking-tighter flex items-center gap-2">
                            <div className="w-8 h-8 bg-[#FE7743]/10 border border-[#FE7743]/20 rounded-md flex items-center justify-center">
                                <Terminal className="w-4 h-4 text-[#FE7743]" />
                            </div>
                            ClearDrive<span className="text-[#FE7743]">.lk</span>
                        </Link>
                        <div className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
                            <Link href="/dashboard" className="text-white transition-colors flex items-center gap-2">
                                Dashboard{" "}
                                <Badge variant="outline" className="text-[10px] border-[#FE7743]/20 text-[#FE7743] h-4 px-1">
                                    ACTIVE
                                </Badge>
                            </Link>
                            <Link href="/dashboard/orders" className="hover:text-white transition-colors">Orders</Link>
                            <Link href="/dashboard/vehicles" className="hover:text-white transition-colors">Vehicles</Link>
                            <Link href="/dashboard/profile" className="hover:text-white transition-colors">Profile</Link>
                        </div>
                        <Button
                            onClick={logout}
                            disabled={isLoading}
                            className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90 font-bold"
                        >
                            {isLoading ? "Signing Out..." : "Sign Out"}
                        </Button>
                    </div>
                </nav>

                {/* Grid Background */}
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
                <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#FE7743]/5 rounded-[100%] blur-[120px] pointer-events-none" />

                {/* Content */}
                <section className="relative pt-20 pb-20 px-6 overflow-hidden flex-1">
                    <div className="relative z-10 max-w-7xl mx-auto">
                        <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-[#FE7743] mb-8">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FE7743] opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#FE7743]"></span>
                            </span>
                            DASHBOARD TERMINAL :: {new Date().toLocaleDateString()}
                        </div>

                        <h1 className="text-5xl md:text-8xl font-bold tracking-tighter text-white leading-[0.9] mb-6">
                            WELCOME{" "}
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FE7743] to-orange-200">
                                {user?.name?.toUpperCase() || "USER"}.
                            </span>
                        </h1>

                        <p className="text-lg md:text-xl text-gray-400 max-w-2xl mb-12">
                            Your personal import terminal dashboard. Monitor clearances, track shipments, and manage orders in real-time.
                        </p>

                        {/* Quick Links Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
                            {[
                                { title: "Orders", href: "/dashboard/orders", icon: Package, code: "ORD-SYS" },
                                { title: "Vehicles", href: "/dashboard/vehicles", icon: Car, code: "VEH-TRK" },
                                { title: "Profile", href: "/dashboard/profile", icon: User, code: "USR-ACC" },
                                { title: "Documents", href: "/dashboard/documents", icon: FileText, code: "DOC-MGT" },
                            ].map((item, i) => {
                                const Icon = item.icon;
                                return (
                                    <Link
                                        key={i}
                                        href={item.href}
                                        className="group relative h-72 rounded-xl border border-white/10 bg-gradient-to-br from-white/5 to-white/[0.02] p-6 flex flex-col justify-between overflow-hidden hover:border-[#FE7743]/50 transition-all cursor-pointer"
                                    >
                                        <div className="absolute inset-0 bg-black/40 group-hover:bg-transparent transition-colors duration-500" />
                                        <div className="relative z-10 flex justify-between items-start">
                                            <Badge
                                                variant="outline"
                                                className="border-white/20 text-white/50 font-mono text-[10px]"
                                            >
                                                {item.code}
                                            </Badge>
                                            <Icon className="w-8 h-8 text-white/40 group-hover:text-white transition-colors" />
                                        </div>
                                        <div className="relative z-10">
                                            <h3 className="text-2xl font-bold text-white group-hover:translate-x-1 transition-transform">
                                                {item.title}
                                            </h3>
                                            <p className="text-sm text-gray-400 mt-1 flex items-center gap-2">
                                                <span className="w-1.5 h-1.5 rounded-full bg-[#FE7743] animate-pulse" />
                                                Live Access
                                            </p>
                                        </div>
                                    </Link>
                                );
                            })}
                        </div>

                        {/* Stats Bar */}
                        <div className="border-b border-white/10 bg-[#0A0A0A]">
                            <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-white/10">
                                {[
                                    { label: "Active Orders", value: "0", icon: Package, sub: "In Progress" },
                                    { label: "In Transit", value: "0", icon: Car, sub: "En Route" },
                                    { label: "Completed", value: "0", icon: TrendingUp, sub: "This Month" },
                                    { label: "Avg. Time", value: "~14 Days", icon: CheckCircle2, sub: "Clearance" },
                                ].map((stat, i) => (
                                    <div
                                        key={i}
                                        className="p-8 flex items-start gap-4 group hover:bg-white/5 transition-colors cursor-default"
                                    >
                                        <div className="mt-1 p-2 rounded-md bg-[#FE7743]/10 text-[#FE7743] group-hover:bg-[#FE7743] group-hover:text-black transition-colors">
                                            <stat.icon className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <div className="text-xl font-bold text-white tracking-tight">{stat.value}</div>
                                            <div className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-1">{stat.label}</div>
                                            <div className="text-[10px] text-gray-600 font-mono mt-1">{stat.sub}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </section>

                {/* Footer (Same as Homepage) */}
                <footer className="border-t border-white/10 py-16 bg-[#050505]">
                    <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12">
                        <div className="space-y-6">
                            <div className="font-bold text-xl tracking-tighter text-white flex items-center gap-2">
                                <Terminal className="w-5 h-5 text-[#FE7743]" />
                                ClearDrive<span className="text-[#FE7743]">.lk</span>
                            </div>
                            <p className="text-sm text-gray-500 leading-relaxed">
                                The first tech-enabled vehicle import platform in Sri Lanka.
                            </p>
                        </div>
                        <div>
                            <h4 className="font-bold text-white mb-6">Quick Links</h4>
                            <ul className="space-y-3 text-sm text-gray-500">
                                <li className="hover:text-[#FE7743] cursor-pointer">Dashboard</li>
                                <li className="hover:text-[#FE7743] cursor-pointer">Orders</li>
                                <li className="hover:text-[#FE7743] cursor-pointer">Vehicles</li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-bold text-white mb-6">Company</h4>
                            <ul className="space-y-3 text-sm text-gray-500">
                                <li className="hover:text-[#FE7743] cursor-pointer">About Us</li>
                                <li className="hover:text-[#FE7743] cursor-pointer">Terms of Service</li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-bold text-white mb-6">Support</h4>
                            <ul className="space-y-3 text-sm text-gray-500">
                                <li className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-green-500" /> Systems Operational
                                </li>
                                <li>support@cleardrive.lk</li>
                            </ul>
                        </div>
                    </div>
                    <div className="max-w-7xl mx-auto px-6 mt-16 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center text-xs text-gray-600 font-mono">
                        <p>© 2026 CLEARDRIVE INC. ALL RIGHTS RESERVED.</p>
                        <p>DESIGNED FOR HIGH-FREQUENCY TRADING</p>
                    </div>
                </footer>
            </div>
        </AuthGuard>
    );
}
