"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAppSelector } from "@/lib/store/store";
import { LogOut, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import ThemeToggle from "@/components/ui/theme-toggle";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useLogout } from "@/lib/hooks/useLogout";
import { getAccessToken, getRefreshToken } from "@/lib/auth";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import { normalizeRole, roleHomePath } from "@/lib/roles";
import CustomerDashboardNav from "@/components/layout/CustomerDashboardNav";

type NavLink = {
  href: string;
  label: string;
};

/**
 * Header Component - Matching homepage design
 */
export default function Header() {
  const pathname = usePathname();
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const role = normalizeRole(user?.role);
  const homePath = roleHomePath(role);
  const { logout, isLoading } = useLogout();
  const hasSession = Boolean(getAccessToken() || getRefreshToken());
  const showCustomerOnlyNav = isAuthenticated && role === "CUSTOMER";
  const isAuthed = isAuthenticated || hasSession;

  if (isAuthed && role === "CUSTOMER") {
    return <CustomerDashboardNav />;
  }

  const isActive = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname === path || pathname.startsWith(`${path}/`);
  };
  const linkBase =
    "transition-colors text-[#546a7b] dark:text-[#b8c7d4] hover:text-[#393d3f] dark:hover:text-[#edf2f7]";
  const activeLink = "text-[#393d3f] dark:text-[#edf2f7]";
  const navLinks: NavLink[] = showCustomerOnlyNav
    ? [
        { href: "/dashboard", label: "Dashboard" },
        { href: "/dashboard/orders", label: "Orders" },
        { href: "/dashboard/vehicles", label: "Vehicles" },
        { href: "/tax-calculator", label: "Tax Calculator" },
        { href: "/dashboard/kyc", label: "KYC" },
        { href: "/dashboard/profile", label: "Profile" },
      ]
    : [
        { href: "/", label: "Home" },
        { href: "/dashboard/vehicles", label: "Vehicles" },
        { href: "/tax-calculator", label: "Tax Calculator" },
        ...(isAuthenticated
          ? [
              { href: "/dashboard", label: "Dashboard" },
              { href: "/dashboard/orders", label: "Orders" },
              { href: "/dashboard/kyc", label: "KYC" },
              { href: "/dashboard/profile", label: "Profile" },
            ]
          : []),
        { href: "/about", label: "About Us" },
      ];

  return (
    <nav className="sticky top-0 z-50 border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md dark:border-[#8fa3b1]/35 dark:bg-[#10191e]/80">
      <div className="cd-container flex min-h-16 items-center justify-between py-2">
        {/* Logo */}
        <Link
          href={isAuthed ? homePath : "/"}
          className="flex items-center gap-2 text-xl font-bold tracking-tighter text-[#393d3f] dark:text-[#edf2f7]"
        >
          <BrandMark className="h-10 w-10 sm:h-12 sm:w-12" />
          <span className="hidden sm:inline">
            <BrandWordmark />
          </span>
        </Link>

        {/* Navigation Links */}
        <div className="hidden gap-6 text-sm font-medium md:flex lg:gap-8">
          {navLinks.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2 ${
                isActive(item.href) ? activeLink : linkBase
              }`}
            >
              {item.label}
              {item.href === "/dashboard" && isActive("/dashboard") && (
                <Badge
                  variant="outline"
                  className="h-4 border-[#62929e]/30 px-1 text-[10px] text-[#62929e] dark:border-[#88d6e4]/30 dark:text-[#88d6e4]"
                >
                  ACTIVE
                </Badge>
              )}
            </Link>
          ))}
        </div>

        {/* User Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          <ThemeToggle />
          {isAuthed ? (
            <>
              <span className="hidden font-mono text-sm text-[#546a7b] dark:text-[#b8c7d4] lg:block">
                {user?.name}
              </span>
              <Button
                onClick={logout}
                disabled={isLoading}
                variant="ghost"
                className="hidden items-center gap-2 px-2 sm:flex sm:px-3 font-mono text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:text-[#b8c7d4] dark:hover:bg-[#24323b] dark:hover:text-[#edf2f7]"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">
                  {isLoading ? "Signing out..." : "Sign Out"}
                </span>
              </Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button
                  variant="ghost"
                  className="px-2 sm:px-3 font-mono text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:text-[#b8c7d4] dark:hover:bg-[#24323b] dark:hover:text-[#edf2f7]"
                >
                  Sign In
                </Button>
              </Link>
              <Link href="/register" className="hidden sm:block">
                <Button className="bg-[#62929e] font-bold text-[#fdfdff] hover:bg-[#62929e]/90 dark:bg-[#6ab2bf] dark:text-[#0f1417] dark:hover:bg-[#88d6e4]">
                  Get Access
                </Button>
              </Link>
            </>
          )}
          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:text-[#b8c7d4] dark:hover:bg-[#24323b] dark:hover:text-[#edf2f7]"
              >
                <Menu className="h-5 w-5" />
                <span className="sr-only">Open menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent
              side="right"
              className="w-[88vw] max-w-sm border-l border-[#546a7b]/30 bg-[#fdfdff] p-0 dark:border-[#8fa3b1]/25 dark:bg-[#10191e]"
            >
              <SheetHeader className="border-b border-[#546a7b]/20 px-5 py-4 text-left dark:border-[#8fa3b1]/20">
                <SheetTitle className="text-[#393d3f] dark:text-[#edf2f7]">
                  Menu
                </SheetTitle>
              </SheetHeader>
              <div className="flex flex-col gap-2 px-4 py-4">
                {navLinks.map((item) => (
                  <SheetClose asChild key={item.href}>
                    <Link
                      href={item.href}
                      className={`rounded-lg px-3 py-2 text-sm font-medium ${
                        isActive(item.href)
                          ? "bg-[#62929e]/15 text-[#393d3f] dark:bg-[#88d6e4]/15 dark:text-[#edf2f7]"
                          : "text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:text-[#b8c7d4] dark:hover:bg-[#24323b] dark:hover:text-[#edf2f7]"
                      }`}
                    >
                      {item.label}
                    </Link>
                  </SheetClose>
                ))}
                {!isAuthed && (
                  <SheetClose asChild>
                    <Link
                      href="/register"
                      className="mt-2 rounded-lg bg-[#62929e] px-3 py-2 text-center text-sm font-semibold text-[#fdfdff] hover:bg-[#62929e]/90 dark:bg-[#6ab2bf] dark:text-[#0f1417] dark:hover:bg-[#88d6e4]"
                    >
                      Get Access
                    </Link>
                  </SheetClose>
                )}
                {isAuthed && (
                  <Button
                    onClick={logout}
                    disabled={isLoading}
                    variant="outline"
                    className="mt-2 w-full justify-center border-[#546a7b]/30 text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:border-[#8fa3b1]/30 dark:text-[#b8c7d4] dark:hover:bg-[#24323b] dark:hover:text-[#edf2f7]"
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    {isLoading ? "Signing out..." : "Sign Out"}
                  </Button>
                )}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </nav>
  );
}
