"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Activity,
  BellRing,
  CheckCircle2,
  Clock3,
  FileCheck2,
  LogOut,
  Mail,
  Package,
  Settings2,
  Shield,
  Sparkles,
  Terminal,
  User,
} from "lucide-react";

import AuthGuard from "@/components/auth/AuthGuard";
import { GDPRDataExport } from "@/components/gdpr/GDPRDataExport";
import CustomerDashboardNav from "@/components/layout/CustomerDashboardNav";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import apiClient from "@/lib/api-client";
import { useLogout } from "@/lib/hooks/useLogout";
import { useAppSelector } from "@/lib/store/store";

type OrderListItem = {
  status: string;
  total_cost_lkr: number | null;
  created_at: string;
};

type KycStatusResponse = {
  has_kyc: boolean;
  status: string | null;
  submitted_at: string | null;
  reviewed_at: string | null;
};

type ProfilePreferences = {
  emailUpdates: boolean;
  auctionAlerts: boolean;
  weeklyDigest: boolean;
};

type TimelineFilter = "all" | "account" | "orders" | "compliance";

const PROFILE_PREFS_KEY = "cleardrive-profile-preferences";

const DEFAULT_PREFERENCES: ProfilePreferences = {
  emailUpdates: true,
  auctionAlerts: true,
  weeklyDigest: false,
};

