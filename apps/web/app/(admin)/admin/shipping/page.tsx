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
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Shipping Assignment</h1>
        <p className="text-gray-600">
          Assign exporters to eligible orders and track shipment queue.
        </p>
      </div>

      <div className="bg-white border rounded-lg p-4 space-y-4">
        <h2 className="text-lg font-semibold">Assign Exporter</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input
            type="text"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            placeholder="Order UUID"
            className="px-3 py-2 border rounded"
          />

          <select
            value={selectedExporter}
            onChange={(e) => setSelectedExporter(e.target.value)}
            className="px-3 py-2 border rounded"
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
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-60"
          >
            {assigning ? "Assigning..." : "Assign Exporter"}
          </button>
        </div>

        {error && (
          <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
            {error}
          </div>
        )}
        {success && (
          <div className="text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">
            {success}
          </div>
        )}
      </div>

      <div className="bg-white border rounded-lg p-4 space-y-4">
        <div>
          <h2 className="text-lg font-semibold">Pending Approvals</h2>
          <p className="text-sm text-gray-600">
            Approve shipments that have submitted details and uploaded
            documents.
          </p>
        </div>

        {pendingLoading ? (
          <div className="p-4 text-center text-gray-500">
            Loading pending shipments...
          </div>
        ) : pendingError ? (
          <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
            {pendingError}
          </div>
        ) : pendingShipments.length === 0 ? (
          <div className="text-sm text-gray-600">
            No shipments awaiting approval.
          </div>
        ) : (
          <div className="space-y-3">
            {pendingShipments.map((shipment) => (
              <div
                key={shipment.id}
                className="border rounded-lg p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3"
              >
                <div className="space-y-1">
                  <p className="text-sm text-gray-500">Order ID</p>
                  <p className="text-sm font-medium">{shipment.order_id}</p>
                  <p className="text-sm text-gray-600">
                    Vessel: {shipment.vessel_name || "TBD"}
                  </p>
                  <p className="text-sm text-gray-600">
                    Route: {shipment.departure_port || "TBD"} →{" "}
                    {shipment.arrival_port || "TBD"}
                  </p>
                  <p className="text-sm text-gray-600">
                    ETA:{" "}
                    {shipment.estimated_arrival_date
                      ? new Date(
                          shipment.estimated_arrival_date,
                        ).toLocaleDateString()
                      : "TBD"}
                  </p>
                  <p className="text-xs text-gray-500">
                    Docs Uploaded: {shipment.documents_uploaded ? "Yes" : "No"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => approveShipment(shipment.id)}
                    disabled={approvingId === shipment.id}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-60"
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
        <div className="bg-white border rounded p-4">
          <p className="text-sm text-gray-500">Total</p>
          <p className="text-2xl font-bold">{summary?.total ?? 0}</p>
        </div>
        <div className="bg-white border rounded p-4">
          <p className="text-sm text-gray-500">Awaiting Details</p>
          <p className="text-2xl font-bold">{summary?.awaiting_details ?? 0}</p>
        </div>
        <div className="bg-white border rounded p-4">
          <p className="text-sm text-gray-500">Awaiting Approval</p>
          <p className="text-2xl font-bold">
            {summary?.awaiting_approval ?? 0}
          </p>
        </div>
        <div className="bg-white border rounded p-4">
          <p className="text-sm text-gray-500">Approved</p>
          <p className="text-2xl font-bold">{summary?.approved ?? 0}</p>
        </div>
      </div>

      <div className="bg-white border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b">
          <h2 className="font-semibold">Current Shipments</h2>
        </div>
        {loading ? (
          <div className="p-6 text-center text-gray-500">Loading...</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500">
                  Order
                </th>
                <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500">
                  Exporter
                </th>
                <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500">
                  Status
                </th>
                <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500">
                  Docs
                </th>
                <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500">
                  Approved
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(summary?.shipments ?? []).map((shipment) => (
                <tr key={shipment.id}>
                  <td className="px-4 py-2 text-sm">{shipment.order_id}</td>
                  <td className="px-4 py-2 text-sm">
                    {shipment.exporter_id ||
                      shipment.assigned_exporter_id ||
                      "-"}
                  </td>
                  <td className="px-4 py-2 text-sm">
                    {shipment.status || "-"}
                  </td>
                  <td className="px-4 py-2 text-sm">
                    {shipment.documents_uploaded ? "Yes" : "No"}
                  </td>
                  <td className="px-4 py-2 text-sm">
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
