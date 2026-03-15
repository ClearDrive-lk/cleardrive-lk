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
  Terminal,
} from "lucide-react";

import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

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
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#FE7743]/10 border border-[#FE7743]/30 text-[#FE7743] shadow-lg shadow-orange-500/20">
            <Terminal className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-gray-500">
              ClearDrive
            </p>
            <p className="text-lg font-semibold text-white">Admin Terminal</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-8 px-4 pb-6">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title}>
            <p className="px-3 text-[11px] font-semibold uppercase tracking-[0.35em] text-gray-500">
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
                        ? "bg-white/10 text-white border border-white/10"
                        : "text-gray-300 hover:bg-white/5 hover:text-white",
                    )}
                  >
                    <item.icon
                      className={cn(
                        "h-4 w-4",
                        active
                          ? "text-[#FE7743]"
                          : "text-gray-400 group-hover:text-[#FE7743]",
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
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-xs text-gray-300">
          <p className="text-[10px] uppercase tracking-[0.3em] text-gray-500">
            System
          </p>
          <p className="mt-2 text-sm font-semibold text-white">
            Admin operations are live.
          </p>
          <p className="mt-1 text-xs text-gray-400">
            Monitor audit logs and gazette approvals regularly.
          </p>
        </div>
      </div>
    </div>
  );
}

export function AdminSidebar() {
  return (
    <aside className="hidden w-72 flex-col border-r border-white/10 bg-[#050505] lg:flex">
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
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-gray-200 shadow-sm transition hover:bg-white/10"
        >
          <Menu className="h-4 w-4" />
          Menu
        </button>
      </SheetTrigger>
      <SheetContent
        side="left"
        className="border-r border-slate-900/70 bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900 p-0 text-white"
      >
        <AdminNavContent isMobile />
      </SheetContent>
    </Sheet>
  );
}
