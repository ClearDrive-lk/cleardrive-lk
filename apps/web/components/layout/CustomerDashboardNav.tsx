"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import ThemeToggle from "@/components/ui/theme-toggle";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import { useLogout } from "@/lib/hooks/useLogout";
import { useAppSelector } from "@/lib/store/store";
import { normalizeRole } from "@/lib/roles";
import { LogOut, Menu } from "lucide-react";

type NavItem = {
  label: string;
  href: string;
};

const CUSTOMER_NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Orders", href: "/dashboard/orders" },
  { label: "Vehicles", href: "/dashboard/vehicles" },
  { label: "KYC", href: "/dashboard/kyc" },
  { label: "Profile", href: "/dashboard/profile" },
];

const STAFF_EXTRA_ITEMS: NavItem[] = [
  { label: "Shipping", href: "/dashboard/shipping" },
  { label: "Documents", href: "/dashboard/documents" },
];

function isItemActive(pathname: string, href: string): boolean {
  if (href === "/dashboard") {
    return pathname === href;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function CustomerDashboardNav() {
  const pathname = usePathname();
  const { user } = useAppSelector((state) => state.auth);
  const role = normalizeRole(user?.role);
  const isStaff = role === "EXPORTER" || role === "ADMIN";
  const { logout, isLoading } = useLogout();
  const navItems = isStaff
    ? [
        ...CUSTOMER_NAV_ITEMS.slice(0, 4),
        ...STAFF_EXTRA_ITEMS,
        ...CUSTOMER_NAV_ITEMS.slice(4),
      ]
    : CUSTOMER_NAV_ITEMS;

  return (
    <nav className="border-b border-[#546a7b]/45 dark:border-[#8fa3b1]/35 bg-[#fdfdff]/80 dark:bg-[#10191e]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="cd-container flex min-h-16 items-center justify-between py-2">
        <Link
          href="/"
          className="font-bold text-xl tracking-tighter flex items-center gap-2 group text-[#1f2937] dark:text-[#edf2f7]"
        >
          <BrandMark className="h-10 w-10 transition-transform group-hover:scale-105 sm:h-12 sm:w-12" />
          <span className="hidden sm:inline">
            <BrandWordmark />
          </span>
        </Link>

        <div className="hidden md:flex gap-8 text-sm font-medium text-[#546a7b] dark:text-[#b8c7d4]">
          {navItems.map((item) => {
            const active = isItemActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={
                  active
                    ? "text-[#1f2937] dark:text-[#edf2f7] transition-colors flex items-center gap-2"
                    : "hover:text-[#2f4250] dark:hover:text-[#edf2f7] transition-colors"
                }
              >
                {item.label}
                {active && (
                  <Badge
                    variant="outline"
                    className="text-[10px] border-[#62929e]/30 text-[#3f7480] dark:text-[#88d6e4] h-4 px-1"
                  >
                    ACTIVE
                  </Badge>
                )}
              </Link>
            );
          })}
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <ThemeToggle />
          <Button
            onClick={logout}
            disabled={isLoading}
            className="hidden bg-[#62929e] px-2 sm:flex sm:px-3 text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
          >
            <LogOut className="h-4 w-4 sm:hidden" />
            <span className="hidden sm:inline">
              {isLoading ? "Signing Out..." : "Sign Out"}
            </span>
          </Button>
          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:text-[#b8c7d4] dark:hover:bg-[#24323b] dark:hover:text-[#edf2f7]"
              >
                <Menu className="h-5 w-5" />
                <span className="sr-only">Open dashboard menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent
              side="right"
              className="w-[88vw] max-w-sm border-l border-[#546a7b]/30 bg-[#fdfdff] p-0 dark:border-[#8fa3b1]/25 dark:bg-[#10191e]"
            >
              <SheetHeader className="border-b border-[#546a7b]/20 px-5 py-4 text-left dark:border-[#8fa3b1]/20">
                <SheetTitle className="text-[#393d3f] dark:text-[#edf2f7]">
                  Dashboard Menu
                </SheetTitle>
              </SheetHeader>
              <div className="flex flex-col gap-2 px-4 py-4">
                {navItems.map((item) => {
                  const active = isItemActive(pathname, item.href);
                  return (
                    <SheetClose asChild key={item.href}>
                      <Link
                        href={item.href}
                        className={`rounded-lg px-3 py-2 text-sm font-medium ${
                          active
                            ? "bg-[#62929e]/15 text-[#393d3f] dark:bg-[#88d6e4]/15 dark:text-[#edf2f7]"
                            : "text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f] dark:text-[#b8c7d4] dark:hover:bg-[#24323b] dark:hover:text-[#edf2f7]"
                        }`}
                      >
                        {item.label}
                      </Link>
                    </SheetClose>
                  );
                })}
                <Button
                  onClick={logout}
                  disabled={isLoading}
                  className="mt-2 w-full bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  {isLoading ? "Signing Out..." : "Sign Out"}
                </Button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </nav>
  );
}
