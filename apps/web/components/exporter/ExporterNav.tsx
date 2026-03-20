"use client";

import { useCallback, useEffect, useState } from "react";
import type { ComponentType } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ClipboardList,
  Flame,
  Ship,
  UploadCloud,
  Radar,
  User,
  Activity,
  Menu,
  LogOut,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import ThemeToggle from "@/components/ui/theme-toggle";
import { useLogout } from "@/lib/hooks/useLogout";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api-client";
import { BrandMark, BrandWordmark } from "@/components/ui/brand";
import { EXPORTER_TERMS } from "@/lib/exporter-phrases";

type NavItem = {
  label: string;
  shortLabel?: string;
  href: string;
  icon: ComponentType<{ className?: string }>;
};

const NAV_ITEMS: NavItem[] = [
  {
    label: "Assigned Orders",
    shortLabel: "Assigned",
    href: "/exporter",
    icon: ClipboardList,
  },
  {
    label: "Active",
    shortLabel: "Active",
    href: "/exporter/active",
    icon: Flame,
  },
  {
    label: "Shipping Details",
    shortLabel: "Shipping",
    href: "/exporter/shipping",
    icon: Ship,
  },
  {
    label: "Documents",
    shortLabel: "Docs",
    href: "/exporter/documents",
    icon: UploadCloud,
  },
  { label: "Tracking", href: "/exporter/tracking", icon: Radar },
  { label: "Profile", href: "/exporter/profile", icon: User },
];

const isActive = (pathname: string, href: string) => {
  if (href === "/exporter") {
    return pathname === href;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
};

export default function ExporterNav() {
  const pathname = usePathname();
  const { logout, isLoading } = useLogout();
  const [health, setHealth] = useState<"checking" | "healthy" | "unhealthy">(
    "checking",
  );
  const [lastChecked, setLastChecked] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const { data } = await apiClient.get<{ status?: string }>("/health");
      const isHealthy = data?.status === "healthy";
      setHealth(isHealthy ? "healthy" : "unhealthy");
    } catch {
      setHealth("unhealthy");
    } finally {
      setLastChecked(new Date().toLocaleTimeString());
    }
  }, []);

  useEffect(() => {
    void checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return (
    <nav className="sticky top-0 z-50 border-b border-[#546a7b]/40 bg-[#fdfdff]/82 backdrop-blur-xl dark:border-[#8fa3b1]/25 dark:bg-[#10191e]/82">
      <div className="cd-container h-16 flex items-center justify-between">
        <Link
          href="/exporter"
          className="font-bold text-xl tracking-tighter flex items-center gap-2 text-[#1f2937] dark:text-[#edf2f7]"
        >
          <BrandMark className="h-12 w-12" />
          <BrandWordmark />
        </Link>

        <div className="hidden md:flex items-center rounded-full border border-[#546a7b]/40 bg-[#c6c5b9]/20 px-2 py-1 dark:border-[#8fa3b1]/30 dark:bg-[#22313c]/70">
          {NAV_ITEMS.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.12em] transition-colors",
                  active
                    ? "bg-[#62929e]/12 text-[#1f2937] dark:bg-[#88d6e4]/14 dark:text-[#edf2f7]"
                    : "text-[#546a7b] hover:text-[#1f2937] dark:text-[#bdcad4] dark:hover:text-[#edf2f7]",
                )}
              >
                <item.icon className="h-3.5 w-3.5 text-[#62929e] dark:text-[#88d6e4]" />
                {item.shortLabel ?? item.label}
                {active && (
                  <span className="h-1.5 w-1.5 rounded-full bg-[#62929e] dark:bg-[#88d6e4]" />
                )}
              </Link>
            );
          })}
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <div
            className={cn(
              "hidden xl:flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-mono",
              health === "healthy"
                ? "border-emerald-500/35 text-emerald-700 dark:text-emerald-300"
                : health === "unhealthy"
                  ? "border-red-500/35 text-red-700 dark:text-red-300"
                  : "border-amber-500/35 text-amber-700 dark:text-amber-300",
            )}
          >
            <Activity className="h-3 w-3" />
            API {health === "checking" ? "CHECKING" : health.toUpperCase()}{" "}
            {lastChecked && (
              <span className="text-[10px] text-[#546a7b] dark:text-[#bdcad4]">
                {lastChecked}
              </span>
            )}
          </div>
          <Button
            onClick={logout}
            disabled={isLoading}
            className="hidden md:inline-flex bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
          >
            {isLoading ? "Signing Out..." : "Sign Out"}
          </Button>

          <Sheet>
            <SheetTrigger asChild>
              <Button
                size="icon"
                variant="outline"
                className="md:hidden border-[#546a7b]/45 text-[#1f2937] dark:border-[#8fa3b1]/35 dark:text-[#edf2f7]"
                aria-label="Open exporter navigation"
              >
                <Menu className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent
              className="w-[88vw] max-w-sm border-l border-[#546a7b]/35 bg-[#fdfdff] dark:border-[#8fa3b1]/30 dark:bg-[#111b21]"
              side="right"
            >
              <SheetHeader className="pr-8">
                <SheetTitle className="text-[#1f2937] dark:text-[#edf2f7]">
                  {EXPORTER_TERMS.opsBadge}
                </SheetTitle>
                <SheetDescription className="text-[#546a7b] dark:text-[#bdcad4]">
                  Navigate assigned orders, documents, and shipment milestones.
                </SheetDescription>
              </SheetHeader>

              <div className="px-4 pb-6 space-y-2">
                {NAV_ITEMS.map((item) => {
                  const active = isActive(pathname, item.href);
                  return (
                    <SheetClose asChild key={item.href}>
                      <Link
                        href={item.href}
                        className={cn(
                          "flex items-center justify-between rounded-xl border px-3 py-3 text-sm transition",
                          active
                            ? "border-[#62929e]/35 bg-[#62929e]/10 text-[#1f2937] dark:border-[#88d6e4]/35 dark:bg-[#88d6e4]/14 dark:text-[#edf2f7]"
                            : "border-[#546a7b]/35 bg-[#c6c5b9]/15 text-[#546a7b] hover:text-[#1f2937] dark:border-[#8fa3b1]/25 dark:bg-[#22313c]/60 dark:text-[#bdcad4] dark:hover:text-[#edf2f7]",
                        )}
                      >
                        <span className="inline-flex items-center gap-2">
                          <item.icon className="h-4 w-4 text-[#62929e] dark:text-[#88d6e4]" />
                          {item.label}
                        </span>
                        {active ? (
                          <Badge
                            variant="outline"
                            className="border-[#62929e]/30 text-[#62929e] dark:border-[#88d6e4]/40 dark:text-[#88d6e4]"
                          >
                            Active
                          </Badge>
                        ) : null}
                      </Link>
                    </SheetClose>
                  );
                })}
              </div>

              <div className="mt-auto border-t border-[#546a7b]/25 p-4 dark:border-[#8fa3b1]/20">
                <Button
                  onClick={logout}
                  disabled={isLoading}
                  className="w-full bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90"
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
