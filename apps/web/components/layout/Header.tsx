"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAppSelector } from "@/lib/store/store";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import ThemeToggle from "@/components/ui/theme-toggle";
import { useLogout } from "@/lib/hooks/useLogout";
import { getAccessToken, getRefreshToken } from "@/lib/auth";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import { normalizeRole } from "@/lib/roles";

/**
 * Header Component - Matching homepage design
 */
export default function Header() {
  const pathname = usePathname();
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const role = normalizeRole(user?.role);
  const { logout, isLoading } = useLogout();
  const hasSession = Boolean(getAccessToken() || getRefreshToken());
  const showCustomerOnlyNav = isAuthenticated && role === "CUSTOMER";
  const isAuthed = isAuthenticated || hasSession;

  const isActive = (path: string) => pathname === path;
  const linkBase =
    "transition-colors text-[#546a7b] dark:text-[#b8c7d4] hover:text-[#393d3f] dark:hover:text-[#edf2f7]";
  const activeLink = "text-[#393d3f] dark:text-[#edf2f7]";

  return (
    <nav className="sticky top-0 z-50 border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md dark:border-[#8fa3b1]/35 dark:bg-[#10191e]/80">
      <div className="cd-container h-16 flex items-center justify-between">
        {/* Logo */}
        <Link
          href={isAuthed ? "/dashboard" : "/"}
          className="flex items-center gap-2 text-xl font-bold tracking-tighter text-[#393d3f] dark:text-[#edf2f7]"
        >
          <BrandMark className="h-12 w-12" />
          <BrandWordmark />
        </Link>

        {/* Navigation Links */}
        {showCustomerOnlyNav ? (
          <div className="hidden gap-8 text-sm font-medium md:flex">
            <Link
              href="/dashboard"
              className={`flex items-center gap-2 ${
                isActive("/dashboard") ? activeLink : linkBase
              }`}
            >
              Dashboard
              {isActive("/dashboard") && (
                <Badge
                  variant="outline"
                  className="h-4 border-[#62929e]/30 px-1 text-[10px] text-[#62929e] dark:border-[#88d6e4]/30 dark:text-[#88d6e4]"
                >
                  ACTIVE
                </Badge>
              )}
            </Link>
            <Link
              href="/dashboard/orders"
              className={isActive("/dashboard/orders") ? activeLink : linkBase}
            >
              Orders
            </Link>
            <Link
              href="/dashboard/vehicles"
              className={
                isActive("/dashboard/vehicles") ? activeLink : linkBase
              }
            >
              Vehicles
            </Link>
            <Link
              href="/tax-calculator"
              className={isActive("/tax-calculator") ? activeLink : linkBase}
            >
              Tax Calculator
            </Link>
            <Link
              href="/dashboard/kyc"
              className={isActive("/dashboard/kyc") ? activeLink : linkBase}
            >
              KYC
            </Link>
            <Link
              href="/dashboard/profile"
              className={isActive("/dashboard/profile") ? activeLink : linkBase}
            >
              Profile
            </Link>
          </div>
        ) : (
          <div className="hidden gap-8 text-sm font-medium md:flex">
            <Link href="/" className={isActive("/") ? activeLink : linkBase}>
              Home
            </Link>

            <Link
              href="/dashboard/vehicles"
              className={
                isActive("/dashboard/vehicles") ? activeLink : linkBase
              }
            >
              Vehicles
            </Link>
            <Link
              href="/tax-calculator"
              className={isActive("/tax-calculator") ? activeLink : linkBase}
            >
              Tax Calculator
            </Link>

            {isAuthenticated && (
              <>
                <Link
                  href="/dashboard"
                  className={`flex items-center gap-2 ${
                    isActive("/dashboard") ? activeLink : linkBase
                  }`}
                >
                  Dashboard
                  {isActive("/dashboard") && (
                    <Badge
                      variant="outline"
                      className="h-4 border-[#62929e]/30 px-1 text-[10px] text-[#62929e] dark:border-[#88d6e4]/30 dark:text-[#88d6e4]"
                    >
                      ACTIVE
                    </Badge>
                  )}
                </Link>
                <Link
                  href="/dashboard/orders"
                  className={
                    isActive("/dashboard/orders") ? activeLink : linkBase
                  }
                >
                  Orders
                </Link>
                <Link
                  href="/dashboard/kyc"
                  className={isActive("/dashboard/kyc") ? activeLink : linkBase}
                >
                  KYC
                </Link>
                <Link
                  href="/dashboard/profile"
                  className={
                    isActive("/dashboard/profile") ? activeLink : linkBase
                  }
                >
                  Profile
                </Link>
              </>
            )}
            <Link
              href="/about"
              className={isActive("/about") ? activeLink : linkBase}
            >
              About Us
            </Link>
          </div>
        )}

        {/* User Actions */}
        <div className="flex gap-3 items-center">
          <ThemeToggle />
          {isAuthed ? (
            <>
              <span className="hidden font-mono text-sm text-[#546a7b] dark:text-[#b8c7d4] md:block">
                {user?.name}
              </span>
              <Button
                onClick={logout}
                disabled={isLoading}
                variant="ghost"
                className="flex items-center gap-2 font-mono text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:text-[#b8c7d4] dark:hover:bg-[#24323b] dark:hover:text-[#edf2f7]"
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
                  className="font-mono text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:text-[#b8c7d4] dark:hover:bg-[#24323b] dark:hover:text-[#edf2f7]"
                >
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button className="bg-[#62929e] font-bold text-[#fdfdff] hover:bg-[#62929e]/90 dark:bg-[#6ab2bf] dark:text-[#0f1417] dark:hover:bg-[#88d6e4]">
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
