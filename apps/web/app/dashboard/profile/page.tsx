"use client";

import AuthGuard from "@/components/auth/AuthGuard";
import { useAppSelector } from "@/lib/store/store";
import Link from "next/link";
import { User, Mail, Shield, Terminal, LogOut, ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useLogout } from "@/lib/hooks/useLogout";

export default function ProfilePage() {
    const { user } = useAppSelector((state) => state.auth);
    const { logout, isLoading } = useLogout();

    return (
        <AuthGuard>
            <div className="min-h-screen bg-[#050505] text-white selection:bg-[#FE7743] selection:text-black font-sans flex flex-col">
                {/* Navigation */}
                <nav className="border-b border-white/10 bg-[#050505]/80 backdrop-blur-md sticky top-0 z-50">
                    <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                        <Link href="/" className="font-bold text-xl tracking-tighter flex items-center gap-2">
                            <div className="w-8 h-8 bg-[#FE7743]/10 border border-[#FE7743]/20 rounded-md flex items-center justify-center">
                                <Terminal className="w-4 h-4 text-[#FE7743]" />
                            </div>
                            ClearDrive<span className="text-[#FE7743]">.lk</span>
                        </Link>
                        <div className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
                            <Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
                            <Link href="/dashboard/orders" className="hover:text-white transition-colors">Orders</Link>
                            <Link href="/dashboard/vehicles" className="hover:text-white transition-colors">Vehicles</Link>
                            <Link href="/dashboard/profile" className="text-white transition-colors flex items-center gap-2">
                                Profile{" "}
                                <Badge variant="outline" className="text-[10px] border-[#FE7743]/20 text-[#FE7743] h-4 px-1">
                                    ACTIVE
                                </Badge>
                            </Link>
                        </div>
                        <Button
                            onClick={logout}
                            disabled={isLoading}
                            className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90 font-bold"
                        >
                            {isLoading ? "Signing out..." : "Sign Out"}
                        </Button>
                    </div>
                </nav>

                {/* Grid Background */}
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
                <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#FE7743]/5 rounded-[100%] blur-[120px] pointer-events-none" />

                {/* Content */}
                <section className="relative pt-20 pb-20 px-6 overflow-hidden flex-1">
                    <div className="relative z-10 max-w-5xl mx-auto">
                        <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-[#FE7743] mb-8">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FE7743] opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#FE7743]"></span>
                            </span>
                            ACCOUNT TERMINAL :: USER PROFILE
                        </div>

                        <h1 className="text-5xl md:text-8xl font-bold tracking-tighter text-white leading-[0.9] mb-6">
                            YOUR{" "}
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FE7743] to-orange-200">
                                PROFILE.
                            </span>
                        </h1>

                        <p className="text-lg md:text-xl text-gray-400 max-w-2xl mb-12">
                            Manage your account information and preferences.
                        </p>

                        {/* Profile Info Grid */}
                        {user && (
                            <div className="border-b border-white/10 bg-[#0A0A0A]">
                                <div className="grid grid-cols-1 md:grid-cols-2 divide-x divide-y divide-white/10">
                                    <div className="p-8 flex items-start gap-4 group hover:bg-white/5 transition-colors">
                                        <div className="mt-1 p-2 rounded-md bg-[#FE7743]/10 text-[#FE7743] group-hover:bg-[#FE7743] group-hover:text-black transition-colors">
                                            <User className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <div className="text-xl font-bold text-white tracking-tight">{user.name}</div>
                                            <div className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-1">Full Name</div>
                                            <div className="text-[10px] text-gray-600 font-mono mt-1">Primary Account</div>
                                        </div>
                                    </div>

                                    <div className="p-8 flex items-start gap-4 group hover:bg-white/5 transition-colors">
                                        <div className="mt-1 p-2 rounded-md bg-[#FE7743]/10 text-[#FE7743] group-hover:bg-[#FE7743] group-hover:text-black transition-colors">
                                            <Mail className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <div className="text-xl font-bold text-white tracking-tight break-all">{user.email}</div>
                                            <div className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-1">Email Address</div>
                                            <div className="text-[10px] text-gray-600 font-mono mt-1">Verified</div>
                                        </div>
                                    </div>

                                    <div className="p-8 flex items-start gap-4 group hover:bg-white/5 transition-colors">
                                        <div className="mt-1 p-2 rounded-md bg-[#FE7743]/10 text-[#FE7743] group-hover:bg-[#FE7743] group-hover:text-black transition-colors">
                                            <Shield className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <div className="text-xl font-bold text-white tracking-tight capitalize">{user.role}</div>
                                            <div className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-1">Account Role</div>
                                            <div className="text-[10px] text-gray-600 font-mono mt-1">Access Level</div>
                                        </div>
                                    </div>

                                    <div className="p-8 flex items-start gap-4 group hover:bg-white/5 transition-colors">
                                        <div className="mt-1 p-2 rounded-md bg-[#FE7743]/10 text-[#FE7743] group-hover:bg-[#FE7743] group-hover:text-black transition-colors">
                                            <Terminal className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <div className="text-sm font-mono text-white opacity-80 tracking-tight">{user.id}</div>
                                            <div className="text-xs text-gray-400 font-medium uppercase tracking-wider mt-1">User ID</div>
                                            <div className="text-[10px] text-gray-600 font-mono mt-1">System Reference</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Actions */}
                        <div className="mt-12">
                            <Button
                                onClick={logout}
                                disabled={isLoading}
                                variant="outline"
                                className="border-white/10 hover:bg-white/5 hover:text-white gap-2"
                            >
                                <LogOut className="w-4 h-4" />
                                {isLoading ? "Signing out..." : "Sign Out & Return to Login"}
                            </Button>
                        </div>
                    </div>
                </section>

                {/* Footer */}
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
                            <ul className="space-y-3 text-sm text-gray-500 font-mono">
                                <li className="hover:text-[#FE7743] cursor-pointer flex items-center gap-2">
                                    <ArrowRight className="w-3 h-3" /> Dashboard
                                </li>
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
