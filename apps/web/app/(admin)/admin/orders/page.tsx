"use client";

import { useCallback, useEffect, useState } from "react";
import { isAxiosError } from "axios";
import { ExporterAssignmentModal } from "@/components/admin/ExporterAssignmentModal";
import { apiClient } from "@/lib/api-client";

interface AssignableOrder {
  id: string;
  customer_name: string;
  customer_email: string;
  vehicle_label: string;
  status: string;
  payment_status: string;
  total_cost_lkr: number | null;
  created_at: string;
}

interface ExporterUser {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface UserListResponse {
  users: ExporterUser[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<AssignableOrder[]>([]);
  const [exporters, setExporters] = useState<ExporterUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<AssignableOrder | null>(
    null,
  );

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [ordersResponse, exportersResponse] = await Promise.all([
        apiClient.get<AssignableOrder[]>("/admin/shipping/assignable-orders"),
        apiClient.get<UserListResponse>("/admin/users?role=EXPORTER&limit=100"),
      ]);

      setOrders(ordersResponse.data);
      setExporters(exportersResponse.data.users);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to load admin orders.",
        );
      } else {
        setError("Failed to load admin orders.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const exporterOptions = exporters.map((exporter) => ({
    id: exporter.id,
    email: exporter.email,
    name: exporter.name,
  }));

  return (
    <div className="min-h-screen p-6 text-white">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-col gap-2 rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-[#FE7743]">
            CD-70 Exporter Assignment
          </p>
          <h1 className="text-3xl font-semibold text-white">
            Assign Exporters to Paid Orders
          </h1>
          <p className="max-w-3xl text-sm text-gray-400">
            Review orders in{" "}
            <span className="font-medium text-gray-200">PAYMENT_CONFIRMED</span>{" "}
            status and assign an exporter to move them into shipment handling.
          </p>
        </header>

        <section className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
            <p className="text-sm text-gray-400">Assignable Orders</p>
            <p className="mt-2 text-3xl font-semibold text-white">
              {orders.length}
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
            <p className="text-sm text-gray-400">Available Exporters</p>
            <p className="mt-2 text-3xl font-semibold text-white">
              {exporters.length}
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
            <p className="text-sm text-gray-400">Status Gate</p>
            <p className="mt-2 text-lg font-semibold text-emerald-200">
              PAYMENT_CONFIRMED only
            </p>
          </div>
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/5 shadow-sm">
          <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
            <div>
              <h2 className="text-xl font-semibold text-white">
                Paid Orders Awaiting Assignment
              </h2>
              <p className="text-sm text-gray-400">
                Orders already assigned to an exporter are excluded.
              </p>
            </div>
            <button
              onClick={() => void loadData()}
              className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-gray-200 transition hover:bg-white/10"
            >
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="px-6 py-16 text-center text-gray-400">
              Loading orders...
            </div>
          ) : error ? (
            <div className="px-6 py-16 text-center">
              <p className="text-sm text-red-300">{error}</p>
            </div>
          ) : orders.length === 0 ? (
            <div className="px-6 py-16 text-center text-gray-400">
              No paid orders are waiting for exporter assignment.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-white/10 text-sm">
                <thead className="bg-white/5">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                      Order
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                      Customer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                      Vehicle
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {orders.map((order) => (
                    <tr key={order.id} className="hover:bg-white/5">
                      <td className="px-6 py-4">
                        <div className="font-medium text-white">{order.id}</div>
                        <div className="text-xs text-gray-500">
                          Created {new Date(order.created_at).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-white">
                          {order.customer_name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {order.customer_email}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-300">
                        {order.vehicle_label}
                      </td>
                      <td className="px-6 py-4 text-gray-300">
                        {order.total_cost_lkr !== null
                          ? `LKR ${order.total_cost_lkr.toLocaleString()}`
                          : "N/A"}
                      </td>
                      <td className="px-6 py-4">
                        <div className="inline-flex rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-200">
                          {order.status}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => setSelectedOrder(order)}
                          disabled={exporters.length === 0}
                          className="rounded-xl bg-[#FE7743] px-4 py-2 text-sm font-semibold text-black transition hover:bg-[#FE7743]/90 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          Assign Exporter
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      {selectedOrder ? (
        <ExporterAssignmentModal
          exporters={exporterOptions}
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
          onSuccess={() => {
            setSelectedOrder(null);
            void loadData();
          }}
        />
      ) : null}
    </div>
  );
}
