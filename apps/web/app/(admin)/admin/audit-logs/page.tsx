"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { isAxiosError } from "axios";
import { apiClient } from "@/lib/api-client";

interface AuditLogItem {
  id: string;
  event_type: string;
  user_id: string | null;
  user_email: string | null;
  admin_id: string | null;
  admin_email: string | null;
  details: Record<string, unknown>;
  created_at: string;
}

interface AuditLogsResponse {
  logs: AuditLogItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

interface EventTypesResponse {
  event_types: string[];
}

interface FiltersState {
  eventType: string;
  userId: string;
  adminId: string;
  startDate: string;
  endDate: string;
  search: string;
}

const DEFAULT_FILTERS: FiltersState = {
  eventType: "",
  userId: "",
  adminId: "",
  startDate: "",
  endDate: "",
  search: "",
};

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

function renderDetailValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }
  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  return JSON.stringify(value);
}

function buildQuery(filters: FiltersState, page: number, limit: number) {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(limit),
  });

  if (filters.eventType) {
    params.set("event_type", filters.eventType);
  }
  if (filters.userId) {
    params.set("user_id", filters.userId);
  }
  if (filters.adminId) {
    params.set("admin_id", filters.adminId);
  }
  if (filters.startDate) {
    params.set("start_date", `${filters.startDate}T00:00:00`);
  }
  if (filters.endDate) {
    params.set("end_date", `${filters.endDate}T23:59:59`);
  }
  if (filters.search) {
    params.set("search", filters.search);
  }

  return params.toString();
}

