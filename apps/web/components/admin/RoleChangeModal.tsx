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
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to change role");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 className="text-xl font-bold mb-4">Change User Role</h2>

        <div className="mb-4">
          <p className="text-sm text-gray-600">User: {user.email}</p>
          <p className="text-sm text-gray-600">
            Current Role: <strong>{user.role}</strong>
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {/* New Role Select */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">
              New Role <span className="text-red-500">*</span>
            </label>
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="w-full px-3 py-2 border rounded"
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
            <label className="block text-sm font-medium mb-2">
              Reason for Change <span className="text-red-500">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 border rounded"
              rows={3}
              placeholder="Explain why this role change is necessary..."
              required
              minLength={10}
            />
            <p className="text-xs text-gray-500 mt-1">
              Minimum 10 characters. This will be logged for audit purposes.
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border rounded hover:bg-gray-50"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
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
