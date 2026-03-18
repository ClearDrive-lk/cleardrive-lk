"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api-client";

interface RoleChangeModalProps {
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
  };
  onClose: () => void;
  onSuccess: () => void;
}

export function RoleChangeModal({
  user,
  onClose,
  onSuccess,
}: RoleChangeModalProps) {
  const [newRole, setNewRole] = useState(user.role);
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newRole === user.role) {
      setError("Please select a different role");
      return;
    }

    if (reason.length < 10) {
      setError("Reason must be at least 10 characters");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await apiClient.patch(`/admin/users/${user.id}/role`, {
        role: newRole,
        reason: reason,
      });

      onSuccess();
    } catch (err: unknown) {
      const detail =
        typeof err === "object" &&
        err !== null &&
        "response" in err &&
        typeof (err as { response?: unknown }).response === "object" &&
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail;
      const message =
        detail ||
        (err instanceof Error ? err.message : "Failed to change role");
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#fdfdff]/70">
      <div className="w-full max-w-md rounded-2xl border border-[#546a7b]/65 bg-[#0b0b0b] p-6">
        <h2 className="text-xl font-bold text-[#393d3f] mb-4">Change User Role</h2>

        <div className="mb-4">
          <p className="text-sm text-[#546a7b]">User: {user.email}</p>
          <p className="text-sm text-[#546a7b]">
            Current Role: <strong className="text-[#393d3f]">{user.role}</strong>
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {/* New Role Select */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2 text-[#546a7b]">
              New Role <span className="text-red-500">*</span>
            </label>
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="w-full rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-3 py-2 text-sm text-gray-200"
              required
            >
              <option value="CUSTOMER">Customer</option>
              <option value="ADMIN">Admin</option>
              <option value="EXPORTER">Exporter</option>
              <option value="CLEARING_AGENT">Clearing Agent</option>
              <option value="FINANCE_PARTNER">Finance Partner</option>
            </select>
          </div>

          {/* Reason Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2 text-[#546a7b]">
              Reason for Change <span className="text-red-500">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full rounded-xl border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-3 py-2 text-sm text-gray-200"
              rows={3}
              placeholder="Explain why this role change is necessary..."
              required
              minLength={10}
            />
            <p className="text-xs text-[#546a7b] mt-1">
              Minimum 10 characters. This will be logged for audit purposes.
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-xl border border-[#546a7b]/65 px-4 py-2 text-sm font-medium text-gray-200 hover:bg-[#c6c5b9]/30"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 rounded-xl bg-[#62929e] px-4 py-2 text-sm font-semibold text-[#fdfdff] hover:bg-[#62929e]/90 disabled:opacity-50"
              disabled={loading}
            >
              {loading ? "Changing..." : "Change Role"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

