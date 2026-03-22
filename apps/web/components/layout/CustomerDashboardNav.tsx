"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import ThemeToggle from "@/components/ui/theme-toggle";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import { useLogout } from "@/lib/hooks/useLogout";
import { useAppSelector } from "@/lib/store/store";
import { normalizeRole } from "@/lib/roles";
import { LogOut } from "lucide-react";

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
            className="bg-[#62929e] px-2 sm:px-3 text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
          >
            <LogOut className="h-4 w-4 sm:hidden" />
            <span className="hidden sm:inline">
              {isLoading ? "Signing Out..." : "Sign Out"}
            </span>
          </Button>
        </div>
      </div>
    </nav>
  );
}
