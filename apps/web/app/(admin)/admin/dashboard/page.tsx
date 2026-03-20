"use client";

import { useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import { isAxiosError } from "axios";
import {
  Activity,
  CalendarRange,
  CircleAlert,
  CircleDollarSign,
  Download,
  FileText,
  RefreshCcw,
  ShieldCheck,
  ShoppingCart,
  Users,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { apiClient } from "@/lib/api-client";

interface DashboardStats {
  total_users: number;
  active_users: number;
  new_users_today: number;
  total_orders: number;
  pending_orders: number;
  in_progress_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  total_revenue: number;
  revenue_today: number;
  avg_order_value: number;
  kyc_pending: number;
  kyc_approved: number;
  kyc_rejected: number;
}
interface DailyCount {
  date: string;
  count: number;
}
interface UserAnalytics {
  daily_registrations: DailyCount[];
  role_distribution: Record<string, number>;
  kyc_status_distribution: Record<string, number>;
}
interface OrderAnalytics {
  status_distribution: Record<string, number>;
}
interface RevenueAnalytics {
  daily_revenue: Array<{ date: string; amount: number }>;
  payment_method_breakdown: Record<string, number>;
  top_revenue_sources: Array<{
    source: string;
    amount: number;
    percentage: number;
  }>;
  revenue_growth_rate: number;
}

const REFRESH_INTERVAL_MS = 30_000;
const CUSTOM_RANGE = "custom";
const QUICK_RANGES = [7, 30, 90, 365] as const;
const CHART_COLORS = ["#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];
const COMPACT_NUMBER = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

function formatCompact(value: number) {
  return COMPACT_NUMBER.format(value);
}

function KPI({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <article className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#546a7b]">
          {title}
        </p>
        <span className="rounded-lg border border-[#546a7b]/65 bg-[#fdfdff]/70 p-2 text-[#393d3f]">
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <p className="text-3xl font-semibold text-[#393d3f]">{value}</p>
      <p className="mt-1 text-sm text-[#546a7b]">{subtitle}</p>
    </article>
  );
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [userAnalytics, setUserAnalytics] = useState<UserAnalytics | null>(
    null,
  );
  const [orderAnalytics, setOrderAnalytics] = useState<OrderAnalytics | null>(
    null,
  );
  const [revenueAnalytics, setRevenueAnalytics] =
    useState<RevenueAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRange, setSelectedRange] = useState<string>("30");
  const [customStartDate, setCustomStartDate] = useState("");
  const [customEndDate, setCustomEndDate] = useState("");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const getDays = () => {
    if (selectedRange !== CUSTOM_RANGE) return Number(selectedRange);
    if (!customStartDate || !customEndDate) return 30;
    const diff =
      new Date(customEndDate).getTime() - new Date(customStartDate).getTime();
    return Math.max(1, Math.min(365, Math.floor(diff / 86400000) + 1));
  };

  const loadDashboardData = async (silent = false) => {
    if (silent) setRefreshing(true);
    else setLoading(true);
    try {
      setError(null);
      const days = getDays();
      const [statsRes, userRes, orderRes, revenueRes] = await Promise.all([
        apiClient.get<DashboardStats>("/admin/dashboard/stats"),
        apiClient.get<UserAnalytics>(`/admin/dashboard/users?days=${days}`),
        apiClient.get<OrderAnalytics>(`/admin/dashboard/orders?days=${days}`),
        apiClient.get<RevenueAnalytics>(
          `/admin/dashboard/revenue?days=${days}`,
        ),
      ]);
      setStats(statsRes.data);
      setUserAnalytics(userRes.data);
      setOrderAnalytics(orderRes.data);
      setRevenueAnalytics(revenueRes.data);
      setLastUpdated(new Date());
    } catch (err: unknown) {
      setError(
        isAxiosError(err)
          ? ((err.response?.data as { detail?: string } | undefined)?.detail ??
              "Failed to load dashboard data.")
          : "Failed to load dashboard data.",
      );
    } finally {
      if (silent) setRefreshing(false);
      else setLoading(false);
    }
  };

  useEffect(() => {
    void loadDashboardData();
    const interval = setInterval(
      () => void loadDashboardData(true),
      REFRESH_INTERVAL_MS,
    );
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRange, customStartDate, customEndDate]);

  const orderStatusData = useMemo(
    () =>
      orderAnalytics
        ? Object.entries(orderAnalytics.status_distribution).map(
            ([name, value]) => ({ name, value }),
          )
        : [],
    [orderAnalytics],
  );
  const paymentData = useMemo(
    () =>
      revenueAnalytics
        ? Object.entries(revenueAnalytics.payment_method_breakdown).map(
            ([name, amount]) => ({ name, amount }),
          )
        : [],
    [revenueAnalytics],
  );

  if (loading) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6 text-center text-[#393d3f]">
          <RefreshCcw className="mx-auto mb-3 h-8 w-8 animate-spin text-[#62929e]" />
          Loading admin analytics...
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center p-6">
        <div className="rounded-3xl border border-red-500/35 bg-red-500/10 p-6 text-center">
          <CircleAlert className="mx-auto mb-3 h-9 w-9 text-red-500" />
          <p className="text-lg font-semibold text-[#393d3f]">
            Dashboard failed to load
          </p>
          <p className="mt-1 text-sm text-red-600 dark:text-red-300">
            {error ?? "Unknown error"}
          </p>
          <button
            onClick={() => void loadDashboardData()}
            className="mt-4 rounded-xl bg-[#62929e] px-4 py-2 text-sm font-semibold text-[#fdfdff]"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="cd-container space-y-6 py-6 text-[#393d3f]">
      <header className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[#62929e]">
              Admin Intelligence
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-[#393d3f]">
              Platform Operations Dashboard
            </h1>
            <p className="mt-2 text-sm text-[#546a7b]">
              Auto-refresh every 30 seconds. Last update:{" "}
              {lastUpdated?.toLocaleTimeString() ?? "--:--:--"}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => void loadDashboardData(true)}
              className="rounded-xl border border-[#546a7b]/65 bg-[#fdfdff]/70 px-3 py-2 text-sm font-semibold text-[#393d3f]"
            >
              {refreshing ? "Refreshing..." : "Refresh"}
            </button>
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-2 rounded-xl border border-[#546a7b]/65 bg-[#fdfdff]/70 px-3 py-2 text-sm font-semibold text-[#393d3f]"
            >
              <FileText className="h-4 w-4" />
              Export PDF
            </button>
            <button
              onClick={() => {
                const rows = [
                  `stats,total_users,${stats.total_users}`,
                  `stats,total_orders,${stats.total_orders}`,
                  `stats,total_revenue,${stats.total_revenue}`,
                ];
                const blob = new Blob(
                  [`section,key,value\n${rows.join("\n")}`],
                  { type: "text/csv;charset=utf-8;" },
                );
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = `admin-dashboard-${new Date().toISOString().slice(0, 10)}.csv`;
                link.click();
                URL.revokeObjectURL(url);
              }}
              className="inline-flex items-center gap-2 rounded-xl border border-[#546a7b]/65 bg-[#fdfdff]/70 px-3 py-2 text-sm font-semibold text-[#393d3f]"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </button>
            <span className="inline-flex items-center gap-2 rounded-xl border border-[#546a7b]/65 bg-[#62929e]/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#546a7b]">
              <CalendarRange className="h-4 w-4 text-[#62929e]" />
              {getDays()} days
            </span>
          </div>
        </div>
      </header>

      <section className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4">
        <div className="flex flex-wrap gap-2">
          {QUICK_RANGES.map((range) => (
            <button
              key={range}
              onClick={() => setSelectedRange(String(range))}
              className={`rounded-xl border px-3 py-2 text-sm font-semibold ${selectedRange === String(range) ? "border-[#62929e]/40 bg-[#62929e]/15 text-[#393d3f]" : "border-[#546a7b]/65 bg-[#fdfdff]/70 text-[#546a7b]"}`}
            >
              Last {range} days
            </button>
          ))}
          <button
            onClick={() => setSelectedRange(CUSTOM_RANGE)}
            className={`rounded-xl border px-3 py-2 text-sm font-semibold ${selectedRange === CUSTOM_RANGE ? "border-[#62929e]/40 bg-[#62929e]/15 text-[#393d3f]" : "border-[#546a7b]/65 bg-[#fdfdff]/70 text-[#546a7b]"}`}
          >
            Custom
          </button>
        </div>
        {selectedRange === CUSTOM_RANGE ? (
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <input
              type="date"
              value={customStartDate}
              onChange={(e) => setCustomStartDate(e.target.value)}
              className="rounded-xl border border-[#546a7b]/65 bg-[#fdfdff]/80 px-3 py-2 text-sm text-[#393d3f]"
            />
            <input
              type="date"
              value={customEndDate}
              onChange={(e) => setCustomEndDate(e.target.value)}
              className="rounded-xl border border-[#546a7b]/65 bg-[#fdfdff]/80 px-3 py-2 text-sm text-[#393d3f]"
            />
          </div>
        ) : null}
      </section>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KPI
          title="Total Users"
          value={stats.total_users.toLocaleString()}
          subtitle={`${stats.active_users.toLocaleString()} active - +${stats.new_users_today} today`}
          icon={Users}
        />
        <KPI
          title="Orders"
          value={stats.total_orders.toLocaleString()}
          subtitle={`${stats.pending_orders} pending - ${stats.in_progress_orders} in progress`}
          icon={ShoppingCart}
        />
        <KPI
          title="Revenue"
          value={`$${stats.total_revenue.toLocaleString()}`}
          subtitle={`$${stats.revenue_today.toLocaleString()} today`}
          icon={CircleDollarSign}
        />
        <KPI
          title="Avg Order Value"
          value={`$${stats.avg_order_value.toLocaleString()}`}
          subtitle={`${stats.completed_orders.toLocaleString()} completed - ${stats.cancelled_orders} canceled`}
          icon={Activity}
        />
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
          <h2 className="mb-4 text-lg font-semibold text-[#393d3f]">
            User Growth
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={userAnalytics?.daily_registrations ?? []}>
              <CartesianGrid
                strokeDasharray="4 4"
                stroke="rgba(84,106,123,0.24)"
              />
              <XAxis
                dataKey="date"
                tickFormatter={(d) => format(new Date(d), "MMM d")}
                tick={{ fontSize: 12, fill: "#5f6c79" }}
              />
              <YAxis
                width={70}
                tickFormatter={(value) => formatCompact(Number(value))}
                tick={{ fontSize: 12, fill: "#5f6c79" }}
              />
              <Tooltip
                labelFormatter={(d) => format(new Date(d), "MMM d, yyyy")}
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke={CHART_COLORS[0]}
                strokeWidth={2.4}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              >
                <LabelList
                  dataKey="count"
                  position="top"
                  fill="#8fa3b1"
                  formatter={(value) => formatCompact(Number(value ?? 0))}
                />
              </Line>
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
          <h2 className="mb-4 text-lg font-semibold text-[#393d3f]">
            Order Status
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={orderStatusData}
                cx="50%"
                cy="50%"
                outerRadius={96}
                dataKey="value"
                labelLine={false}
                label={({ name, value }) =>
                  `${name}: ${formatCompact(Number(value ?? 0))}`
                }
              >
                {orderStatusData.map((_, i) => (
                  <Cell
                    key={`status-${i}`}
                    fill={CHART_COLORS[i % CHART_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
          <h2 className="mb-4 text-lg font-semibold text-[#393d3f]">
            Daily Revenue
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={revenueAnalytics?.daily_revenue ?? []}>
              <CartesianGrid
                strokeDasharray="4 4"
                stroke="rgba(84,106,123,0.24)"
              />
              <XAxis
                dataKey="date"
                tickFormatter={(d) => format(new Date(d), "MMM d")}
                tick={{ fontSize: 12, fill: "#5f6c79" }}
              />
              <YAxis
                width={82}
                tickFormatter={(value) => formatCompact(Number(value))}
                tick={{ fontSize: 12, fill: "#5f6c79" }}
              />
              <Tooltip
                formatter={(v) => [
                  `$${Number(v ?? 0).toLocaleString()}`,
                  "Revenue",
                ]}
              />
              <Bar
                dataKey="amount"
                fill={CHART_COLORS[1]}
                radius={[8, 8, 0, 0]}
              >
                <LabelList
                  dataKey="amount"
                  position="top"
                  fill="#8fa3b1"
                  formatter={(value) => `$${formatCompact(Number(value ?? 0))}`}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
          <h2 className="mb-4 text-lg font-semibold text-[#393d3f]">
            Payment Methods
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={paymentData}>
              <CartesianGrid
                strokeDasharray="4 4"
                stroke="rgba(84,106,123,0.24)"
              />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#5f6c79" }} />
              <YAxis
                width={82}
                tickFormatter={(value) => formatCompact(Number(value))}
                tick={{ fontSize: 12, fill: "#5f6c79" }}
              />
              <Tooltip
                formatter={(v) => [
                  `$${Number(v ?? 0).toLocaleString()}`,
                  "Amount",
                ]}
              />
              <Bar
                dataKey="amount"
                fill={CHART_COLORS[4]}
                radius={[8, 8, 0, 0]}
              >
                <LabelList
                  dataKey="amount"
                  position="top"
                  fill="#8fa3b1"
                  formatter={(value) => `$${formatCompact(Number(value ?? 0))}`}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <article className="rounded-2xl border border-amber-500/35 bg-amber-500/10 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-200">
            KYC Pending
          </p>
          <p className="mt-2 text-3xl font-semibold text-[#393d3f]">
            {stats.kyc_pending}
          </p>
        </article>
        <article className="rounded-2xl border border-emerald-500/35 bg-emerald-500/10 p-4">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-200">
              KYC Approved
            </p>
            <ShieldCheck className="h-4 w-4 text-emerald-200" />
          </div>
          <p className="mt-2 text-3xl font-semibold text-[#393d3f]">
            {stats.kyc_approved}
          </p>
        </article>
        <article className="rounded-2xl border border-red-500/35 bg-red-500/10 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-red-200">
            KYC Rejected
          </p>
          <p className="mt-2 text-3xl font-semibold text-[#393d3f]">
            {stats.kyc_rejected}
          </p>
        </article>
      </section>

      {revenueAnalytics?.top_revenue_sources?.length ? (
        <section className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
          <h2 className="mb-3 text-lg font-semibold text-[#393d3f]">
            Top Revenue Sources
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-[#546a7b]/40 text-left text-xs font-semibold uppercase tracking-[0.2em] text-[#546a7b]">
                  <th className="px-1 py-3">Source</th>
                  <th className="px-1 py-3">Revenue</th>
                  <th className="px-1 py-3">Share</th>
                </tr>
              </thead>
              <tbody>
                {revenueAnalytics.top_revenue_sources.map((src) => (
                  <tr
                    key={src.source}
                    className="border-b border-[#546a7b]/25 last:border-0"
                  >
                    <td className="px-1 py-3 font-medium text-[#393d3f]">
                      {src.source}
                    </td>
                    <td className="px-1 py-3 text-[#393d3f]">
                      ${src.amount.toLocaleString()}
                    </td>
                    <td className="px-1 py-3 text-[#546a7b]">
                      {src.percentage.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
