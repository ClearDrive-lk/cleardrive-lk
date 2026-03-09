"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { isAxiosError } from "axios";
import { apiClient } from "@/lib/api-client";

interface ComparisonRow {
  label: string;
  extracted_value: string | null;
  user_value: string | null;
  matches: boolean;
}

interface KycReviewDetail {
  id: string;
  user_id: string;
  user_email: string;
  user_name: string;
  status: string;
  created_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
  rejection_reason: string | null;
  nic_front_url: string;
  nic_back_url: string;
  selfie_url: string;
  extracted_data: Record<string, unknown>;
  user_provided_data: Record<string, string | null>;
  discrepancies: Record<string, boolean>;
  comparison_rows: ComparisonRow[];
  extraction_method: string;
  auto_extracted: boolean;
  needs_manual_extraction: boolean;
}

export default function AdminKycReviewDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const kycId = params.id;

  const [detail, setDetail] = useState<KycReviewDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  useEffect(() => {
    const loadDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<KycReviewDetail>(
          `/admin/kyc/${kycId}`,
        );
        setDetail(response.data);
      } catch (err: unknown) {
        if (isAxiosError(err)) {
          setError(
            (err.response?.data as { detail?: string } | undefined)?.detail ??
              "Failed to load KYC review details.",
          );
        } else {
          setError("Failed to load KYC review details.");
        }
      } finally {
        setLoading(false);
      }
    };

    if (kycId) {
      void loadDetail();
    }
  }, [kycId]);

  const mismatchCount = useMemo(
    () => detail?.comparison_rows.filter((row) => !row.matches).length ?? 0,
    [detail],
  );

  const approveKyc = async () => {
    if (!detail) {
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await apiClient.post(`/admin/kyc/${detail.id}/approve`);
      router.push("/admin/kyc");
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to approve KYC.",
        );
      } else {
        setError("Failed to approve KYC.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const rejectKyc = async () => {
    if (!detail) {
      return;
    }
    if (rejectReason.trim().length < 10) {
      setError("Rejection reason must be at least 10 characters.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await apiClient.post(`/admin/kyc/${detail.id}/reject`, {
        reason: rejectReason.trim(),
      });
      router.push("/admin/kyc");
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to reject KYC.",
        );
      } else {
        setError("Failed to reject KYC.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-6 text-slate-500">Loading KYC review...</div>;
  }

  if (error && !detail) {
    return <div className="p-6 text-red-600">{error}</div>;
  }

  if (!detail) {
    return <div className="p-6 text-slate-500">KYC record not found.</div>;
  }

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-3xl bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-blue-600">
            CD-52 KYC Admin Review
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-900">
            {detail.user_name}
          </h1>
          <p className="mt-2 text-sm text-slate-600">{detail.user_email}</p>
        </header>

        <section className="grid gap-4 sm:grid-cols-4">
          <div className="rounded-2xl bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Status</p>
            <p className="mt-2 text-lg font-semibold text-slate-900">
              {detail.status}
            </p>
          </div>
          <div className="rounded-2xl bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Extraction</p>
            <p className="mt-2 text-lg font-semibold text-slate-900">
              {detail.extraction_method}
            </p>
          </div>
          <div className="rounded-2xl bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Discrepancies</p>
            <p className="mt-2 text-lg font-semibold text-slate-900">
              {mismatchCount}
            </p>
          </div>
          <div className="rounded-2xl bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Submitted</p>
            <p className="mt-2 text-lg font-semibold text-slate-900">
              {new Date(detail.created_at).toLocaleString()}
            </p>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-3xl bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">NIC Front</h2>
            <img
              src={detail.nic_front_url}
              alt="NIC front"
              className="mt-4 w-full rounded-2xl border border-slate-200 object-cover"
            />
          </div>
          <div className="rounded-3xl bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">NIC Back</h2>
            <img
              src={detail.nic_back_url}
              alt="NIC back"
              className="mt-4 w-full rounded-2xl border border-slate-200 object-cover"
            />
          </div>
          <div className="rounded-3xl bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Selfie</h2>
            <img
              src={detail.selfie_url}
              alt="Selfie"
              className="mt-4 w-full rounded-2xl border border-slate-200 object-cover"
            />
          </div>
        </section>

        <section className="rounded-3xl bg-white shadow-sm">
          <div className="border-b border-slate-200 px-6 py-4">
            <h2 className="text-xl font-semibold text-slate-900">
              Extracted vs Stored Data
            </h2>
            <p className="text-sm text-slate-500">
              Mismatches are highlighted to support admin review.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left font-medium uppercase tracking-wide text-slate-500">
                    Field
                  </th>
                  <th className="px-6 py-3 text-left font-medium uppercase tracking-wide text-slate-500">
                    Extracted
                  </th>
                  <th className="px-6 py-3 text-left font-medium uppercase tracking-wide text-slate-500">
                    Stored
                  </th>
                  <th className="px-6 py-3 text-left font-medium uppercase tracking-wide text-slate-500">
                    Result
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {detail.comparison_rows.map((row) => (
                  <tr
                    key={row.label}
                    className={row.matches ? "bg-white" : "bg-red-50"}
                  >
                    <td className="px-6 py-4 font-medium text-slate-900">
                      {row.label}
                    </td>
                    <td className="px-6 py-4 text-slate-700">
                      {row.extracted_value || "N/A"}
                    </td>
                    <td className="px-6 py-4 text-slate-700">
                      {row.user_value || "N/A"}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
                          row.matches
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {row.matches ? "Match" : "Mismatch"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="rounded-3xl bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Decision</h2>
          <p className="mt-2 text-sm text-slate-600">
            Approval sends a notification to the customer. Rejection requires a
            reason and also sends a notification email.
          </p>

          <label className="mt-5 block text-sm font-medium text-slate-700">
            Rejection Reason
          </label>
          <textarea
            value={rejectReason}
            onChange={(event) => setRejectReason(event.target.value)}
            className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            rows={4}
            placeholder="Explain why this KYC submission should be rejected."
          />

          {error ? (
            <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          <div className="mt-5 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={approveKyc}
              disabled={submitting}
              className="rounded-xl bg-emerald-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? "Processing..." : "Approve KYC"}
            </button>
            <button
              type="button"
              onClick={rejectKyc}
              disabled={submitting}
              className="rounded-xl bg-red-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? "Processing..." : "Reject KYC"}
            </button>
            <button
              type="button"
              onClick={() => router.push("/admin/kyc")}
              className="rounded-xl border border-slate-300 px-5 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              Back to Queue
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
