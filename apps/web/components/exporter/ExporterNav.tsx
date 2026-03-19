"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ClipboardList,
  Ship,
  UploadCloud,
  Radar,
  User,
  Terminal,
  Activity,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import ThemeToggle from "@/components/ui/theme-toggle";
import { useLogout } from "@/lib/hooks/useLogout";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api-client";

const NAV_ITEMS = [
  { label: "Assigned Orders", href: "/exporter", icon: ClipboardList },
  { label: "Shipping Details", href: "/exporter/shipping", icon: Ship },
  { label: "Documents", href: "/exporter/documents", icon: UploadCloud },
  { label: "Tracking", href: "/exporter/tracking", icon: Radar },
  { label: "Profile", href: "/exporter/profile", icon: User },
];

const isActive = (pathname: string, href: string) =>
  pathname === href || pathname.startsWith(`${href}/`);

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
    <nav className="border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="cd-container h-16 flex items-center justify-between">
        <Link
          href="/exporter"
          className="font-bold text-xl tracking-tighter flex items-center gap-2"
        >
          <div className="w-8 h-8 bg-[#62929e]/10 border border-[#62929e]/20 rounded-md flex items-center justify-center">
            <Terminal className="w-4 h-4 text-[#62929e]" />
          </div>
          ClearDrive<span className="text-[#62929e]">.lk</span>
        </Link>
        <div className="hidden md:flex gap-6 text-sm font-medium text-[#546a7b]">
          {NAV_ITEMS.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 transition-colors",
                  active ? "text-[#393d3f]" : "hover:text-[#393d3f]",
                )}
              >
                <item.icon className="w-4 h-4 text-[#62929e]/80" />
                {item.label}
                {active && (
                  <Badge
                    variant="outline"
                    className="text-[10px] border-[#62929e]/20 text-[#62929e] h-4 px-1"
                  >
                    ACTIVE
                  </Badge>
                )}
              </Link>
            );
          })}
        </div>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <div
            className={cn(
              "hidden md:flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-mono",
              health === "healthy"
                ? "border-emerald-500/30 text-emerald-300"
                : health === "unhealthy"
                  ? "border-red-500/30 text-red-300"
                  : "border-amber-500/30 text-amber-300",
            )}
          >
            <Activity className="h-3 w-3" />
            API {health === "checking" ? "CHECKING" : health.toUpperCase()}
            {lastChecked && (
              <span className="text-[10px] text-[#546a7b]">{lastChecked}</span>
            )}
          </div>
          <Button
            onClick={logout}
            disabled={isLoading}
            className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
          >
            {isLoading ? "Signing Out..." : "Sign Out"}
          </Button>
        </div>
      </div>
    </nav>
  );
}
