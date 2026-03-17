"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { isAxiosError } from "axios";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  XCircle,
  RefreshCw,
  ClipboardCheck,
} from "lucide-react";

import { apiClient } from "@/lib/api-client";
import { cn } from "@/lib/utils";

type GazetteRule = {
  vehicle_type?: string;
  fuel_type?: string;
  engine_min?: number;
  engine_max?: number;
  customs_percent?: number;
  excise_percent?: number;
  vat_percent?: number;
  pal_percent?: number;
  cess_percent?: number;
  apply_on?: string;
  notes?: string;
};

type GazettePreview = {
  gazette_no?: string;
  effective_date?: string;
  rules?: GazetteRule[];
  text?: string;
  tables?: unknown[];
  error?: string;
};

type GazetteUploadResponse = {
  gazette_id: string;
  gazette_no: string;
  effective_date: string | null;
  rules_count: number;
  confidence: number;
  status: string;
  preview: GazettePreview;
  message?: string | null;
};

type GazetteDetailResponse = {
  gazette_id: string;
  gazette_no: string;
  effective_date: string | null;
  rules_count: number;
  status: string;
  preview: GazettePreview;
  rejection_reason?: string | null;
  uploaded_by?: string | null;
  approved_by?: string | null;
  created_at: string;
};

type GazetteHistoryItem = {
  id: string;
  gazette_no: string;
  effective_date: string | null;
  status: string;
  rules_count: number;
  created_at: string;
  uploaded_by?: string | null;
  approved_by?: string | null;
  rejection_reason?: string | null;
};

type GazetteHistoryResponse = {
  items: GazetteHistoryItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
};

const STATUS_STYLES: Record<string, string> = {
  PENDING: "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
  APPROVED: "bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200",
  REJECTED: "bg-rose-100 text-rose-800 ring-1 ring-rose-200",
  NEEDS_MANUAL_REVIEW: "bg-orange-100 text-orange-800 ring-1 ring-orange-200",
};

const MAX_FILE_SIZE_MB = 50;

function statusBadge(status: string) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide",
        STATUS_STYLES[status] ??
          "bg-slate-100 text-slate-700 ring-1 ring-slate-200",
      )}
    >
      {status}
    </span>
  );
}

