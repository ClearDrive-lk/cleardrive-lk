"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAppSelector } from "@/lib/store/store";
import { Terminal, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useLogout } from "@/lib/hooks/useLogout";
import { getAccessToken, getRefreshToken } from "@/lib/auth";

/**
 * Header Component - Matching homepage design
 */
export default function Header() {
  const pathname = usePathname();
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const { logout, isLoading } = useLogout();
  const hasSession = Boolean(getAccessToken() || getRefreshToken());

  const isActive = (path: string) => pathname === path;

  return (
    <nav className="border-b border-[#c6c5b9]/50 bg-[#fdfdff]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link
          href={isAuthenticated || hasSession ? "/dashboard" : "/"}
          className="font-bold text-xl tracking-tighter flex items-center gap-2"
        >
          <div className="w-8 h-8 bg-[#62929e]/10 border border-[#62929e]/20 rounded-md flex items-center justify-center">
            <Terminal className="w-4 h-4 text-[#62929e]" />
          </div>
          ClearDrive<span className="text-[#62929e]">.lk</span>
        </Link>

        {/* Navigation Links */}
        <div className="hidden md:flex gap-8 text-sm font-medium text-[#546a7b]">
          <Link
            href="/"
            className={`transition-colors ${
              isActive("/") ? "text-[#393d3f]" : "hover:text-[#393d3f]"
            }`}
          >
            Home
          </Link>

          <Link
            href="/dashboard/vehicles"
            className={`transition-colors ${
              isActive("/dashboard/vehicles")
                ? "text-[#393d3f]"
                : "hover:text-[#393d3f]"
            }`}
          >
            Vehicles
          </Link>

          {isAuthenticated && (
            <>
              <Link
                href="/dashboard"
                className={`transition-colors flex items-center gap-2 ${
                  isActive("/dashboard") ? "text-[#393d3f]" : "hover:text-[#393d3f]"
                }`}
              >
                Dashboard
                {isActive("/dashboard") && (
                  <Badge
                    variant="outline"
                    className="text-[10px] border-[#62929e]/20 text-[#62929e] h-4 px-1"
                  >
                    ACTIVE
                  </Badge>
                )}
              </Link>
              <Link
                href="/dashboard/orders"
                className={`transition-colors ${
                  isActive("/dashboard/orders")
                    ? "text-[#393d3f]"
                    : "hover:text-[#393d3f]"
                }`}
              >
                Orders
              </Link>
              <Link
                href="/dashboard/kyc"
                className={`transition-colors ${
                  isActive("/dashboard/kyc") ? "text-[#393d3f]" : "hover:text-[#393d3f]"
                }`}
              >
                KYC
              </Link>
              <Link
                href="/dashboard/profile"
                className={`transition-colors ${
                  isActive("/dashboard/profile")
                    ? "text-[#393d3f]"
                    : "hover:text-[#393d3f]"
                }`}
              >
                Profile
              </Link>
            </>
          )}
        </div>

        {/* User Actions */}
        <div className="flex gap-4 items-center">
          {isAuthenticated ? (
            <>
              <span className="hidden md:block text-sm text-[#546a7b] font-mono">
                {user?.name}
              </span>
              <Button
                onClick={logout}
                disabled={isLoading}
                variant="ghost"
                className="text-[#546a7b] hover:text-[#393d3f] hover:bg-[#c6c5b9]/20 font-mono flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                {isLoading ? "Signing out..." : "Sign Out"}
              </Button>
            </>
          ) : (
            <>
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
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

