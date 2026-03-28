"use client";

import type { ComponentType } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  ShoppingBag,
  Truck,
  Car,
  ShieldCheck,
  FileClock,
  ScrollText,
  UploadCloud,
  ClipboardCheck,
  History,
  Menu,
  LogOut,
} from "lucide-react";

import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";
import { useLogout } from "@/lib/hooks/useLogout";
import { cn } from "@/lib/utils";
import { BrandMark } from "@/components/ui/brand";

type NavItem = {
  label: string;
  href: string;
  icon: ComponentType<{ className?: string }>;
};

type NavSection = {
  title: string;
  items: NavItem[];
};

const NAV_SECTIONS: NavSection[] = [
  {
    title: "Core",
    items: [
      {
        label: "Dashboard",
        href: "/admin/dashboard",
        icon: LayoutDashboard,
      },
      {
        label: "Users",
        href: "/admin/users",
        icon: Users,
      },
      {
        label: "Orders",
        href: "/admin/orders",
        icon: ShoppingBag,
      },
      {
        label: "Vehicles",
        href: "/admin/vehicles",
        icon: Car,
      },
      {
        label: "Shipping",
        href: "/admin/shipping",
        icon: Truck,
      },
      {
        label: "KYC Review",
        href: "/admin/kyc",
        icon: ShieldCheck,
      },
      {
        label: "Audit Logs",
        href: "/admin/audit-logs",
        icon: FileClock,
      },
    ],
  },
  {
    title: "Gazette Management",
    items: [
      {
        label: "Overview",
        href: "/admin/gazette",
        icon: ScrollText,
      },
      {
        label: "Upload PDF",
        href: "/admin/gazette#upload",
        icon: UploadCloud,
      },
      {
        label: "Review Rules",
        href: "/admin/gazette#review",
        icon: ClipboardCheck,
      },
      {
        label: "History",
        href: "/admin/gazette#history",
        icon: History,
      },
    ],
  },
];

function isActivePath(pathname: string, href: string) {
  const baseHref = href.split("#")[0];
  if (baseHref === "/admin") {
    return pathname === "/admin";
  }
  return pathname === baseHref || pathname.startsWith(`${baseHref}/`);
}

function AdminNavContent({ isMobile = false }: { isMobile?: boolean }) {
  const pathname = usePathname();
  const { logout, isLoading } = useLogout();

  return (
    <div className="flex h-full flex-col">
      <div className="px-6 py-6">
        <div className="flex items-center gap-3">
          <BrandMark className="h-14 w-14" />
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-[#546a7b]">
              ClearDrive
            </p>
            <p className="text-lg font-semibold text-[#393d3f]">
              Admin Terminal
            </p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-8 px-4 pb-6">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title}>
            <p className="px-3 text-[11px] font-semibold uppercase tracking-[0.35em] text-[#546a7b]">
              {section.title}
            </p>
            <div className="mt-3 space-y-1">
              {section.items.map((item) => {
                const active = isActivePath(pathname, item.href);
                const content = (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "group flex items-center gap-3 rounded-xl border px-3 py-2 text-sm font-medium transition",
                      active
                        ? "border-[#62929e]/40 bg-[#62929e]/15 text-[#393d3f] shadow-md shadow-black/10"
                        : "border-transparent text-[#546a7b] hover:border-[#546a7b]/65 hover:bg-[#c6c5b9]/20 hover:text-[#393d3f]",
                    )}
                  >
                    <item.icon
                      className={cn(
                        "h-4 w-4",
                        active
                          ? "text-[#62929e]"
                          : "text-[#546a7b] group-hover:text-[#62929e]",
                      )}
                    />
                    <span>{item.label}</span>
                  </Link>
                );

                if (isMobile) {
                  return (
                    <SheetClose asChild key={item.href}>
                      {content}
                    </SheetClose>
                  );
                }

                return <div key={item.href}>{content}</div>;
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="px-6 pb-6">
        {isMobile ? (
          <SheetClose asChild>
            <button
              type="button"
              onClick={logout}
              disabled={isLoading}
              className="mb-3 flex w-full items-center justify-center gap-2 rounded-xl border border-[#546a7b]/65 bg-[#62929e] px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#fdfdff] shadow-sm transition hover:bg-[#4f7d87] disabled:cursor-not-allowed disabled:opacity-70"
            >
              <LogOut className="h-4 w-4" />
              {isLoading ? "Signing Out" : "Sign Out"}
            </button>
          </SheetClose>
        ) : (
          <button
            type="button"
            onClick={logout}
            disabled={isLoading}
            className="mb-3 flex w-full items-center justify-center gap-2 rounded-xl border border-[#546a7b]/65 bg-[#62929e] px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#fdfdff] shadow-sm transition hover:bg-[#4f7d87] disabled:cursor-not-allowed disabled:opacity-70"
          >
            <LogOut className="h-4 w-4" />
            {isLoading ? "Signing Out" : "Sign Out"}
          </button>
        )}
        <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4 text-xs text-[#546a7b] shadow-md shadow-black/5">
          <p className="text-[10px] uppercase tracking-[0.3em] text-[#546a7b]">
            System
          </p>
          <p className="mt-2 text-sm font-semibold text-[#393d3f]">
            Admin operations are live.
          </p>
          <p className="mt-1 text-xs text-[#546a7b]">
            Monitor audit logs and gazette approvals regularly.
          </p>
        </div>
      </div>
    </div>
  );
}

export function AdminSidebar() {
  return (
    <aside className="hidden w-72 flex-col border-r border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-xl lg:flex">
      <AdminNavContent />
    </aside>
  );
}

export function AdminMobileNav() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[#393d3f] shadow-sm transition hover:bg-[#c6c5b9]/30"
        >
          <Menu className="h-4 w-4" />
          Menu
        </button>
      </SheetTrigger>
      <SheetContent
        side="left"
        className="border-r border-[#546a7b]/65 bg-[#fdfdff]/95 p-0 text-[#393d3f] backdrop-blur-2xl"
      >
        <AdminNavContent isMobile />
      </SheetContent>
    </Sheet>
  );
}
