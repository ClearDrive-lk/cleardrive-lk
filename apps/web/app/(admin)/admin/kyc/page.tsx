"use client";

import { useCallback, useEffect, useState } from "react";
import { isAxiosError } from "axios";
import { apiClient } from "@/lib/api-client";

interface PendingKycItem {
  id: string;
  user_id: string;
  user_email: string;
  user_name: string;
  status: string;
  created_at: string;
  extraction_method: string;
  auto_extracted: boolean;
  needs_manual_extraction: boolean;
}

export default function AdminKycPage() {
  const [items, setItems] = useState<PendingKycItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadItems = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response =
        await apiClient.get<PendingKycItem[]>("/admin/kyc/pending");
      setItems(response.data);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to load KYC review queue.",
        );
      } else {
        setError("Failed to load KYC review queue.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadItems();
  }, [loadItems]);

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="rounded-3xl bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-blue-600">
            CD-52 KYC Admin Review
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-900">
            Pending KYC Reviews
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Review pending KYC submissions, compare extracted fields, and
            approve or reject with a reason when needed.
          </p>
        </header>

        <section className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Queue Size</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {items.length}
            </p>
          </div>
          <div className="rounded-2xl bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Auto Extracted</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {items.filter((item) => item.auto_extracted).length}
            </p>
          </div>
          <div className="rounded-2xl bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Manual Review Needed</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {items.filter((item) => item.needs_manual_extraction).length}
            </p>
          </div>
        </section>

        <section className="rounded-3xl bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">
                Review Queue
              </h2>
              <p className="text-sm text-slate-500">
                Oldest submissions are shown first.
              </p>
            </div>
            <button
              type="button"
              onClick={() => void loadItems()}
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="px-6 py-16 text-center text-slate-500">
              Loading KYC queue...
            </div>
          ) : error ? (
            <div className="px-6 py-16 text-center text-red-600">{error}</div>
          ) : items.length === 0 ? (
            <div className="px-6 py-16 text-center text-slate-500">
              No KYC submissions are waiting for review.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left font-medium uppercase tracking-wide text-slate-500">
                      User
                    </th>
                    <th className="px-6 py-3 text-left font-medium uppercase tracking-wide text-slate-500">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left font-medium uppercase tracking-wide text-slate-500">
                      Extraction
                    </th>
                    <th className="px-6 py-3 text-left font-medium uppercase tracking-wide text-slate-500">
                      Submitted
                    </th>
                    <th className="px-6 py-3 text-left font-medium uppercase tracking-wide text-slate-500">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {items.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50/80">
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-900">
                          {item.user_name}
                        </div>
                        <div className="text-xs text-slate-500">
                          {item.user_email}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                          {item.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-700">
                        {item.extraction_method}
                        {item.needs_manual_extraction ? " / manual" : ""}
                      </td>
                      <td className="px-6 py-4 text-slate-700">
                        {new Date(item.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4">
                        <a
                          href={`/admin/kyc/${item.id}`}
                          className="inline-flex rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
                        >
                          Review
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
