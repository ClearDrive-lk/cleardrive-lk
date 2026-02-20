"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { format } from "date-fns";

interface AuditLog {
  id: string;
  event_type: string;
  user_email: string;
  admin_email: string;
  details: {
    old_role?: string;
    new_role?: string;
    reason?: string;
  };
  created_at: string;
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [filter, setFilter] = useState("ROLE_CHANGED");

  useEffect(() => {
    let isCancelled = false;

    const fetchLogs = async () => {
      try {
        const response = await apiClient.get(
          `/admin/audit-logs?event_type=${filter}`,
        );
        if (!isCancelled) {
          setLogs(response.data.logs);
        }
      } catch (error) {
        console.error("Failed to load audit logs:", error);
      }
    };

    void fetchLogs();

    return () => {
      isCancelled = true;
    };
  }, [filter]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Audit Logs</h1>

      {/* Filter */}
      <div className="mb-6">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-4 py-2 border rounded"
        >
          <option value="ROLE_CHANGED">Role Changes</option>
          <option value="USER_CREATED">User Created</option>
          <option value="LOGIN">Logins</option>
          <option value="ALL">All Events</option>
        </select>
      </div>

      {/* Logs Table */}
      <div className="border rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Event
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Admin
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Details
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {logs.map((log) => (
              <tr key={log.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {format(new Date(log.created_at), "MMM d, yyyy HH:mm")}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                    {log.event_type}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {log.user_email}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {log.admin_email}
                </td>
                <td className="px-6 py-4 text-sm">
                  {log.details.old_role && log.details.new_role && (
                    <div>
                      <div>
                        {log.details.old_role} → {log.details.new_role}
                      </div>
                      <div className="text-gray-500 text-xs mt-1">
                        Reason: {log.details.reason}
                      </div>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
