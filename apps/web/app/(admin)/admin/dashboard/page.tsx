"use client";

/**
 * CD-61: Admin Dashboard Analytics
 * File: apps/web/app/(admin)/admin/dashboard/page.tsx
 *
 * Displays KPI cards, trend charts, and platform health metrics.
 * Auto-refreshes every 30 seconds.
 *
 * Dependencies (run once):
 *   npm install recharts@3 date-fns@4
 */

import {
  type ComponentType,
  type ReactNode,
  useEffect,
  useMemo,
  useState,
} from "react";
import { isAxiosError } from "axios";
import { apiClient } from "@/lib/api-client";
import * as Recharts from "recharts";
import { format } from "date-fns";

type ChartComponentProps = Record<string, unknown> & { children?: ReactNode };

const LineChart =
  Recharts.LineChart as unknown as ComponentType<ChartComponentProps>;
const Line = Recharts.Line as unknown as ComponentType<ChartComponentProps>;
const BarChart =
  Recharts.BarChart as unknown as ComponentType<ChartComponentProps>;
const Bar = Recharts.Bar as unknown as ComponentType<ChartComponentProps>;
const PieChart =
  Recharts.PieChart as unknown as ComponentType<ChartComponentProps>;
const Pie = Recharts.Pie as unknown as ComponentType<ChartComponentProps>;
const Cell = Recharts.Cell as unknown as ComponentType<ChartComponentProps>;
const XAxis = Recharts.XAxis as unknown as ComponentType<ChartComponentProps>;
const YAxis = Recharts.YAxis as unknown as ComponentType<ChartComponentProps>;
const CartesianGrid =
  Recharts.CartesianGrid as unknown as ComponentType<ChartComponentProps>;
const Tooltip =
  Recharts.Tooltip as unknown as ComponentType<ChartComponentProps>;
const Legend = Recharts.Legend as unknown as ComponentType<ChartComponentProps>;
const ResponsiveContainer =
  Recharts.ResponsiveContainer as unknown as ComponentType<ChartComponentProps>;

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface DashboardStats {
  total_users: number;
  active_users: number;
  new_users_today: number;
  new_users_this_week: number;
  new_users_this_month: number;
  total_orders: number;
  pending_orders: number;
  in_progress_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  total_revenue: number;
  revenue_today: number;
  revenue_this_week: number;
  revenue_this_month: number;
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
  active_users_trend: DailyCount[];
  top_registration_days: DailyCount[];
}

interface OrderAnalytics {
  status_distribution: Record<string, number>;
  daily_orders: DailyCount[];
  avg_processing_time_days: number;
  completion_rate: number;
  cancellation_rate: number;
  orders_by_vehicle_type: Record<string, number>;
}

interface RevenueDataPoint {
  date: string;
  amount: number;
}

interface RevenueAnalytics {
  daily_revenue: RevenueDataPoint[];
  monthly_revenue: Array<{ month: string; amount: number }>;
  payment_method_breakdown: Record<string, number>;
  top_revenue_sources: Array<{
    source: string;
    amount: number;
    percentage: number;
  }>;
  revenue_growth_rate: number;
}

interface PieLabelRendererProps {
  name?: string;
  percent?: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const CHART_COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8"];
const REFRESH_INTERVAL_MS = 30_000; // 30 seconds

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle: string;
  icon: string;
  iconColor?: string;
}

function KpiCard({
  title,
  value,
  subtitle,
  icon,
  iconColor = "text-blue-600",
}: KpiCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-500 text-sm">{title}</p>
          <p className="text-3xl font-bold mt-1">{value}</p>
          <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
        </div>
        <div className={`text-4xl ${iconColor}`}>{icon}</div>
      </div>
    </div>
  );
}

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  valueColor?: string;
}

