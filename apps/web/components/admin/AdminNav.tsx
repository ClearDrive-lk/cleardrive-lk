"use client";

import type { ComponentType } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  ShoppingBag,
  Truck,
  ShieldCheck,
  FileClock,
  ScrollText,
  UploadCloud,
  ClipboardCheck,
  History,
  Menu,
} from "lucide-react";

import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";
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

  return (
    <div className="flex h-full flex-col">
      <div className="px-6 py-6">
        <div className="flex items-center gap-3">
          <BrandMark className="h-11 w-11 rounded-2xl border border-[#62929e]/30 bg-[#62929e]/10 p-2 shadow-lg shadow-[0_0_16px_rgba(98,146,158,0.2)]" />
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
                      "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition",
                      active
                        ? "bg-[#c6c5b9]/30 text-[#393d3f] border border-[#546a7b]/65"
                        : "text-[#546a7b] hover:bg-[#c6c5b9]/20 hover:text-[#393d3f]",
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
        <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4 text-xs text-[#546a7b]">
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
    <aside className="hidden w-72 flex-col border-r border-[#546a7b]/65 bg-[#fdfdff] lg:flex">
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
          className="inline-flex items-center gap-2 rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-gray-200 shadow-sm transition hover:bg-[#c6c5b9]/30"
        >
          <Menu className="h-4 w-4" />
          Menu
        </button>
      </SheetTrigger>
      <SheetContent
        side="left"
        className="border-r border-slate-900/70 bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900 p-0 text-[#393d3f]"
      >
        <AdminNavContent isMobile />
      </SheetContent>
    </Sheet>
  );
}
