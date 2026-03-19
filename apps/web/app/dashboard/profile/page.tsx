"use client";

import AuthGuard from "@/components/auth/AuthGuard";
import { useAppSelector } from "@/lib/store/store";
import Link from "next/link";
import { User, Mail, Shield, Terminal, LogOut } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useLogout } from "@/lib/hooks/useLogout";
import { GDPRDataExport } from "@/components/gdpr/GDPRDataExport";
import ThemeToggle from "@/components/ui/theme-toggle";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";

export default function ProfilePage() {
  const { user } = useAppSelector((state) => state.auth);
  const { logout, isLoading } = useLogout();

  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans flex flex-col">
        {/* Navigation */}
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
                href="/dashboard"
                className="hover:text-[#393d3f] transition-colors"
              >
                Dashboard
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
                href="/dashboard/profile"
                className="text-[#393d3f] transition-colors flex items-center gap-2"
              >
                Profile{" "}
                <Badge
                  variant="outline"
                  className="text-[10px] border-[#62929e]/20 text-[#62929e] h-4 px-1"
                >
                  ACTIVE
                </Badge>
              </Link>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <Button
                onClick={logout}
                disabled={isLoading}
                className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
              >
                {isLoading ? "Signing out..." : "Sign Out"}
              </Button>
            </div>
          </div>
        </nav>

        {/* Grid Background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
        <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#62929e]/5 rounded-[100%] blur-[120px] pointer-events-none" />

        {/* Content */}
        <section className="relative pt-20 pb-20 overflow-hidden flex-1">
          <div className="relative z-10 cd-container-narrow">
            <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-[#c6c5b9]/20 border border-[#546a7b]/65 text-xs font-mono text-[#62929e] mb-8">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#62929e] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#62929e]"></span>
              </span>
              ACCOUNT TERMINAL :: USER PROFILE
            </div>

            <h1 className="text-5xl md:text-8xl font-bold tracking-tighter text-[#393d3f] leading-[0.9] mb-6">
              YOUR{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#62929e] to-[#c6c5b9]">
                PROFILE.
              </span>
            </h1>

            <p className="text-lg md:text-xl text-[#546a7b] max-w-2xl mb-12">
              Manage your account information and preferences.
            </p>

            {/* Profile Info Grid */}
            {user && (
              <div className="border-b border-[#546a7b]/65 bg-[#fdfdff]">
                <div className="grid grid-cols-1 md:grid-cols-2 divide-x divide-y divide-white/10">
                  <div className="p-8 flex items-start gap-4 group hover:bg-[#c6c5b9]/20 transition-colors">
                    <div className="mt-1 p-2 rounded-md bg-[#62929e]/10 text-[#62929e] group-hover:bg-[#62929e] group-hover:text-[#fdfdff] transition-colors">
                      <User className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-xl font-bold text-[#393d3f] tracking-tight">
                        {user.name}
                      </div>
                      <div className="text-xs text-[#546a7b] font-medium uppercase tracking-wider mt-1">
                        Full Name
                      </div>
                      <div className="text-[10px] text-[#393d3f] font-mono mt-1">
                        Primary Account
                      </div>
                    </div>
                  </div>

                  <div className="p-8 flex items-start gap-4 group hover:bg-[#c6c5b9]/20 transition-colors">
                    <div className="mt-1 p-2 rounded-md bg-[#62929e]/10 text-[#62929e] group-hover:bg-[#62929e] group-hover:text-[#fdfdff] transition-colors">
                      <Mail className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-xl font-bold text-[#393d3f] tracking-tight break-all">
                        {user.email}
                      </div>
                      <div className="text-xs text-[#546a7b] font-medium uppercase tracking-wider mt-1">
                        Email Address
                      </div>
                      <div className="text-[10px] text-[#393d3f] font-mono mt-1">
                        Verified
                      </div>
                    </div>
                  </div>

                  <div className="p-8 flex items-start gap-4 group hover:bg-[#c6c5b9]/20 transition-colors">
                    <div className="mt-1 p-2 rounded-md bg-[#62929e]/10 text-[#62929e] group-hover:bg-[#62929e] group-hover:text-[#fdfdff] transition-colors">
                      <Shield className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-xl font-bold text-[#393d3f] tracking-tight capitalize">
                        {user.role}
                      </div>
                      <div className="text-xs text-[#546a7b] font-medium uppercase tracking-wider mt-1">
                        Account Role
                      </div>
                      <div className="text-[10px] text-[#393d3f] font-mono mt-1">
                        Access Level
                      </div>
                    </div>
                  </div>

                  <div className="p-8 flex items-start gap-4 group hover:bg-[#c6c5b9]/20 transition-colors">
                    <div className="mt-1 p-2 rounded-md bg-[#62929e]/10 text-[#62929e] group-hover:bg-[#62929e] group-hover:text-[#fdfdff] transition-colors">
                      <Terminal className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-sm font-mono text-[#393d3f] opacity-80 tracking-tight">
                        {user.id}
                      </div>
                      <div className="text-xs text-[#546a7b] font-medium uppercase tracking-wider mt-1">
                        User ID
                      </div>
                      <div className="text-[10px] text-[#393d3f] font-mono mt-1">
                        System Reference
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="mt-12">
              <div className="mb-8">
                <GDPRDataExport />
              </div>
              <Button
                onClick={logout}
                disabled={isLoading}
                variant="outline"
                className="border-[#546a7b]/65 hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] gap-2"
              >
                <LogOut className="w-4 h-4" />
                {isLoading ? "Signing out..." : "Sign Out & Return to Login"}
              </Button>
            </div>
          </div>
        </section>
      </div>
    </AuthGuard>
  );
}


