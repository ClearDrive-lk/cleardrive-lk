"use client";

import { useState } from "react";
import { isAxiosError } from "axios";
import { apiClient } from "@/lib/api-client";

interface ExporterOption {
  id: string;
  email: string;
  name: string;
}

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

interface ExporterAssignmentModalProps {
  exporters: ExporterOption[];
  order: AssignableOrder;
  onClose: () => void;
  onSuccess: () => void;
}

export function ExporterAssignmentModal({
  exporters,
  order,
  onClose,
  onSuccess,
}: ExporterAssignmentModalProps) {
  const [selectedExporterId, setSelectedExporterId] = useState(
    exporters[0]?.id ?? "",
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedExporterId) {
      setError("Select an exporter before continuing.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await apiClient.post(`/admin/shipping/${order.id}/assign`, {
        exporter_id: selectedExporterId,
      });
      onSuccess();
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to assign exporter.",
        );
      } else {
        setError("Failed to assign exporter.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 px-4">
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
        <div className="mb-5">
          <h2 className="text-2xl font-semibold text-slate-900">
            Assign Exporter
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            Order <span className="font-medium text-slate-900">{order.id}</span>
          </p>
          <p className="text-sm text-slate-600">{order.vehicle_label}</p>
          <p className="text-sm text-slate-600">
            Customer: {order.customer_name} ({order.customer_email})
          </p>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="exporter"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Exporter
            </label>
            <select
              id="exporter"
              value={selectedExporterId}
              onChange={(event) => setSelectedExporterId(event.target.value)}
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            >
              {exporters.map((exporter) => (
                <option key={exporter.id} value={exporter.id}>
                  {exporter.name || exporter.email} ({exporter.email})
                </option>
              ))}
            </select>
          </div>

          {error ? (
            <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={loading}
            >
              {loading ? "Assigning..." : "Assign Exporter"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
