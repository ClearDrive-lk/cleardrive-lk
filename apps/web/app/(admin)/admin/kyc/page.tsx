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

function extractionBadge(item: PendingKycItem) {
  if (item.needs_manual_extraction) {
    return {
      label: "Manual Review Required",
      className: "bg-amber-500/10 text-amber-200 border border-amber-500/20",
    };
  }
  if (item.extraction_method === "manual") {
    return {
      label: "Manually Extracted",
      className: "bg-sky-500/10 text-sky-200 border border-sky-500/20",
    };
  }
  return {
    label: `Auto Extracted (${item.extraction_method})`,
    className:
      "bg-emerald-500/10 text-emerald-200 border border-emerald-500/20",
  };
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
    <div className="min-h-screen p-6 text-white">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-[#FE7743]">
            CD-52 KYC Admin Review
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-white">
            Pending KYC Reviews
          </h1>
          <p className="mt-2 text-sm text-gray-400">
            Review pending KYC submissions, compare extracted fields, and
            approve or reject with a reason when needed.
          </p>
        </header>

        <section className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
            <p className="text-sm text-gray-400">Queue Size</p>
            <p className="mt-2 text-3xl font-semibold text-white">
              {items.length}
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
            <p className="text-sm text-gray-400">Auto Extracted</p>
            <p className="mt-2 text-3xl font-semibold text-white">
              {items.filter((item) => item.auto_extracted).length}
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">
            <p className="text-sm text-gray-400">Manual Review Needed</p>
            <p className="mt-2 text-3xl font-semibold text-white">
              {items.filter((item) => item.needs_manual_extraction).length}
            </p>
          </div>
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/5 shadow-sm">
          <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
            <div>
              <h2 className="text-xl font-semibold text-white">Review Queue</h2>
              <p className="text-sm text-gray-400">
                Oldest submissions are shown first.
              </p>
            </div>
            <button
              type="button"
              onClick={() => void loadItems()}
              className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-gray-200 transition hover:bg-white/10"
            >
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="px-6 py-16 text-center text-gray-400">
              Loading KYC queue...
            </div>
          ) : error ? (
            <div className="px-6 py-16 text-center text-red-300">{error}</div>
          ) : items.length === 0 ? (
            <div className="px-6 py-16 text-center text-gray-400">
              No KYC submissions are waiting for review.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-white/10 text-sm">
                <thead className="bg-white/5">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                      Extraction
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                      Submitted
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-400">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {items.map((item) => {
                    const badge = extractionBadge(item);
                    return (
                      <tr key={item.id} className="hover:bg-white/5">
                        <td className="px-6 py-4">
                          <div className="font-medium text-white">
                            {item.user_name}
                          </div>
                          <div className="text-xs text-gray-500">
                            {item.user_email}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-200">
                            {item.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-gray-300">
                          <span
                            className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${badge.className}`}
                          >
                            {badge.label}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-gray-300">
                          {new Date(item.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4">
                          <a
                            href={`/admin/kyc/${item.id}`}
                            className="inline-flex rounded-xl bg-[#FE7743] px-4 py-2 text-sm font-semibold text-black transition hover:bg-[#FE7743]/90"
                          >
                            Review
                          </a>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
