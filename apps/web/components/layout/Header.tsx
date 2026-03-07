"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAppSelector } from "@/lib/store/store";
import { Terminal, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useLogout } from "@/lib/hooks/useLogout";

/**
 * Header Component - Matching homepage design
 */
export default function Header() {
  const pathname = usePathname();
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const { logout, isLoading } = useLogout();

  const isActive = (path: string) => pathname === path;

  return (
    <nav className="border-b border-white/10 bg-[#050505]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link
          href="/"
          className="font-bold text-xl tracking-tighter flex items-center gap-2"
        >
          <div className="w-8 h-8 bg-[#FE7743]/10 border border-[#FE7743]/20 rounded-md flex items-center justify-center">
            <Terminal className="w-4 h-4 text-[#FE7743]" />
          </div>
          ClearDrive<span className="text-[#FE7743]">.lk</span>
        </Link>

        {/* Navigation Links */}
        <div className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
          <Link
            href="/"
            className={`transition-colors ${
              isActive("/") ? "text-white" : "hover:text-white"
            }`}
          >
            Home
          </Link>

          {isAuthenticated && (
            <>
              <Link
                href="/dashboard"
                className={`transition-colors flex items-center gap-2 ${
                  isActive("/dashboard") ? "text-white" : "hover:text-white"
                }`}
              >
                Dashboard
                {isActive("/dashboard") && (
                  <Badge
                    variant="outline"
                    className="text-[10px] border-[#FE7743]/20 text-[#FE7743] h-4 px-1"
                  >
                    ACTIVE
                  </Badge>
                )}
              </Link>
              <Link
                href="/dashboard/orders"
                className={`transition-colors ${
                  isActive("/dashboard/orders")
                    ? "text-white"
                    : "hover:text-white"
                }`}
              >
                Orders
              </Link>
              <Link
                href="/dashboard/vehicles"
                className={`transition-colors ${
                  isActive("/dashboard/vehicles")
                    ? "text-white"
                    : "hover:text-white"
                }`}
              >
                Vehicles
              </Link>
              <Link
                href="/dashboard/profile"
                className={`transition-colors ${
                  isActive("/dashboard/profile")
                    ? "text-white"
                    : "hover:text-white"
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
              <span className="hidden md:block text-sm text-gray-400 font-mono">
                {user?.name}
              </span>
              <Button
                onClick={logout}
                disabled={isLoading}
                variant="ghost"
                className="text-gray-400 hover:text-white hover:bg-white/5 font-mono flex items-center gap-2"
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
                  className="text-gray-400 hover:text-white hover:bg-white/5 font-mono"
                >
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button className="bg-[#FE7743] text-black hover:bg-[#FE7743]/90 font-bold">
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
