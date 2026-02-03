"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LayoutDashboard,
  ShoppingCart,
  FileText,
  Settings,
  LogOut,
  Bell,
  User,
} from "lucide-react";
import ReduxTest from "@/components/debug/ReduxTest";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-[#050505] text-white flex font-sans">
      {/* --- SIDEBAR --- */}
      <aside className="w-64 border-r border-white/10 bg-[#0A0A0A] hidden md:flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-white/10">
          <span className="font-bold text-xl tracking-tighter">
            CD<span className="text-[#FE7743]">.lk</span>
          </span>
        </div>

        <div className="flex-1 py-6 px-3 space-y-1">
          {[
            { icon: LayoutDashboard, label: "Overview", active: true },
            { icon: ShoppingCart, label: "My Orders" },
            { icon: FileText, label: "Documents" },
            { icon: Settings, label: "Settings" },
          ].map((item, i) => (
            <button
              key={i}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${item.active ? "bg-[#FE7743]/10 text-[#FE7743]" : "text-gray-400 hover:text-white hover:bg-white/5"}`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </div>

        <div className="p-4 border-t border-white/10">
          <button className="w-full flex items-center gap-3 px-3 py-2 text-gray-400 hover:text-red-400 transition-colors text-sm">
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* --- MAIN CONTENT --- */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-16 border-b border-white/10 bg-[#050505]/80 backdrop-blur flex items-center justify-between px-6 sticky top-0 z-40">
          <div className="text-sm text-gray-400 font-mono">
            TERMINAL &gt; DASHBOARD
          </div>
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              className="text-gray-400 hover:text-white"
            >
              <Bell className="w-5 h-5" />
            </Button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#FE7743] to-purple-600 border border-white/20" />
          </div>
        </header>

        {/* Dashboard Content */}
        <main className="flex-1 p-6 relative overflow-hidden">
          {/* Background Glow */}
          <div className="absolute top-0 left-0 w-full h-96 bg-[#FE7743]/5 blur-[100px] pointer-events-none" />

          <div className="relative z-10 max-w-6xl mx-auto space-y-6">
            <h1 className="text-3xl font-bold tracking-tight">
              Terminal Overview
            </h1>

            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { title: "Pending Orders", value: "2", sub: "Action required" },
                {
                  title: "Est. Cost Calculator",
                  value: "JPY/LKR",
                  sub: "2.25 Live Rate",
                },
                {
                  title: "Account Status",
                  value: "Active",
                  sub: "Level 1 Verified",
                  color: "text-green-500",
                },
              ].map((card, i) => (
                <Card
                  key={i}
                  className="bg-[#0A0A0A]/50 border-white/10 backdrop-blur"
                >
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-400">
                      {card.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div
                      className={`text-2xl font-bold ${card.color || "text-white"}`}
                    >
                      {card.value}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{card.sub}</p>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Empty State / Content Placeholder */}
            <div className="rounded-xl border border-dashed border-white/10 bg-white/5 h-64 flex flex-col items-center justify-center text-gray-500 gap-4">
              <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center">
                <LayoutDashboard className="w-6 h-6 opacity-50" />
              </div>
              <p>No active auctions selected.</p>
              <Button
                variant="outline"
                className="border-white/10 hover:bg-white/5 hover:text-white"
              >
                Browse Auction House
              </Button>
            </div>
          </div>

          {/* Keep Redux Test for Debugging */}
          <ReduxTest />
        </main>
      </div>
    </div>
  );
}
