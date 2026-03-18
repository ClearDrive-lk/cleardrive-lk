"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
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
  manual_extracted_by: string | null;
  manual_extracted_at: string | null;
}

interface ManualExtractionForm {
  nic_number: string;
  full_name: string;
  date_of_birth: string;
  address: string;
  gender: string;
  issue_date: string;
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
  const [manualForm, setManualForm] = useState<ManualExtractionForm>({
    nic_number: "",
    full_name: "",
    date_of_birth: "",
    address: "",
    gender: "",
    issue_date: "",
  });

  useEffect(() => {
    const loadDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<KycReviewDetail>(
          `/admin/kyc/${kycId}`,
        );
        setDetail(response.data);
        setManualForm({
          nic_number: ((
            response.data.extracted_data.front as Record<string, string>
          )?.nic_number ??
            response.data.user_provided_data.nic_number ??
            "") as string,
          full_name: ((
            response.data.extracted_data.front as Record<string, string>
          )?.full_name ??
            response.data.user_provided_data.full_name ??
            "") as string,
          date_of_birth: ((
            response.data.extracted_data.front as Record<string, string>
          )?.date_of_birth ??
            response.data.user_provided_data.date_of_birth ??
            "") as string,
          address: ((
            response.data.extracted_data.back as Record<string, string>
          )?.address ??
            response.data.user_provided_data.address ??
            "") as string,
          gender: ((response.data.extracted_data.back as Record<string, string>)
            ?.gender ??
            response.data.user_provided_data.gender ??
            "") as string,
          issue_date: ((
            response.data.extracted_data.back as Record<string, string>
          )?.issue_date ?? "") as string,
        });
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

  const extractionBadge = useMemo(() => {
    if (!detail) {
      return { label: "", className: "" };
    }
    if (detail.needs_manual_extraction) {
      return {
        label: "Manual Review Required",
        className: "bg-amber-500/10 text-amber-200 border border-amber-500/20",
      };
    }
    if (detail.extraction_method === "manual") {
      return {
        label: "Manually Extracted",
        className: "bg-sky-500/10 text-sky-200 border border-sky-500/20",
      };
    }
    return {
      label: `Auto Extracted (${detail.extraction_method})`,
      className:
        "bg-emerald-500/10 text-emerald-200 border border-emerald-500/20",
    };
  }, [detail]);

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

  const saveManualExtraction = async () => {
    if (!detail) {
      return;
    }
    if (
      !manualForm.nic_number.trim() ||
      !manualForm.full_name.trim() ||
      !manualForm.date_of_birth.trim() ||
      !manualForm.address.trim() ||
      !manualForm.gender.trim()
    ) {
      setError("Complete all required manual extraction fields.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const response = await apiClient.post<KycReviewDetail>(
        `/admin/kyc/${detail.id}/extract-manual`,
        {
          nic_number: manualForm.nic_number.trim(),
          full_name: manualForm.full_name.trim(),
          date_of_birth: manualForm.date_of_birth,
          address: manualForm.address.trim(),
          gender: manualForm.gender.trim(),
          issue_date: manualForm.issue_date || null,
        },
      );
      setDetail(response.data);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to save manual extraction.",
        );
      } else {
        setError("Failed to save manual extraction.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-6 text-[#546a7b]">Loading KYC review...</div>;
  }

  if (error && !detail) {
    return <div className="p-6 text-red-300">{error}</div>;
  }

  if (!detail) {
    return <div className="p-6 text-[#546a7b]">KYC record not found.</div>;
  }

  return (
    <div className="min-h-screen p-6 text-[#393d3f]">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-[#62929e]">
            CD-52 KYC Admin Review
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-[#393d3f]">
            {detail.user_name}
          </h1>
          <p className="mt-2 text-sm text-[#546a7b]">{detail.user_email}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <span
              className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${extractionBadge.className}`}
            >
              {extractionBadge.label}
            </span>
            {detail.manual_extracted_by ? (
              <span className="inline-flex rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-3 py-1 text-xs font-semibold text-gray-200">
                Saved by {detail.manual_extracted_by}
              </span>
            ) : null}
          </div>
        </header>

        <section className="grid gap-4 sm:grid-cols-4">
          <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5 shadow-sm">
            <p className="text-sm text-[#546a7b]">Status</p>
            <p className="mt-2 text-lg font-semibold text-[#393d3f]">
              {detail.status}
            </p>
          </div>
          <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5 shadow-sm">
            <p className="text-sm text-[#546a7b]">Extraction</p>
            <p className="mt-2 text-lg font-semibold text-[#393d3f]">
              {detail.extraction_method}
            </p>
          </div>
          <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5 shadow-sm">
            <p className="text-sm text-[#546a7b]">Discrepancies</p>
            <p className="mt-2 text-lg font-semibold text-[#393d3f]">
              {mismatchCount}
            </p>
          </div>
          <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5 shadow-sm">
            <p className="text-sm text-[#546a7b]">Submitted</p>
            <p className="mt-2 text-lg font-semibold text-[#393d3f]">
              {new Date(detail.created_at).toLocaleString()}
            </p>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-[#393d3f]">NIC Front</h2>
            <div className="relative mt-4 h-56 w-full overflow-hidden rounded-2xl border border-[#546a7b]/65">
              <Image
                src={detail.nic_front_url}
                alt="NIC front"
                fill
                sizes="(max-width: 1024px) 100vw, 33vw"
                className="object-cover"
              />
            </div>
          </div>
          <div className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-[#393d3f]">NIC Back</h2>
            <div className="relative mt-4 h-56 w-full overflow-hidden rounded-2xl border border-[#546a7b]/65">
              <Image
                src={detail.nic_back_url}
                alt="NIC back"
                fill
                sizes="(max-width: 1024px) 100vw, 33vw"
                className="object-cover"
              />
            </div>
          </div>
          <div className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-[#393d3f]">Selfie</h2>
            <div className="relative mt-4 h-56 w-full overflow-hidden rounded-2xl border border-[#546a7b]/65">
              <Image
                src={detail.selfie_url}
                alt="Selfie"
                fill
                sizes="(max-width: 1024px) 100vw, 33vw"
                className="object-cover"
              />
            </div>
          </div>
        </section>

        {detail.needs_manual_extraction ? (
          <section className="rounded-3xl border border-amber-500/30 bg-amber-500/10 p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-[#393d3f]">
              Manual Extraction Required
            </h2>
            <p className="mt-2 text-sm text-amber-100/80">
              Auto extraction did not complete. Enter the document data from the
              images, save it, then continue with approval or rejection.
            </p>

            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-medium text-[#546a7b]">
                  NIC Number
                </label>
                <input
                  type="text"
                  value={manualForm.nic_number}
                  onChange={(event) =>
                    setManualForm((current) => ({
                      ...current,
                      nic_number: event.target.value,
                    }))
                  }
                  className="w-full rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-4 py-3 text-sm text-gray-200"
                />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-[#546a7b]">
                  Full Name
                </label>
                <input
                  type="text"
                  value={manualForm.full_name}
                  onChange={(event) =>
                    setManualForm((current) => ({
                      ...current,
                      full_name: event.target.value,
                    }))
                  }
                  className="w-full rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-4 py-3 text-sm text-gray-200"
                />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-[#546a7b]">
                  Date of Birth
                </label>
                <input
                  type="date"
                  value={manualForm.date_of_birth}
                  onChange={(event) =>
                    setManualForm((current) => ({
                      ...current,
                      date_of_birth: event.target.value,
                    }))
                  }
                  className="w-full rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-4 py-3 text-sm text-gray-200"
                />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-[#546a7b]">
                  Gender
                </label>
                <input
                  type="text"
                  value={manualForm.gender}
                  onChange={(event) =>
                    setManualForm((current) => ({
                      ...current,
                      gender: event.target.value,
                    }))
                  }
                  className="w-full rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-4 py-3 text-sm text-gray-200"
                />
              </div>
              <div className="md:col-span-2">
                <label className="mb-2 block text-sm font-medium text-[#546a7b]">
                  Address
                </label>
                <textarea
                  value={manualForm.address}
                  onChange={(event) =>
                    setManualForm((current) => ({
                      ...current,
                      address: event.target.value,
                    }))
                  }
                  rows={3}
                  className="w-full rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-4 py-3 text-sm text-gray-200"
                />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-[#546a7b]">
                  Issue Date
                </label>
                <input
                  type="date"
                  value={manualForm.issue_date}
                  onChange={(event) =>
                    setManualForm((current) => ({
                      ...current,
                      issue_date: event.target.value,
                    }))
                  }
                  className="w-full rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-4 py-3 text-sm text-gray-200"
                />
              </div>
            </div>

            <div className="mt-5">
              <button
                type="button"
                onClick={saveManualExtraction}
                disabled={submitting}
                className="rounded-xl bg-[#62929e] px-5 py-3 text-sm font-semibold text-[#fdfdff] transition hover:bg-[#62929e]/90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {submitting ? "Saving..." : "Save Manual Extraction"}
              </button>
            </div>
          </section>
        ) : null}

        <section className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 shadow-sm">
          <div className="border-b border-[#546a7b]/65 px-6 py-4">
            <h2 className="text-xl font-semibold text-[#393d3f]">
              Extracted vs Stored Data
            </h2>
            <p className="text-sm text-[#546a7b]">
              Mismatches are highlighted to support admin review.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead className="bg-[#c6c5b9]/20">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                    Field
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                    Extracted
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                    Stored
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wide text-[#546a7b]">
                    Result
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {detail.comparison_rows.map((row) => (
                  <tr
                    key={row.label}
                    className={
                      row.matches
                        ? "hover:bg-[#c6c5b9]/20"
                        : "bg-red-500/10 hover:bg-red-500/20"
                    }
                  >
                    <td className="px-6 py-4 font-medium text-[#393d3f]">
                      {row.label}
                    </td>
                    <td className="px-6 py-4 text-[#546a7b]">
                      {row.extracted_value || "N/A"}
                    </td>
                    <td className="px-6 py-4 text-[#546a7b]">
                      {row.user_value || "N/A"}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
                          row.matches
                            ? "border border-emerald-500/20 bg-emerald-500/10 text-emerald-200"
                            : "border border-red-500/20 bg-red-500/10 text-red-200"
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

        <section className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[#393d3f]">Decision</h2>
          <p className="mt-2 text-sm text-[#546a7b]">
            Approval sends a notification to the customer. Rejection requires a
            reason and also sends a notification email.
          </p>

          <label className="mt-5 block text-sm font-medium text-[#546a7b]">
            Rejection Reason
          </label>
          <textarea
            value={rejectReason}
            onChange={(event) => setRejectReason(event.target.value)}
            className="mt-2 w-full rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-4 py-3 text-sm text-gray-200 shadow-sm focus:border-[#62929e]/60 focus:outline-none focus:ring-2 focus:ring-[#62929e]/60"
            rows={4}
            placeholder="Explain why this KYC submission should be rejected."
          />

          {error ? (
            <div className="mt-4 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          ) : null}

          <div className="mt-5 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={approveKyc}
              disabled={submitting || detail.needs_manual_extraction}
              className="rounded-xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-[#393d3f] transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? "Processing..." : "Approve KYC"}
            </button>
            <button
              type="button"
              onClick={rejectKyc}
              disabled={submitting}
              className="rounded-xl bg-red-500 px-5 py-3 text-sm font-semibold text-[#393d3f] transition hover:bg-red-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? "Processing..." : "Reject KYC"}
            </button>
            <button
              type="button"
              onClick={() => router.push("/admin/kyc")}
              className="rounded-xl border border-[#546a7b]/65 px-5 py-3 text-sm font-medium text-gray-200 transition hover:bg-[#c6c5b9]/30"
            >
              Back to Queue
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
