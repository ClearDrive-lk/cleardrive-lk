"use client";

import { useEffect, useState } from "react";
import { isAxiosError } from "axios";
import { apiClient } from "@/lib/api-client";

interface Exporter {
  id: string;
  email: string;
  name: string;
}

interface ShipmentItem {
  id: string;
  order_id: string;
  exporter_id?: string;
  assigned_exporter_id?: string;
  status?: string;
  documents_uploaded: boolean;
  approved: boolean;
  created_at: string;
}

interface ShipmentSummaryResponse {
  total: number;
  awaiting_details: number;
  awaiting_approval: number;
  approved: number;
  shipments: ShipmentItem[];
}

interface PendingShipment {
  id: string;
  order_id: string;
  exporter_id?: string;
  assigned_exporter_id?: string;
  vessel_name?: string;
  departure_port?: string;
  arrival_port?: string;
  estimated_arrival_date?: string;
  documents_uploaded: boolean;
  approved: boolean;
  created_at: string;
}

export default function AdminShippingPage() {
  const [orderId, setOrderId] = useState("");
  const [exporters, setExporters] = useState<Exporter[]>([]);
  const [selectedExporter, setSelectedExporter] = useState("");
  const [summary, setSummary] = useState<ShipmentSummaryResponse | null>(null);
  const [pendingShipments, setPendingShipments] = useState<PendingShipment[]>(
    [],
  );
  const [loading, setLoading] = useState(true);
  const [pendingLoading, setPendingLoading] = useState(true);
  const [approvingId, setApprovingId] = useState<string | null>(null);
  const [assigning, setAssigning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingError, setPendingError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadExporters = async () => {
    const response = await apiClient.get<{
      users: Exporter[];
    }>(
      "/admin/users?role=EXPORTER&page=1&limit=100&sort_by=created_at&sort_order=desc",
    );
    setExporters(response.data.users);
    if (!selectedExporter && response.data.users.length > 0) {
      setSelectedExporter(response.data.users[0].id);
    }
  };

  const loadShipments = async () => {
    const response = await apiClient.get<ShipmentSummaryResponse>(
      "/admin/shipping/all",
    );
    setSummary(response.data);
  };

  const loadPendingShipments = async () => {
    setPendingLoading(true);
    setPendingError(null);
    try {
      const response = await apiClient.get<PendingShipment[]>(
        "/admin/shipping/pending",
      );
      setPendingShipments(response.data);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setPendingError(detail);
      } else {
        setPendingError("Failed to load pending approvals.");
      }
    } finally {
      setPendingLoading(false);
    }
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([
        loadExporters(),
        loadShipments(),
        loadPendingShipments(),
      ]);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setError(detail);
      } else {
        setError("Failed to load shipping data.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const assignExporter = async () => {
    if (!orderId.trim() || !selectedExporter) {
      setError("Order ID and exporter are required.");
      return;
    }

    setAssigning(true);
    setError(null);
    setSuccess(null);
    try {
      await apiClient.post(`/admin/shipping/${orderId.trim()}/assign`, {
        exporter_id: selectedExporter,
      });
      setSuccess("Exporter assigned successfully.");
      setOrderId("");
      await loadShipments();
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setError(detail);
      } else {
        setError("Failed to assign exporter.");
      }
    } finally {
      setAssigning(false);
    }
  };

  const approveShipment = async (shipmentId: string) => {
    if (
      !window.confirm("Approve this shipment and mark the order as shipped?")
    ) {
      return;
    }

    setApprovingId(shipmentId);
    setPendingError(null);
    setSuccess(null);
    try {
      await apiClient.post(`/admin/shipping/${shipmentId}/approve`);
      setSuccess("Shipment approved successfully.");
      await Promise.all([loadShipments(), loadPendingShipments()]);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setPendingError(detail);
      } else {
        setPendingError("Failed to approve shipment.");
      }
    } finally {
      setApprovingId(null);
    }
  };

  return (
    <div className="p-6 space-y-6 text-[#393d3f]">
      <div>
        <h1 className="text-2xl font-bold">Shipping Assignment</h1>
        <p className="text-[#546a7b]">
          Assign exporters to eligible orders and track shipment queue.
        </p>
      </div>

      <div className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4 shadow-sm space-y-4">
        <h2 className="text-lg font-semibold text-[#393d3f]">Assign Exporter</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input
            type="text"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            placeholder="Order UUID"
            className="rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-3 py-2 text-sm text-gray-200 placeholder:text-[#546a7b]"
          />

          <select
            value={selectedExporter}
            onChange={(e) => setSelectedExporter(e.target.value)}
            className="rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-3 py-2 text-sm text-gray-200"
          >
            {exporters.map((exporter) => (
              <option key={exporter.id} value={exporter.id}>
                {exporter.email}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={assignExporter}
            disabled={assigning}
            className="rounded-xl bg-[#62929e] px-4 py-2 text-sm font-semibold text-[#fdfdff] hover:bg-[#62929e]/90 disabled:opacity-60"
          >
            {assigning ? "Assigning..." : "Assign Exporter"}
          </button>
        </div>

        {error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-2 text-sm text-red-200">
            {error}
          </div>
        )}
        {success && (
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-2 text-sm text-emerald-200">
            {success}
          </div>
        )}
      </div>

      <div className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4 shadow-sm space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-[#393d3f]">
            Pending Approvals
          </h2>
          <p className="text-sm text-[#546a7b]">
            Approve shipments that have submitted details and uploaded
            documents.
          </p>
        </div>

        {pendingLoading ? (
          <div className="p-4 text-center text-[#546a7b]">
            Loading pending shipments...
          </div>
        ) : pendingError ? (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-2 text-sm text-red-200">
            {pendingError}
          </div>
        ) : pendingShipments.length === 0 ? (
          <div className="text-sm text-[#546a7b]">
            No shipments awaiting approval.
          </div>
        ) : (
          <div className="space-y-3">
            {pendingShipments.map((shipment) => (
              <div
                key={shipment.id}
                className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between"
              >
                <div className="space-y-1">
                  <p className="text-sm text-[#546a7b]">Order ID</p>
                  <p className="text-sm font-medium text-[#393d3f]">
                    {shipment.order_id}
                  </p>
                  <p className="text-sm text-[#546a7b]">
                    Vessel: {shipment.vessel_name || "TBD"}
                  </p>
                  <p className="text-sm text-[#546a7b]">
                    Route: {shipment.departure_port || "TBD"}
                    {" -> "}
                    {shipment.arrival_port || "TBD"}
                  </p>
                  <p className="text-sm text-[#546a7b]">
                    ETA:{" "}
                    {shipment.estimated_arrival_date
                      ? new Date(
                          shipment.estimated_arrival_date,
                        ).toLocaleDateString()
                      : "TBD"}
                  </p>
                  <p className="text-xs text-[#546a7b]">
                    Docs Uploaded: {shipment.documents_uploaded ? "Yes" : "No"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => approveShipment(shipment.id)}
                    disabled={approvingId === shipment.id}
                    className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-[#393d3f] hover:bg-emerald-400 disabled:opacity-60"
                  >
                    {approvingId === shipment.id ? "Approving..." : "Approve"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4">
          <p className="text-sm text-[#546a7b]">Total</p>
          <p className="text-2xl font-bold text-[#393d3f]">{summary?.total ?? 0}</p>
        </div>
        <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4">
          <p className="text-sm text-[#546a7b]">Awaiting Details</p>
          <p className="text-2xl font-bold text-[#393d3f]">
            {summary?.awaiting_details ?? 0}
          </p>
        </div>
        <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4">
          <p className="text-sm text-[#546a7b]">Awaiting Approval</p>
          <p className="text-2xl font-bold text-[#393d3f]">
            {summary?.awaiting_approval ?? 0}
          </p>
        </div>
        <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-4">
          <p className="text-sm text-[#546a7b]">Approved</p>
          <p className="text-2xl font-bold text-[#393d3f]">
            {summary?.approved ?? 0}
          </p>
        </div>
      </div>

      <div className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 overflow-hidden">
        <div className="px-4 py-3 border-b border-[#546a7b]/65">
          <h2 className="font-semibold text-[#393d3f]">Current Shipments</h2>
        </div>
        {loading ? (
          <div className="p-6 text-center text-[#546a7b]">Loading...</div>
        ) : (
          <table className="min-w-full divide-y divide-white/10 text-sm">
            <thead className="bg-[#c6c5b9]/20">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-semibold text-[#546a7b]">
                  Order
                </th>
                <th className="px-4 py-2 text-left text-xs font-semibold text-[#546a7b]">
                  Exporter
                </th>
                <th className="px-4 py-2 text-left text-xs font-semibold text-[#546a7b]">
                  Status
                </th>
                <th className="px-4 py-2 text-left text-xs font-semibold text-[#546a7b]">
                  Docs
                </th>
                <th className="px-4 py-2 text-left text-xs font-semibold text-[#546a7b]">
                  Approved
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {(summary?.shipments ?? []).map((shipment) => (
                <tr key={shipment.id} className="hover:bg-[#c6c5b9]/20">
                  <td className="px-4 py-2 text-sm text-[#393d3f]">
                    {shipment.order_id}
                  </td>
                  <td className="px-4 py-2 text-sm text-[#546a7b]">
                    {shipment.exporter_id ||
                      shipment.assigned_exporter_id ||
                      "-"}
                  </td>
                  <td className="px-4 py-2 text-sm text-[#546a7b]">
                    {shipment.status || "-"}
                  </td>
                  <td className="px-4 py-2 text-sm text-[#546a7b]">
                    {shipment.documents_uploaded ? "Yes" : "No"}
                  </td>
                  <td className="px-4 py-2 text-sm text-[#546a7b]">
                    {shipment.approved ? "Yes" : "No"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