function MetricCard({
  title,
  value,
  subtitle,
  valueColor = "text-gray-800",
}: MetricCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className={`text-3xl font-bold ${valueColor}`}>{value}</p>
      <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

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
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  // ── Data fetching ──────────────────────────────────────────────────────────
  const loadDashboardData = async () => {
    try {
      setError(null);
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
    } catch (err: unknown) {
      console.error("Failed to load dashboard data:", err);
      if (isAxiosError(err)) {
        setError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to load dashboard data.",
        );
      } else {
        setError("Failed to load dashboard data.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    loadDashboardData();

    // Auto-refresh every 30 s
    const interval = setInterval(loadDashboardData, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  // ── Memoised chart data (avoids expensive re-computation on every render) ──
  const roleChartData = useMemo(
    () =>
      userAnalytics
        ? Object.entries(userAnalytics.role_distribution).map(
            ([name, value]) => ({
              name,
              value,
            }),
          )
        : [],
    [userAnalytics],
  );

  const statusChartData = useMemo(
    () =>
      orderAnalytics
        ? Object.entries(orderAnalytics.status_distribution).map(
            ([name, value]) => ({
              name,
              value,
            }),
          )
        : [],
    [orderAnalytics],
  );

  const kycChartData = useMemo(
    () =>
      userAnalytics
        ? Object.entries(userAnalytics.kyc_status_distribution).map(
            ([name, value]) => ({
              name,
              value,
            }),
          )
        : [],
    [userAnalytics],
  );

  const paymentChartData = useMemo(
    () =>
      revenueAnalytics
        ? Object.entries(revenueAnalytics.payment_method_breakdown).map(
            ([name, amount]) => ({
              name,
              amount,
            }),
          )
        : [],
    [revenueAnalytics],
  );

  // ── Loading / error states ────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="text-4xl mb-4">⏳</div>
          <p className="text-xl text-gray-600">Loading dashboard…</p>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <p className="text-xl text-red-600">{error ?? "Unknown error"}</p>
          <button
            onClick={loadDashboardData}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="p-6 space-y-6">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Platform overview and analytics</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Auto-refresh indicator */}
          <span className="text-xs text-gray-400">Auto-refresh: 30s</span>

          {/* Date range selector */}
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
        </div>
      </div>

      {/* ── KPI Cards ─────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KpiCard
          title="Total Users"
          value={stats.total_users.toLocaleString()}
          subtitle={`+${stats.new_users_today} today · ${stats.active_users.toLocaleString()} active`}
          icon="👥"
          iconColor="text-blue-600"
        />
        <KpiCard
          title="Total Orders"
          value={stats.total_orders.toLocaleString()}
          subtitle={`${stats.pending_orders} pending · ${stats.in_progress_orders} in-progress`}
          icon="📦"
          iconColor="text-orange-500"
        />
        <KpiCard
          title="Total Revenue"
          value={`$${stats.total_revenue.toLocaleString()}`}
          subtitle={`$${stats.revenue_today.toLocaleString()} today`}
          icon="💰"
          iconColor="text-green-600"
        />
        <KpiCard
          title="Avg Order Value"
          value={`$${stats.avg_order_value.toLocaleString()}`}
          subtitle={`${stats.completed_orders.toLocaleString()} completed orders`}
          icon="📊"
          iconColor="text-purple-600"
        />
      </div>

      {/* ── KYC quick-stats bar ───────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-4">
        {[
          {
            label: "KYC Pending",
            value: stats.kyc_pending,
            color: "bg-yellow-100 text-yellow-800",
          },
          {
            label: "KYC Approved",
            value: stats.kyc_approved,
            color: "bg-green-100 text-green-800",
          },
          {
            label: "KYC Rejected",
            value: stats.kyc_rejected,
            color: "bg-red-100 text-red-800",
          },
        ].map(({ label, value, color }) => (
          <div
            key={label}
            className={`rounded-lg px-4 py-3 ${color} flex items-center justify-between`}
          >
            <span className="text-sm font-medium">{label}</span>
            <span className="text-xl font-bold">{value}</span>
          </div>
        ))}
      </div>

      {/* ── Charts Row 1 ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Growth – Line Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">User Growth</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={userAnalytics?.daily_registrations ?? []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(d: string) => format(new Date(d), "MMM d")}
                tick={{ fontSize: 12 }}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                labelFormatter={(d: string) =>
                  format(new Date(d), "MMM d, yyyy")
                }
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="count"
                stroke={CHART_COLORS[0]}
                strokeWidth={2}
                dot={false}
                name="New Users"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Order Status – Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Order Status Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusChartData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                labelLine={false}
                label={({ name, percent }: PieLabelRendererProps) =>
                  `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`
                }
              >
                {statusChartData.map((_, i) => (
                  <Cell
                    key={`cell-${i}`}
                    fill={CHART_COLORS[i % CHART_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Charts Row 2 ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Revenue – Bar Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Daily Revenue</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={revenueAnalytics?.daily_revenue ?? []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(d: string) => format(new Date(d), "MMM d")}
                tick={{ fontSize: 12 }}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                labelFormatter={(d: string) =>
                  format(new Date(d), "MMM d, yyyy")
                }
                formatter={(v: number | string) => [
                  `$${Number(v ?? 0).toLocaleString()}`,
                  "Revenue",
                ]}
              />
              <Legend />
              <Bar
                dataKey="amount"
                fill={CHART_COLORS[1]}
                name="Revenue"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* User Roles – Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">User Role Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={roleChartData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                labelLine={false}
                label={({ name, percent }: PieLabelRendererProps) =>
                  `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`
                }
              >
                {roleChartData.map((_, i) => (
                  <Cell
                    key={`cell-${i}`}
                    fill={CHART_COLORS[i % CHART_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Charts Row 3 – KYC & Payment breakdown ────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* KYC Status – Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">KYC Status Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={kycChartData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                labelLine={false}
                label={({ name, percent }: PieLabelRendererProps) =>
                  `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`
                }
              >
                {kycChartData.map((_, i) => (
                  <Cell
                    key={`cell-${i}`}
                    fill={CHART_COLORS[i % CHART_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Payment Methods – Bar Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Revenue by Payment Method</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={paymentChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(v: number | string) => [
                  `$${Number(v ?? 0).toLocaleString()}`,
                  "Amount",
                ]}
              />
              <Legend />
              <Bar
                dataKey="amount"
                fill={CHART_COLORS[4]}
                name="Amount"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Summary Metric Cards ───────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <MetricCard
          title="Avg Processing Time"
          value={`${orderAnalytics?.avg_processing_time_days.toFixed(1) ?? "—"} days`}
          subtitle="Order created → delivered"
        />
        <MetricCard
          title="Order Completion Rate"
          value={`${orderAnalytics?.completion_rate.toFixed(1) ?? "—"}%`}
          subtitle="Successfully delivered"
          valueColor="text-green-600"
        />
        <MetricCard
          title="Revenue Growth"
          value={`${(revenueAnalytics?.revenue_growth_rate ?? 0) >= 0 ? "+" : ""}${revenueAnalytics?.revenue_growth_rate.toFixed(1) ?? "—"}%`}
          subtitle={`vs previous ${days} days`}
          valueColor={
            (revenueAnalytics?.revenue_growth_rate ?? 0) >= 0
              ? "text-green-600"
              : "text-red-600"
          }
        />
      </div>

      {/* ── Top Revenue Sources Table ──────────────────────────────────────── */}
      {revenueAnalytics && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Top Revenue Sources</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b text-gray-500 uppercase text-xs">
                  <th className="pb-3 pr-6">Source</th>
                  <th className="pb-3 pr-6">Revenue</th>
                  <th className="pb-3">Share</th>
                </tr>
              </thead>
              <tbody>
                {revenueAnalytics.top_revenue_sources.map((src) => (
                  <tr key={src.source} className="border-b last:border-0">
                    <td className="py-3 pr-6 font-medium">{src.source}</td>
                    <td className="py-3 pr-6">
                      $
                      {src.amount.toLocaleString(undefined, {
                        maximumFractionDigits: 0,
                      })}
                    </td>
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${src.percentage}%` }}
                          />
                        </div>
                        <span>{src.percentage.toFixed(1)}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
