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
  const [pendingPayments, setPendingPayments] = useState<AssignableOrder[]>([]);
  const [exporters, setExporters] = useState<ExporterUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingLoading, setPendingLoading] = useState(true);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pendingError, setPendingError] = useState<string | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<AssignableOrder | null>(
    null,
  );

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    setPendingLoading(true);
    setPendingError(null);

    try {
      const [ordersResponse, exportersResponse, pendingResponse] =
        await Promise.all([
          apiClient.get<AssignableOrder[]>("/admin/shipping/assignable-orders"),
          apiClient.get<UserListResponse>(
            "/admin/users?role=EXPORTER&limit=100",
          ),
          apiClient.get<AssignableOrder[]>("/admin/shipping/pending-payments"),
        ]);

      setOrders(ordersResponse.data);
      setExporters(exportersResponse.data.users);
      setPendingPayments(pendingResponse.data);
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
      setPendingLoading(false);
    }
  }, []);

  const loadPendingPayments = useCallback(async () => {
    setPendingLoading(true);
    setPendingError(null);
    try {
      const response = await apiClient.get<AssignableOrder[]>(
        "/admin/shipping/pending-payments",
      );
      setPendingPayments(response.data);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setPendingError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to load pending payments.",
        );
      } else {
        setPendingError("Failed to load pending payments.");
      }
    } finally {
      setPendingLoading(false);
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

  const confirmPayment = async (orderId: string) => {
    setConfirmingId(orderId);
    setPendingError(null);
    try {
      await apiClient.post(`/admin/shipping/${orderId}/confirm-payment`);
      await Promise.all([loadData(), loadPendingPayments()]);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setPendingError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to confirm payment.",
        );
      } else {
        setPendingError("Failed to confirm payment.");
      }
    } finally {
      setConfirmingId(null);
    }
  };

  return (
    <div className="min-h-screen text-[#393d3f]">
      <div className="cd-container py-6 space-y-6">
        <header className="flex flex-col gap-2 rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-[#62929e]">
            CD-70 Exporter Assignment
          </p>
          <h1 className="text-3xl font-semibold text-[#393d3f]">
            Assign Exporters to Paid Orders
          </h1>
          <p className="max-w-3xl text-sm text-[#546a7b]">
            Review orders in{" "}
            <span className="font-medium text-emerald-700 dark:text-emerald-200">
              PAYMENT_CONFIRMED
            </span>{" "}
            status and assign an exporter to move them into shipment handling.
          </p>
        </header>

        <section className="grid gap-4 sm:grid-cols-4">
          <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5 shadow-sm">
            <p className="text-sm text-[#546a7b]">Assignable Orders</p>
            <p className="mt-2 text-3xl font-semibold text-[#393d3f]">
              {orders.length}
            </p>
          </div>
          <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5 shadow-sm">
            <p className="text-sm text-[#546a7b]">Pending Payments</p>
            <p className="mt-2 text-3xl font-semibold text-[#393d3f]">
              {pendingPayments.length}
            </p>
          </div>
          <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5 shadow-sm">
            <p className="text-sm text-[#546a7b]">Available Exporters</p>
            <p className="mt-2 text-3xl font-semibold text-[#393d3f]">
              {exporters.length}
            </p>
          </div>
          <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5 shadow-sm">
            <p className="text-sm text-[#546a7b]">Status Gate</p>
            <p className="mt-2 text-lg font-semibold text-emerald-700 dark:text-emerald-200">
              PAYMENT_CONFIRMED only
            </p>
          </div>
        </section>

        <section className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#546a7b]/65 px-6 py-4">
            <div>
              <h2 className="text-xl font-semibold text-[#393d3f]">
                Orders Awaiting Payment Confirmation
              </h2>
              <p className="text-sm text-[#546a7b]">
                Mark payment as completed to move the order into the exporter
                assignment queue.
              </p>
            </div>
            <button
              onClick={() => void loadPendingPayments()}
              className="rounded-xl border border-[#546a7b]/65 px-4 py-2 text-sm font-medium text-[#393d3f] transition hover:bg-[#c6c5b9]/30"
            >
              Refresh
            </button>
          </div>

          {pendingLoading ? (
            <div className="px-6 py-16 text-center text-[#546a7b]">
              Loading pending payments...
            </div>
          ) : pendingError ? (
            <div className="px-6 py-16 text-center">
              <p className="text-sm text-red-600 dark:text-red-300">
                {pendingError}
              </p>
            </div>
          ) : pendingPayments.length === 0 ? (
            <div className="px-6 py-16 text-center text-[#546a7b]">
              No pending payment orders right now.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-white/10 text-sm">
                <thead className="bg-[#c6c5b9]/20">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                      Order
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                      Customer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                      Vehicle
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                      Payment
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {pendingPayments.map((order) => (
                    <tr key={order.id} className="hover:bg-[#c6c5b9]/20">
                      <td className="px-6 py-4">
                        <div className="font-medium text-[#393d3f]">
                          {order.id}
                        </div>
                        <div className="text-xs text-[#546a7b]">
                          Created {new Date(order.created_at).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-[#393d3f]">
                          {order.customer_name}
                        </div>
                        <div className="text-xs text-[#546a7b]">
                          {order.customer_email}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-[#546a7b]">
                        {order.vehicle_label}
                      </td>
                      <td className="px-6 py-4">
                        <div className="inline-flex rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-700 dark:text-amber-200">
                          {order.payment_status}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => void confirmPayment(order.id)}
                          disabled={confirmingId === order.id}
                          className="rounded-xl bg-[#62929e] px-4 py-2 text-sm font-semibold text-[#fdfdff] transition hover:bg-[#62929e]/90 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {confirmingId === order.id
                            ? "Confirming..."
                            : "Confirm Payment"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#546a7b]/65 px-6 py-4">
            <div>
              <h2 className="text-xl font-semibold text-[#393d3f]">
                Paid Orders Awaiting Assignment
              </h2>
              <p className="text-sm text-[#546a7b]">
                Orders already assigned to an exporter are excluded.
              </p>
            </div>
            <button
              onClick={() => void loadData()}
              className="rounded-xl border border-[#546a7b]/65 px-4 py-2 text-sm font-medium text-[#393d3f] transition hover:bg-[#c6c5b9]/30"
            >
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="px-6 py-16 text-center text-[#546a7b]">
              Loading orders...
            </div>
          ) : error ? (
            <div className="px-6 py-16 text-center">
              <p className="text-sm text-red-600 dark:text-red-300">{error}</p>
            </div>
          ) : orders.length === 0 ? (
            <div className="px-6 py-16 text-center text-[#546a7b]">
              No paid orders are waiting for exporter assignment.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-white/10 text-sm">
                <thead className="bg-[#c6c5b9]/20">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                      Order
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                      Customer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                      Vehicle
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {orders.map((order) => (
                    <tr key={order.id} className="hover:bg-[#c6c5b9]/20">
                      <td className="px-6 py-4">
                        <div className="font-medium text-[#393d3f]">
                          {order.id}
                        </div>
                        <div className="text-xs text-[#546a7b]">
                          Created {new Date(order.created_at).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-[#393d3f]">
                          {order.customer_name}
                        </div>
                        <div className="text-xs text-[#546a7b]">
                          {order.customer_email}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-[#546a7b]">
                        {order.vehicle_label}
                      </td>
                      <td className="px-6 py-4 text-[#546a7b]">
                        {order.total_cost_lkr !== null
                          ? `LKR ${order.total_cost_lkr.toLocaleString()}`
                          : "N/A"}
                      </td>
                      <td className="px-6 py-4">
                        <div className="inline-flex rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-200">
                          {order.status}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => setSelectedOrder(order)}
                          disabled={exporters.length === 0}
                          className="rounded-xl bg-[#62929e] px-4 py-2 text-sm font-semibold text-[#fdfdff] transition hover:bg-[#62929e]/90 disabled:cursor-not-allowed disabled:opacity-60"
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