export default function AuditLogsPage() {
  const [filters, setFilters] = useState<FiltersState>(DEFAULT_FILTERS);
  const [draftFilters, setDraftFilters] =
    useState<FiltersState>(DEFAULT_FILTERS);
  const [logsResponse, setLogsResponse] = useState<AuditLogsResponse | null>(
    null,
  );
  const [eventTypes, setEventTypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const limit = 20;
  const currentPage = logsResponse?.page ?? 1;

  const queryString = useMemo(
    () => buildQuery(filters, currentPage, limit),
    [currentPage, filters],
  );

  const loadLogs = useCallback(
    async (page = 1, activeFilters = filters) => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<AuditLogsResponse>(
          `/admin/audit-logs?${buildQuery(activeFilters, page, limit)}`,
        );
        setLogsResponse(response.data);
      } catch (err: unknown) {
        if (isAxiosError(err)) {
          setError(
            (err.response?.data as { detail?: string } | undefined)?.detail ??
              "Failed to load audit logs.",
          );
        } else {
          setError("Failed to load audit logs.");
        }
      } finally {
        setLoading(false);
      }
    },
    [filters],
  );

  const loadEventTypes = useCallback(async () => {
    try {
      const response = await apiClient.get<EventTypesResponse>(
        "/admin/audit-logs/event-types",
      );
      setEventTypes(response.data.event_types);
    } catch {
      setEventTypes([]);
    }
  }, []);

  useEffect(() => {
    void loadEventTypes();
  }, [loadEventTypes]);

  useEffect(() => {
    void loadLogs(1, filters);
  }, [filters, loadLogs]);

  const handleDraftChange = (key: keyof FiltersState, value: string) => {
    setDraftFilters((current) => ({ ...current, [key]: value }));
  };

  const applyFilters = () => {
    setFilters(draftFilters);
  };

  const resetFilters = () => {
    setDraftFilters(DEFAULT_FILTERS);
    setFilters(DEFAULT_FILTERS);
  };

  const exportCsv = async () => {
    setExporting(true);
    try {
      const response = await apiClient.get(
        `/admin/audit-logs/export?${queryString}`,
        {
          responseType: "blob",
        },
      );
      const blob = new Blob([response.data], {
        type: "text/csv;charset=utf-8;",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "audit-logs.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to export audit logs:", err);
      setError("Failed to export audit logs.");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="min-h-screen p-6 text-white">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-[#FE7743]">
            CD-62 Admin Audit Logs
          </p>
          <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-semibold text-white">
                Audit Log Viewer
              </h1>
              <p className="mt-2 text-sm text-gray-400">
                Review privileged actions across KYC, gazettes, user changes,
                and other operational events.
              </p>
            </div>
            <button
              type="button"
              onClick={() => void exportCsv()}
              disabled={exporting}
              className="inline-flex rounded-xl bg-[#FE7743] px-4 py-2 text-sm font-semibold text-black transition hover:bg-[#FE7743]/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {exporting ? "Exporting..." : "Export CSV"}
            </button>
          </div>
        </header>

        <section className="grid gap-4 lg:grid-cols-6">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
            <p className="text-sm text-gray-400">Total Logs</p>
            <p className="mt-2 text-3xl font-semibold text-white">
              {logsResponse?.total ?? 0}
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
            <p className="text-sm text-gray-400">Current Page</p>
            <p className="mt-2 text-3xl font-semibold text-white">
              {logsResponse?.page ?? 1}
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
            <p className="text-sm text-gray-400">Total Pages</p>
            <p className="mt-2 text-3xl font-semibold text-white">
              {logsResponse?.total_pages ?? 0}
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
            <p className="text-sm text-gray-400">Page Size</p>
            <p className="mt-2 text-3xl font-semibold text-white">{limit}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
            <p className="text-sm text-gray-400">Active Event Filter</p>
            <p className="mt-2 text-base font-semibold text-white">
              {filters.eventType || "All"}
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
            <p className="text-sm text-gray-400">Search</p>
            <p className="mt-2 text-base font-semibold text-white">
              {filters.search || "None"}
            </p>
          </div>
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <label className="space-y-2">
              <span className="text-sm font-medium text-gray-400">
                Event Type
              </span>
              <select
                value={draftFilters.eventType}
                onChange={(event) =>
                  handleDraftChange("eventType", event.target.value)
                }
                className="w-full rounded-xl border border-white/10 bg-white/10 px-4 py-2.5 text-sm text-gray-200 focus:border-[#FE7743]/60 focus:outline-none focus:ring-2 focus:ring-[#FE7743]/60"
              >
                <option value="">All event types</option>
                {eventTypes.map((eventType) => (
                  <option key={eventType} value={eventType}>
                    {eventType}
                  </option>
                ))}
              </select>
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-gray-400">User ID</span>
              <input
                value={draftFilters.userId}
                onChange={(event) =>
                  handleDraftChange("userId", event.target.value)
                }
                placeholder="Filter by affected user UUID"
                className="w-full rounded-xl border border-white/10 bg-white/10 px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-500 focus:border-[#FE7743]/60 focus:outline-none focus:ring-2 focus:ring-[#FE7743]/60"
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-gray-400">
                Admin ID
              </span>
              <input
                value={draftFilters.adminId}
                onChange={(event) =>
                  handleDraftChange("adminId", event.target.value)
                }
                placeholder="Filter by acting admin UUID"
                className="w-full rounded-xl border border-white/10 bg-white/10 px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-500 focus:border-[#FE7743]/60 focus:outline-none focus:ring-2 focus:ring-[#FE7743]/60"
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-gray-400">
                Start Date
              </span>
              <input
                type="date"
                value={draftFilters.startDate}
                onChange={(event) =>
                  handleDraftChange("startDate", event.target.value)
                }
                className="w-full rounded-xl border border-white/10 bg-white/10 px-4 py-2.5 text-sm text-gray-200 focus:border-[#FE7743]/60 focus:outline-none focus:ring-2 focus:ring-[#FE7743]/60"
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-gray-400">
                End Date
              </span>
              <input
                type="date"
                value={draftFilters.endDate}
                onChange={(event) =>
                  handleDraftChange("endDate", event.target.value)
                }
                className="w-full rounded-xl border border-white/10 bg-white/10 px-4 py-2.5 text-sm text-gray-200 focus:border-[#FE7743]/60 focus:outline-none focus:ring-2 focus:ring-[#FE7743]/60"
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-gray-400">Search</span>
              <input
                value={draftFilters.search}
                onChange={(event) =>
                  handleDraftChange("search", event.target.value)
                }
                placeholder="Search details JSON"
                className="w-full rounded-xl border border-white/10 bg-white/10 px-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-500 focus:border-[#FE7743]/60 focus:outline-none focus:ring-2 focus:ring-[#FE7743]/60"
              />
            </label>
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={applyFilters}
              className="rounded-xl bg-[#FE7743] px-4 py-2 text-sm font-semibold text-black transition hover:bg-[#FE7743]/90"
            >
              Apply Filters
            </button>
            <button
              type="button"
              onClick={resetFilters}
              className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-gray-200 transition hover:bg-white/10"
            >
              Reset
            </button>
          </div>
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/5 shadow-sm">
          <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
            <div>
              <h2 className="text-xl font-semibold text-white">Audit Events</h2>
              <p className="text-sm text-gray-400">
                Showing newest events first.
              </p>
            </div>
            <button
              type="button"
              onClick={() => void loadLogs(currentPage)}
              className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-gray-200 transition hover:bg-white/10"
            >
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="px-6 py-16 text-center text-gray-400">
              Loading audit logs...
            </div>
          ) : error ? (
            <div className="px-6 py-16 text-center text-red-300">{error}</div>
          ) : !logsResponse || logsResponse.logs.length === 0 ? (
            <div className="px-6 py-16 text-center text-gray-400">
              No audit logs matched the selected filters.
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-white/10 text-sm">
                  <thead className="bg-white/5">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                        Time
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                        Event
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                        Admin
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                        Details
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10">
                    {logsResponse.logs.map((log) => (
                      <tr key={log.id} className="align-top hover:bg-white/5">
                        <td className="px-6 py-4 text-gray-300">
                          {formatTimestamp(log.created_at)}
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1 text-xs font-semibold text-blue-200">
                            {log.event_type}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-gray-300">
                          <div className="font-medium text-white">
                            {log.user_email || "N/A"}
                          </div>
                          <div className="text-xs text-gray-500">
                            {log.user_id || "No linked user"}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-gray-300">
                          <div className="font-medium text-white">
                            {log.admin_email || "N/A"}
                          </div>
                          <div className="text-xs text-gray-500">
                            {log.admin_id || "System"}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-gray-300">
                          <dl className="space-y-1">
                            {Object.entries(log.details || {}).length === 0 ? (
                              <div>N/A</div>
                            ) : (
                              Object.entries(log.details || {}).map(
                                ([key, value]) => (
                                  <div key={`${log.id}-${key}`}>
                                    <dt className="inline font-medium text-white">
                                      {key}:
                                    </dt>{" "}
                                    <dd className="inline">
                                      {renderDetailValue(value)}
                                    </dd>
                                  </div>
                                ),
                              )
                            )}
                          </dl>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex flex-col gap-4 border-t border-white/10 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-gray-400">
                  Page {logsResponse.page} of{" "}
                  {Math.max(logsResponse.total_pages, 1)}
                </p>
                <div className="flex gap-3">
                  <button
                    type="button"
                    disabled={logsResponse.page <= 1}
                    onClick={() => void loadLogs(logsResponse.page - 1)}
                    className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-gray-200 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    disabled={logsResponse.page >= logsResponse.total_pages}
                    onClick={() => void loadLogs(logsResponse.page + 1)}
                    className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-gray-200 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