export default function ProfilePage() {
  const { user } = useAppSelector((state) => state.auth);
  const { logout, isLoading } = useLogout();

  const [orderStats, setOrderStats] = useState({
    total: 0,
    active: 0,
    completed: 0,
    avgValue: null as number | null,
    lastCreatedAt: null as string | null,
  });
  const [kycStatus, setKycStatus] = useState<KycStatusResponse | null>(null);
  const [loadingInsights, setLoadingInsights] = useState(true);
  const [insightsError, setInsightsError] = useState<string | null>(null);

  const [preferences, setPreferences] =
    useState<ProfilePreferences>(DEFAULT_PREFERENCES);
  const [timelineFilter, setTimelineFilter] = useState<TimelineFilter>("all");

  useEffect(() => {
    const raw = localStorage.getItem(PROFILE_PREFS_KEY);
    if (!raw) return;

    try {
      const parsed = JSON.parse(raw) as Partial<ProfilePreferences>;
      setPreferences({
        emailUpdates:
          parsed.emailUpdates ?? DEFAULT_PREFERENCES.emailUpdates,
        auctionAlerts:
          parsed.auctionAlerts ?? DEFAULT_PREFERENCES.auctionAlerts,
        weeklyDigest: parsed.weeklyDigest ?? DEFAULT_PREFERENCES.weeklyDigest,
      });
    } catch {
      // Ignore invalid stored preferences.
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(PROFILE_PREFS_KEY, JSON.stringify(preferences));
  }, [preferences]);

  useEffect(() => {
    let mounted = true;

    const loadInsights = async () => {
      setLoadingInsights(true);
      setInsightsError(null);

      try {
        const [ordersResponse, kycResponse] = await Promise.allSettled([
          apiClient.get<OrderListItem[]>("/orders"),
          apiClient.get<KycStatusResponse>("/kyc/status"),
        ]);

        if (!mounted) return;

        if (ordersResponse.status === "fulfilled") {
          const orders = ordersResponse.value.data ?? [];
          const total = orders.length;
          const active = orders.filter(
            (order) => !["DELIVERED", "CANCELLED"].includes(order.status),
          ).length;
          const completed = orders.filter(
            (order) => order.status === "DELIVERED",
          ).length;
          const avgValue =
            total === 0
              ? null
              : Math.round(
                  orders.reduce(
                    (sum, order) => sum + (order.total_cost_lkr ?? 0),
                    0,
                  ) / total,
                );
          const lastCreatedAt =
            orders
              .slice()
              .sort(
                (a, b) =>
                  new Date(b.created_at).getTime() -
                  new Date(a.created_at).getTime(),
              )[0]?.created_at ?? null;

          setOrderStats({
            total,
            active,
            completed,
            avgValue,
            lastCreatedAt,
          });
        } else {
          setInsightsError("Unable to load order insights right now.");
        }

        if (kycResponse.status === "fulfilled") {
          setKycStatus(kycResponse.value.data);
        }
      } finally {
        if (mounted) {
          setLoadingInsights(false);
        }
      }
    };

    void loadInsights();

    return () => {
      mounted = false;
    };
  }, []);

  const kycBadge = (() => {
    switch (kycStatus?.status) {
      case "APPROVED":
        return {
          label: "KYC Approved",
          className:
            "border border-emerald-500/30 bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-100",
        };
      case "REJECTED":
        return {
          label: "KYC Rejected",
          className:
            "border border-red-500/30 bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-100",
        };
      case "PENDING":
      case "PENDING_MANUAL_REVIEW":
        return {
          label: "KYC In Review",
          className:
            "border border-amber-500/30 bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-100",
        };
      default:
        return {
          label: "KYC Not Submitted",
          className:
            "border border-[#8fa3b1]/40 bg-[#d8e0e6] text-[#243746] dark:border-[#9fb8c9]/40 dark:bg-[#2a3d48] dark:text-[#d7e4ee]",
        };
    }
  })();

  const completionItems = [
    { label: "Name and email present", done: Boolean(user?.name && user?.email) },
    { label: "KYC submitted", done: Boolean(kycStatus?.has_kyc) },
    { label: "At least one order", done: orderStats.total > 0 },
    {
      label: "Notifications enabled",
      done: preferences.emailUpdates || preferences.auctionAlerts,
    },
  ];

  const completionPercent = Math.round(
    (completionItems.filter((item) => item.done).length /
      completionItems.length) *
      100,
  );

  const timelineItems = useMemo(() => {
    const items = [
      {
        category: "account" as const,
        title: "Profile is active",
        description:
          "Your account is ready to manage orders, verification, and alerts.",
        when: "Today",
      },
      {
        category: "compliance" as const,
        title: kycBadge.label,
        description: kycStatus?.submitted_at
          ? `Submitted on ${new Date(kycStatus.submitted_at).toLocaleDateString()}`
          : "Submit your NIC and selfie from the KYC tab to unlock approvals.",
        when: kycStatus?.submitted_at
          ? new Date(kycStatus.submitted_at).toLocaleDateString()
          : "Pending",
      },
      {
        category: "orders" as const,
        title:
          orderStats.total > 0
            ? `${orderStats.total} orders tracked`
            : "No orders tracked yet",
        description:
          orderStats.total > 0
            ? `${orderStats.active} active and ${orderStats.completed} completed orders in your queue.`
            : "Start from live auctions to create your first import order.",
        when: orderStats.lastCreatedAt
          ? new Date(orderStats.lastCreatedAt).toLocaleDateString()
          : "No activity",
      },
      {
        category: "account" as const,
        title: "Preference settings saved",
        description:
          "Your notification settings are applied to future account updates.",
        when: "Latest",
      },
    ];

    if (timelineFilter === "all") return items;
    return items.filter((item) => item.category === timelineFilter);
  }, [timelineFilter, kycBadge.label, kycStatus?.submitted_at, orderStats]);

  const togglePreference = (key: keyof ProfilePreferences) => {
    setPreferences((current) => ({ ...current, [key]: !current[key] }));
  };

  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#fdfdff] font-sans text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] dark:bg-[#0f1417] dark:text-[#edf2f7]">
        <CustomerDashboardNav />

        <section className="relative overflow-hidden pb-20 pt-14">
          <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px]" />
          <div className="pointer-events-none absolute left-1/2 top-[8%] h-[560px] w-[920px] -translate-x-1/2 rounded-[100%] bg-[#62929e]/10 blur-[120px] dark:bg-[#88d6e4]/10" />

          <div className="relative z-10 cd-container space-y-8">
            <header className="rounded-3xl border border-[#546a7b]/55 bg-[#fdfdff]/70 p-6 shadow-[0_18px_42px_rgba(15,23,42,0.12)] dark:border-[#8fa3b1]/35 dark:bg-[#131c21]/75 dark:shadow-[0_18px_42px_rgba(0,0,0,0.32)] md:p-8">
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#546a7b]/45 bg-[#c6c5b9]/20 px-4 py-1.5 font-mono text-xs uppercase tracking-[0.2em] text-[#62929e] dark:border-[#8fa3b1]/35 dark:bg-[#22313c] dark:text-[#88d6e4]">
                <Sparkles className="h-3.5 w-3.5" />
                Customer Profile
              </div>

              <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr] lg:items-end">
                <div>
                  <h1 className="text-4xl font-bold tracking-tight md:text-6xl">
                    YOUR{" "}
                    <span className="bg-gradient-to-r from-[#62929e] to-[#c6c5b9] bg-clip-text text-transparent dark:from-[#88d6e4] dark:to-[#9fb8c9]">
                      PROFILE.
                    </span>
                  </h1>
                  <p className="mt-4 max-w-2xl text-base text-[#546a7b] dark:text-[#bdcad4] md:text-lg">
                    Manage your personal details, KYC progress, notification
                    preferences, and order activity in one place.
                  </p>
                </div>

                <div className="rounded-2xl border border-[#546a7b]/40 bg-[#c6c5b9]/20 p-4 dark:border-[#8fa3b1]/35 dark:bg-[#22313c]/80">
                  <div className="mb-2 flex items-center justify-between text-xs uppercase tracking-[0.18em] text-[#546a7b] dark:text-[#bdcad4]">
                    <span>Profile Completion</span>
                    <span className="font-semibold text-[#393d3f] dark:text-[#edf2f7]">
                      {completionPercent}%
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-[#d5dde4] dark:bg-[#2f424e]">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-[#62929e] to-[#c6c5b9] transition-all duration-500 dark:from-[#88d6e4] dark:to-[#9fb8c9]"
                      style={{ width: `${completionPercent}%` }}
                    />
                  </div>
                  <p className="mt-3 text-xs text-[#546a7b] dark:text-[#bdcad4]">
                    Complete your profile details to unlock a smoother import
                    experience.
                  </p>
                </div>
              </div>
            </header>

            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.9fr)]">
              <div className="space-y-6">
                <section className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-2xl border border-[#546a7b]/50 bg-[#fdfdff]/70 p-5 dark:border-[#8fa3b1]/35 dark:bg-[#131c21]/75">
                    <div className="flex items-start gap-3">
                      <div className="rounded-xl border border-[#62929e]/30 bg-[#62929e]/15 p-2 text-[#62929e] dark:border-[#88d6e4]/35 dark:bg-[#88d6e4]/15 dark:text-[#88d6e4]">
                        <User className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-[0.18em] text-[#546a7b] dark:text-[#bdcad4]">
                          Full Name
                        </p>
                        <p className="mt-2 text-lg font-semibold text-[#393d3f] dark:text-[#edf2f7]">
                          {user?.name ?? "N/A"}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-[#546a7b]/50 bg-[#fdfdff]/70 p-5 dark:border-[#8fa3b1]/35 dark:bg-[#131c21]/75">
                    <div className="flex items-start gap-3">
                      <div className="rounded-xl border border-[#62929e]/30 bg-[#62929e]/15 p-2 text-[#62929e] dark:border-[#88d6e4]/35 dark:bg-[#88d6e4]/15 dark:text-[#88d6e4]">
                        <Mail className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs uppercase tracking-[0.18em] text-[#546a7b] dark:text-[#bdcad4]">
                          Email
                        </p>
                        <p className="mt-2 break-all text-base font-semibold text-[#393d3f] dark:text-[#edf2f7]">
                          {user?.email ?? "N/A"}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-[#546a7b]/50 bg-[#fdfdff]/70 p-5 dark:border-[#8fa3b1]/35 dark:bg-[#131c21]/75">
                    <div className="flex items-start gap-3">
                      <div className="rounded-xl border border-[#62929e]/30 bg-[#62929e]/15 p-2 text-[#62929e] dark:border-[#88d6e4]/35 dark:bg-[#88d6e4]/15 dark:text-[#88d6e4]">
                        <Shield className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-[0.18em] text-[#546a7b] dark:text-[#bdcad4]">
                          Role
                        </p>
                        <p className="mt-2 text-base font-semibold uppercase text-[#393d3f] dark:text-[#edf2f7]">
                          {user?.role ?? "N/A"}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-[#546a7b]/50 bg-[#fdfdff]/70 p-5 dark:border-[#8fa3b1]/35 dark:bg-[#131c21]/75">
                    <div className="flex items-start gap-3">
                      <div className="rounded-xl border border-[#62929e]/30 bg-[#62929e]/15 p-2 text-[#62929e] dark:border-[#88d6e4]/35 dark:bg-[#88d6e4]/15 dark:text-[#88d6e4]">
                        <Terminal className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs uppercase tracking-[0.18em] text-[#546a7b] dark:text-[#bdcad4]">
                          User ID
                        </p>
                        <p className="mt-2 break-all font-mono text-xs text-[#393d3f] dark:text-[#edf2f7]">
                          {user?.id ?? "N/A"}
                        </p>
                      </div>
                    </div>
                  </div>
                </section>

                <section className="rounded-3xl border border-[#546a7b]/55 bg-[#fdfdff]/70 p-6 dark:border-[#8fa3b1]/35 dark:bg-[#131c21]/75">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="text-xl font-semibold text-[#393d3f] dark:text-[#edf2f7]">
                        Import Progress Snapshot
                      </h2>
                      <p className="text-sm text-[#546a7b] dark:text-[#bdcad4]">
                        Quick overview of your orders and verification status.
                      </p>
                    </div>
                    <Badge className={kycBadge.className}>{kycBadge.label}</Badge>
                  </div>

                  {insightsError ? (
                    <p className="mt-4 rounded-xl border border-red-500/25 bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-200">
                      {insightsError}
                    </p>
                  ) : null}

                  <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    {[
                      {
                        label: "Orders",
                        value: String(orderStats.total),
                        hint: "Total created",
                      },
                      {
                        label: "Active",
                        value: String(orderStats.active),
                        hint: "In progress",
                      },
                      {
                        label: "Completed",
                        value: String(orderStats.completed),
                        hint: "Delivered",
                      },
                      {
                        label: "Average Value",
                        value: orderStats.avgValue
                          ? `LKR ${orderStats.avgValue.toLocaleString()}`
                          : "N/A",
                        hint: "Per order",
                      },
                    ].map((item) => (
                      <div
                        key={item.label}
                        className="rounded-2xl border border-[#546a7b]/40 bg-[#c6c5b9]/20 p-4 dark:border-[#8fa3b1]/35 dark:bg-[#22313c]/80"
                      >
                        <p className="text-[11px] uppercase tracking-[0.16em] text-[#546a7b] dark:text-[#bdcad4]">
                          {item.label}
                        </p>
                        <p className="mt-2 text-lg font-semibold text-[#393d3f] dark:text-[#edf2f7]">
                          {loadingInsights ? "..." : item.value}
                        </p>
                        <p className="mt-1 text-xs text-[#546a7b] dark:text-[#bdcad4]">
                          {item.hint}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="rounded-3xl border border-[#546a7b]/55 bg-[#fdfdff]/70 p-6 dark:border-[#8fa3b1]/35 dark:bg-[#131c21]/75">
                  <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="text-xl font-semibold text-[#393d3f] dark:text-[#edf2f7]">
                        Notification Preferences
                      </h2>
                      <p className="text-sm text-[#546a7b] dark:text-[#bdcad4]">
                        Choose how you want to receive account updates.
                      </p>
                    </div>
                    <Settings2 className="h-4 w-4 text-[#62929e] dark:text-[#88d6e4]" />
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    {[
                      {
                        key: "emailUpdates" as const,
                        label: "Email updates",
                        desc: "Receive order and compliance notices via email.",
                        icon: Mail,
                      },
                      {
                        key: "auctionAlerts" as const,
                        label: "Auction alerts",
                        desc: "Get notified when matching vehicles are listed.",
                        icon: BellRing,
                      },
                      {
                        key: "weeklyDigest" as const,
                        label: "Weekly digest",
                        desc: "One compact summary of profile and order activity.",
                        icon: Activity,
                      },
                    ].map((item) => (
                      <button
                        key={item.key}
                        type="button"
                        onClick={() => togglePreference(item.key)}
                        className={`rounded-2xl border p-4 text-left transition ${
                          preferences[item.key]
                            ? "border-[#62929e]/45 bg-[#62929e]/10 dark:border-[#88d6e4]/45 dark:bg-[#88d6e4]/15"
                            : "border-[#546a7b]/40 bg-[#c6c5b9]/20 hover:border-[#62929e]/35 dark:border-[#8fa3b1]/35 dark:bg-[#22313c]/80 dark:hover:border-[#88d6e4]/35"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-[#393d3f] dark:text-[#edf2f7]">
                              {item.label}
                            </p>
                            <p className="mt-1 text-xs text-[#546a7b] dark:text-[#bdcad4]">
                              {item.desc}
                            </p>
                          </div>
                          <item.icon className="h-4 w-4 text-[#62929e] dark:text-[#88d6e4]" />
                        </div>
                        <p className="mt-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-[#546a7b] dark:text-[#bdcad4]">
                          {preferences[item.key] ? "Enabled" : "Disabled"}
                        </p>
                      </button>
                    ))}
                  </div>
                </section>
              </div>

              <aside className="space-y-6">
                <section className="rounded-3xl border border-[#546a7b]/55 bg-[#fdfdff]/70 p-6 dark:border-[#8fa3b1]/35 dark:bg-[#131c21]/75">
                  <h2 className="text-lg font-semibold text-[#393d3f] dark:text-[#edf2f7]">
                    Profile Checklist
                  </h2>
                  <div className="mt-4 space-y-3">
                    {completionItems.map((item) => (
                      <div
                        key={item.label}
                        className="flex items-center justify-between rounded-xl border border-[#546a7b]/35 bg-[#c6c5b9]/20 px-3 py-2 dark:border-[#8fa3b1]/30 dark:bg-[#22313c]/75"
                      >
                        <p className="text-sm text-[#393d3f] dark:text-[#edf2f7]">
                          {item.label}
                        </p>
                        {item.done ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-300" />
                        ) : (
                          <Clock3 className="h-4 w-4 text-amber-600 dark:text-amber-300" />
                        )}
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Button
                      asChild
                      variant="outline"
                      className="border-[#546a7b]/55 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
                    >
                      <Link href="/dashboard/kyc">
                        <FileCheck2 className="mr-2 h-4 w-4" />
                        Open KYC
                      </Link>
                    </Button>
                    <Button
                      asChild
                      variant="outline"
                      className="border-[#546a7b]/55 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
                    >
                      <Link href="/dashboard/orders">
                        <Package className="mr-2 h-4 w-4" />
                        View Orders
                      </Link>
                    </Button>
                  </div>
                </section>

                <section className="rounded-3xl border border-[#546a7b]/55 bg-[#fdfdff]/70 p-6 dark:border-[#8fa3b1]/35 dark:bg-[#131c21]/75">
                  <h2 className="mb-3 text-lg font-semibold text-[#393d3f] dark:text-[#edf2f7]">
                    Recent Activity
                  </h2>
                  <div className="mb-4 flex flex-wrap gap-2">
                    {(["all", "account", "orders", "compliance"] as const).map(
                      (filter) => (
                        <button
                          key={filter}
                          type="button"
                          onClick={() => setTimelineFilter(filter)}
                          className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] transition ${
                            timelineFilter === filter
                              ? "border-[#62929e]/50 bg-[#62929e]/15 text-[#2f5862] dark:border-[#88d6e4]/45 dark:bg-[#88d6e4]/15 dark:text-[#d7e4ee]"
                              : "border-[#546a7b]/40 bg-[#c6c5b9]/20 text-[#546a7b] hover:text-[#393d3f] dark:border-[#8fa3b1]/35 dark:bg-[#22313c] dark:text-[#bdcad4] dark:hover:text-[#edf2f7]"
                          }`}
                        >
                          {filter}
                        </button>
                      ),
                    )}
                  </div>
                  <div className="space-y-3">
                    {timelineItems.map((item) => (
                      <div
                        key={`${item.category}-${item.title}`}
                        className="rounded-2xl border border-[#546a7b]/35 bg-[#c6c5b9]/20 p-3 dark:border-[#8fa3b1]/30 dark:bg-[#22313c]/75"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-sm font-semibold text-[#393d3f] dark:text-[#edf2f7]">
                            {item.title}
                          </p>
                          <span className="text-[11px] font-mono text-[#546a7b] dark:text-[#bdcad4]">
                            {item.when}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-[#546a7b] dark:text-[#bdcad4]">
                          {item.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="rounded-3xl border border-[#546a7b]/55 bg-[#fdfdff]/70 p-6 dark:border-[#8fa3b1]/35 dark:bg-[#131c21]/75">
                  <h2 className="text-lg font-semibold text-[#393d3f] dark:text-[#edf2f7]">
                    Account Actions
                  </h2>
                  <p className="mt-1 text-sm text-[#546a7b] dark:text-[#bdcad4]">
                    Manage privacy exports and secure sign-out.
                  </p>
                  <div className="mt-4">
                    <GDPRDataExport />
                  </div>
                  <Button
                    onClick={logout}
                    disabled={isLoading}
                    variant="outline"
                    className="mt-4 w-full border-[#546a7b]/55 bg-transparent text-[#393d3f] hover:bg-[#c6c5b9]/20 dark:border-[#8fa3b1]/35 dark:text-[#edf2f7] dark:hover:bg-[#22313c]"
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    {isLoading ? "Signing out..." : "Sign Out & Return to Login"}
                  </Button>
                </section>
              </aside>
            </div>
          </div>
        </section>
      </div>
    </AuthGuard>
  );
}