function formatDate(value: string | null | undefined) {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString();
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export default function GazetteManagementPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [gazetteNo, setGazetteNo] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] =
    useState<GazetteUploadResponse | null>(null);

  const [history, setHistory] = useState<GazetteHistoryResponse | null>(null);
  const [historyStatus, setHistoryStatus] = useState("");
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const [selectedGazette, setSelectedGazette] =
    useState<GazetteDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [decisionLoading, setDecisionLoading] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [decisionSuccess, setDecisionSuccess] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");

  const rules = useMemo(() => {
    if (!selectedGazette?.preview?.rules) return [];
    if (!Array.isArray(selectedGazette.preview.rules)) return [];
    return selectedGazette.preview.rules;
  }, [selectedGazette]);

  const loadHistory = useCallback(
    async (page = 1) => {
      setHistoryLoading(true);
      setHistoryError(null);
      try {
        const params = new URLSearchParams({
          page: String(page),
          limit: "12",
        });
        if (historyStatus) {
          params.set("status", historyStatus);
        }
        const response = await apiClient.get<GazetteHistoryResponse>(
          `/gazette/history?${params.toString()}`,
        );
        setHistory(response.data);
      } catch (err: unknown) {
        if (isAxiosError(err)) {
          setHistoryError(
            (err.response?.data as { detail?: string } | undefined)?.detail ??
              "Failed to load gazette history.",
          );
        } else {
          setHistoryError("Failed to load gazette history.");
        }
      } finally {
        setHistoryLoading(false);
      }
    },
    [historyStatus],
  );

  const loadGazetteDetail = useCallback(async (gazetteId: string) => {
    setDetailLoading(true);
    setDetailError(null);
    try {
      const response = await apiClient.get<GazetteDetailResponse>(
        `/gazette/${gazetteId}`,
      );
      setSelectedGazette(response.data);
      setDecisionSuccess(null);
      setDecisionError(null);
      setRejectionReason(response.data.rejection_reason ?? "");
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setDetailError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to load gazette details.",
        );
      } else {
        setDetailError("Failed to load gazette details.");
      }
    } finally {
      setDetailLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHistory(1);
  }, [loadHistory, historyStatus]);

  const validateFile = (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      return "Only PDF files are allowed.";
    }
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      return `File is too large. Max ${MAX_FILE_SIZE_MB}MB.`;
    }
    return null;
  };

  const handleFileSelect = (file: File) => {
    const error = validateFile(file);
    if (error) {
      setUploadError(error);
      setSelectedFile(null);
      return;
    }
    setUploadError(null);
    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!gazetteNo.trim()) {
      setUploadError("Gazette number is required.");
      return;
    }
    if (!selectedFile) {
      setUploadError("Please select a PDF file.");
      return;
    }

    setUploading(true);
    setUploadError(null);
    setDecisionSuccess(null);
    setDecisionError(null);
    try {
      const form = new FormData();
      form.append("file", selectedFile);
      form.append("gazette_no", gazetteNo.trim());

      const response = await apiClient.post<GazetteUploadResponse>(
        "/gazette/upload",
        form,
        {
          headers: { "Content-Type": "multipart/form-data" },
        },
      );

      setUploadResult(response.data);
      setSelectedGazette({
        gazette_id: response.data.gazette_id,
        gazette_no: response.data.gazette_no,
        effective_date: response.data.effective_date,
        rules_count: response.data.rules_count,
        status: response.data.status,
        preview: response.data.preview,
        created_at: new Date().toISOString(),
      });
      setRejectionReason("");
      setGazetteNo("");
      setSelectedFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
      await loadHistory(1);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setUploadError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Upload failed.",
        );
      } else {
        setUploadError("Upload failed.");
      }
    } finally {
      setUploading(false);
    }
  };

  const approveGazette = async () => {
    if (!selectedGazette) return;
    setDecisionLoading(true);
    setDecisionError(null);
    setDecisionSuccess(null);
    try {
      await apiClient.post(`/gazette/${selectedGazette.gazette_id}/approve`);
      setDecisionSuccess("Gazette approved. Tax rules activated.");
      setSelectedGazette((current) =>
        current
          ? {
              ...current,
              status: "APPROVED",
              rejection_reason: null,
            }
          : current,
      );
      await loadHistory(history?.page ?? 1);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setDecisionError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Approval failed.",
        );
      } else {
        setDecisionError("Approval failed.");
      }
    } finally {
      setDecisionLoading(false);
    }
  };

  const rejectGazette = async () => {
    if (!selectedGazette) return;
    const reason = rejectionReason.trim();
    if (reason.length < 10) {
      setDecisionError("Rejection reason must be at least 10 characters.");
      return;
    }
    setDecisionLoading(true);
    setDecisionError(null);
    setDecisionSuccess(null);
    try {
      await apiClient.post(`/gazette/${selectedGazette.gazette_id}/reject`, {
        reason,
      });
      setDecisionSuccess("Gazette rejected. Reason saved.");
      setSelectedGazette((current) =>
        current
          ? {
              ...current,
              status: "REJECTED",
              rejection_reason: reason,
            }
          : current,
      );
      await loadHistory(history?.page ?? 1);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setDecisionError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Rejection failed.",
        );
      } else {
        setDecisionError("Rejection failed.");
      }
    } finally {
      setDecisionLoading(false);
    }
  };

  return (
    <div className="min-h-screen space-y-8 p-6">
      <header className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm backdrop-blur">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-orange-500">
              Gazette Control
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-900">
              Gazette Upload, Review, and Approval
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Upload gazette PDFs, review extracted tax rules, and approve or
              reject with full audit coverage.
            </p>
          </div>
          <div className="rounded-2xl bg-slate-900 px-4 py-3 text-sm text-slate-100">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
              Status
            </p>
            <p className="mt-1 text-lg font-semibold">
              {history?.total ?? 0} gazettes tracked
            </p>
          </div>
        </div>
      </header>

      <section id="upload" className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">
                Upload Gazette PDF
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                PDF only. Max {MAX_FILE_SIZE_MB}MB per file.
              </p>
            </div>
            <UploadCloud className="h-8 w-8 text-orange-400" />
          </div>

          <div className="mt-6 space-y-4">
            <label className="space-y-2 text-sm font-medium text-slate-700">
              Gazette Number
              <input
                value={gazetteNo}
                onChange={(event) => setGazetteNo(event.target.value)}
                placeholder="Example: 2026/03"
                className="w-full rounded-2xl border border-white/10 bg-transparent px-4 py-3 text-sm text-white focus:border-orange-400 focus:outline-none"
              />
            </label>

            <div
              onDragOver={(event) => {
                event.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragOver(false);
                const file = event.dataTransfer.files?.[0];
                if (file) handleFileSelect(file);
              }}
              onClick={() => inputRef.current?.click()}
              className={cn(
                "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-3xl border-2 border-dashed px-6 py-10 text-center transition",
                dragOver
                  ? "border-orange-400 bg-orange-500/10"
                  : "border-white/10 bg-white/5 hover:border-orange-300 hover:bg-orange-500/10",
              )}
            >
              <FileText className="h-10 w-10 text-gray-400" />
              <div className="text-sm text-gray-300">
                <p className="font-semibold text-white">
                  Drop PDF here or click to browse
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  Only gazette PDFs are supported.
                </p>
              </div>
              {selectedFile && (
                <div className="rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white">
                  {selectedFile.name}
                </div>
              )}
            </div>

            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) handleFileSelect(file);
              }}
            />

            {uploadError && (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {uploadError}
              </div>
            )}

            <button
              type="button"
              onClick={handleUpload}
              disabled={uploading}
              className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {uploading ? "Uploading..." : "Upload and Extract Rules"}
            </button>

            {uploadResult?.message && (
              <div className="rounded-2xl border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-700">
                {uploadResult.message}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 p-6 text-slate-100 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
            Latest Upload
          </p>
          {uploadResult ? (
            <div className="mt-4 space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Gazette</span>
                <span className="font-semibold text-white">
                  {uploadResult.gazette_no}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Effective Date</span>
                <span className="font-semibold text-white">
                  {formatDate(uploadResult.effective_date)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Rules Extracted</span>
                <span className="font-semibold text-white">
                  {uploadResult.rules_count}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Confidence</span>
                <span className="font-semibold text-white">
                  {(uploadResult.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div>{statusBadge(uploadResult.status)}</div>
            </div>
          ) : (
            <div className="mt-4 text-sm text-slate-400">
              No uploads yet. Submit a gazette to generate previews.
            </div>
          )}
        </div>
      </section>

      <section
        id="review"
        className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm"
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">
              Extracted Rules Review
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Validate the extracted rules before approval.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {selectedGazette && (
              <div className="rounded-2xl border border-white/10 px-3 py-2 text-sm text-gray-300">
                Gazette{" "}
                <span className="font-semibold">
                  {selectedGazette.gazette_no}
                </span>
              </div>
            )}
            {selectedGazette && statusBadge(selectedGazette.status)}
          </div>
        </div>

        {detailLoading && (
          <div className="mt-6 text-sm text-slate-500">Loading gazette...</div>
        )}
        {detailError && (
          <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {detailError}
          </div>
        )}

        {!selectedGazette && !detailLoading && !detailError && (
          <div className="mt-6 rounded-2xl border border-dashed border-slate-200 px-6 py-10 text-center text-sm text-slate-500">
            Select a gazette from history or upload a new one to review.
          </div>
        )}

        {selectedGazette && (
          <div className="mt-6 space-y-6">
            <div className="grid gap-4 md:grid-cols-4">
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Effective Date
                </p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {formatDate(selectedGazette.effective_date)}
                </p>
              </div>
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Rules
                </p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {selectedGazette.rules_count}
                </p>
              </div>
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Uploaded
                </p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {formatDateTime(selectedGazette.created_at)}
                </p>
              </div>
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Uploaded By
                </p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {selectedGazette.uploaded_by ?? "Unknown"}
                </p>
              </div>
            </div>

            {rules.length === 0 ? (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-700">
                No structured rules were extracted. Manual review is required.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-2xl border border-white/10">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-white/5 text-xs uppercase tracking-wide text-gray-400">
                    <tr>
                      <th className="px-4 py-3">Vehicle</th>
                      <th className="px-4 py-3">Fuel</th>
                      <th className="px-4 py-3">Engine Range</th>
                      <th className="px-4 py-3">Customs %</th>
                      <th className="px-4 py-3">Excise %</th>
                      <th className="px-4 py-3">VAT %</th>
                      <th className="px-4 py-3">PAL %</th>
                      <th className="px-4 py-3">CESS %</th>
                      <th className="px-4 py-3">Apply On</th>
                      <th className="px-4 py-3">Notes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {rules.map((rule, index) => (
                      <tr
                        key={`${rule.vehicle_type}-${index}`}
                        className="hover:bg-white/5"
                      >
                        <td className="px-4 py-3 font-medium text-white">
                          {rule.vehicle_type ?? "N/A"}
                        </td>
                        <td className="px-4 py-3 text-gray-300">
                          {rule.fuel_type ?? "N/A"}
                        </td>
                        <td className="px-4 py-3 text-gray-300">
                          {rule.engine_min ?? 0} - {rule.engine_max ?? "N/A"}
                        </td>
                        <td className="px-4 py-3 text-gray-300">
                          {rule.customs_percent ?? 0}%
                        </td>
                        <td className="px-4 py-3 text-gray-300">
                          {rule.excise_percent ?? 0}%
                        </td>
                        <td className="px-4 py-3 text-gray-300">
                          {rule.vat_percent ?? 0}%
                        </td>
                        <td className="px-4 py-3 text-gray-300">
                          {rule.pal_percent ?? 0}%
                        </td>
                        <td className="px-4 py-3 text-gray-300">
                          {rule.cess_percent ?? 0}%
                        </td>
                        <td className="px-4 py-3 text-gray-300">
                          {rule.apply_on ?? "N/A"}
                        </td>
                        <td className="px-4 py-3 text-gray-300">
                          {rule.notes ?? "N/A"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-2xl border border-white/10 p-4">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                  Rejection Reason
                </label>
                <textarea
                  value={rejectionReason}
                  onChange={(event) => setRejectionReason(event.target.value)}
                  placeholder="Provide a detailed reason if rejecting."
                  className="mt-2 min-h-[120px] w-full rounded-2xl border border-white/10 bg-transparent px-4 py-3 text-sm text-white focus:border-rose-400 focus:outline-none"
                />
                <p className="mt-2 text-xs text-gray-500">
                  Minimum 10 characters required for rejection.
                </p>
              </div>
              <div className="space-y-3">
                <button
                  type="button"
                  onClick={approveGazette}
                  disabled={
                    decisionLoading || selectedGazette.status === "APPROVED"
                  }
                  className="flex w-full items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Approve Gazette
                </button>
                <button
                  type="button"
                  onClick={rejectGazette}
                  disabled={
                    decisionLoading || selectedGazette.status === "REJECTED"
                  }
                  className="flex w-full items-center justify-center gap-2 rounded-2xl bg-rose-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <XCircle className="h-4 w-4" />
                  Reject Gazette
                </button>
                {decisionError && (
                  <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                    {decisionError}
                  </div>
                )}
                {decisionSuccess && (
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                    {decisionSuccess}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </section>

      <section
        id="history"
        className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm"
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">
              Gazette History
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Track approvals and review pending gazettes.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-sm text-gray-300">
              Status
              <select
                value={historyStatus}
                onChange={(event) => setHistoryStatus(event.target.value)}
                className="ml-2 rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white"
              >
                <option value="">All</option>
                <option value="PENDING">PENDING</option>
                <option value="APPROVED">APPROVED</option>
                <option value="REJECTED">REJECTED</option>
              </select>
            </label>
            <button
              type="button"
              onClick={() => void loadHistory(1)}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-700 transition hover:bg-slate-50"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </div>

        {historyLoading ? (
          <div className="mt-6 text-sm text-slate-500">Loading history...</div>
        ) : historyError ? (
          <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {historyError}
          </div>
        ) : !history || history.items.length === 0 ? (
          <div className="mt-6 rounded-2xl border border-dashed border-white/10 px-6 py-10 text-center text-sm text-gray-500">
            No gazettes found for the selected filter.
          </div>
        ) : (
          <div className="mt-6 space-y-4">
            <div className="overflow-x-auto rounded-2xl border border-white/10">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-white/5 text-xs uppercase tracking-wide text-gray-400">
                  <tr>
                    <th className="px-4 py-3">Gazette</th>
                    <th className="px-4 py-3">Effective Date</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Rules</th>
                    <th className="px-4 py-3">Uploaded</th>
                    <th className="px-4 py-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {history.items.map((item) => (
                    <tr key={item.id} className="hover:bg-white/5">
                      <td className="px-4 py-3 font-medium text-white">
                        {item.gazette_no}
                      </td>
                      <td className="px-4 py-3 text-gray-300">
                        {formatDate(item.effective_date)}
                      </td>
                      <td className="px-4 py-3">{statusBadge(item.status)}</td>
                      <td className="px-4 py-3 text-gray-300">
                        {item.rules_count}
                      </td>
                      <td className="px-4 py-3 text-gray-300">
                        {formatDateTime(item.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          onClick={() => void loadGazetteDetail(item.id)}
                          className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-3 py-2 text-xs font-semibold text-white transition hover:bg-slate-800"
                        >
                          <ClipboardCheck className="h-4 w-4" />
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-slate-500">
                Page {history.page} of {history.total_pages}
              </p>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() =>
                    void loadHistory(Math.max(1, history.page - 1))
                  }
                  disabled={history.page <= 1}
                  className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() =>
                    void loadHistory(
                      Math.min(history.total_pages, history.page + 1),
                    )
                  }
                  disabled={history.page >= history.total_pages}
                  className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
