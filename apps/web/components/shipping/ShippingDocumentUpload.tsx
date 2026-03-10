"use client";

import { useState, useRef, useCallback } from "react";
import { isAxiosError } from "axios";
import { apiClient } from "@/lib/api-client";

// ─── Types ────────────────────────────────────────────────────────────────────

type DocumentType =
  | "BILL_OF_LADING"
  | "BILL_OF_LANDING"
  | "PACKING_LIST"
  | "EXPORT_CERTIFICATE"
  | "COMMERCIAL_INVOICE"
  | "INSURANCE_CERTIFICATE";

interface DocumentMeta {
  label: string;
  required: boolean;
  accept: string;
  hint: string;
}

interface UploadedDocument {
  id: string;
  shipment_id: string;
  order_id: string;
  document_type: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  file_url: string;
  verified: boolean;
  uploaded_at: string;
  uploaded_by: string;
}

interface RequiredDocumentsCheck {
  order_id: string;
  total_required: number;
  total_uploaded: number;
  all_uploaded: boolean;
  uploaded_documents: string[];
  missing_documents: string[];
  completion_percentage: number;
}

interface ShippingDocumentUploadProps {
  orderId: string;
  onAllUploaded?: () => void;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const DOCUMENT_TYPES: Record<DocumentType, DocumentMeta> = {
  BILL_OF_LADING: {
    label: "Bill of Lading",
    required: true,
    accept: "application/pdf",
    hint: "PDF only · max 10 MB",
  },
  BILL_OF_LANDING: {
    label: "Bill of Landing",
    required: true,
    accept: "application/pdf",
    hint: "PDF only · max 10 MB",
  },
  COMMERCIAL_INVOICE: {
    label: "Commercial Invoice",
    required: true,
    accept: "application/pdf",
    hint: "PDF only · max 10 MB",
  },
  PACKING_LIST: {
    label: "Packing List",
    required: true,
    accept: "application/pdf",
    hint: "PDF only · max 10 MB",
  },
  EXPORT_CERTIFICATE: {
    label: "Export Certificate",
    required: false,
    accept: "application/pdf,image/jpeg,image/png,image/webp",
    hint: "PDF or image · max 10 MB",
  },
  INSURANCE_CERTIFICATE: {
    label: "Insurance Certificate",
    required: false,
    accept: "application/pdf,image/jpeg,image/png,image/webp",
    hint: "PDF or image · max 10 MB",
  },
};

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

const ALLOWED_MIME = new Set([
  "application/pdf",
  "image/jpeg",
  "image/png",
  "image/webp",
]);

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function docTypeFromUploaded(raw: string): DocumentType | null {
  return (
    (Object.keys(DOCUMENT_TYPES) as DocumentType[]).find((k) => k === raw) ??
    null
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatusBadge({ verified }: { verified: boolean }) {
  if (verified) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        Verified
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-amber-200">
      <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
      Pending
    </span>
  );
}

function ProgressBar({ pct }: { pct: number }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
      <div
        className="h-full rounded-full bg-blue-500 transition-all duration-500"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

// ─── Upload Row ───────────────────────────────────────────────────────────────

interface UploadRowProps {
  docType: DocumentType;
  meta: DocumentMeta;
  existing: UploadedDocument | undefined;
  orderId: string;
  onUploaded: (doc: UploadedDocument) => void;
}

function UploadRow({
  docType,
  meta,
  existing,
  orderId,
  onUploaded,
}: UploadRowProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);

  const upload = useCallback(
    async (file: File) => {
      setError("");

      // Client-side validation
      if (!ALLOWED_MIME.has(file.type)) {
        setError("Invalid file type. Allowed: PDF, JPEG, PNG, WebP");
        return;
      }
      if (file.size > MAX_FILE_SIZE) {
        setError("File too large. Maximum size: 10 MB");
        return;
      }

      setUploading(true);
      try {
        const form = new FormData();
        form.append("document_type", docType);
        form.append("file", file);

        const res = await apiClient.post<UploadedDocument>(
          `/shipping/${orderId}/documents`,
          form,
          { headers: { "Content-Type": "multipart/form-data" } },
        );
        onUploaded(res.data);
      } catch (err: unknown) {
        if (isAxiosError(err)) {
          setError(
            (err.response?.data as { detail?: string } | undefined)?.detail ??
              "Upload failed.",
          );
        } else {
          setError("Upload failed.");
        }
      } finally {
        setUploading(false);
      }
    },
    [docType, orderId, onUploaded],
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) void upload(file);
    // reset so same file can be re-uploaded
    e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) void upload(file);
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-800">
              {meta.label}
            </span>
            {meta.required ? (
              <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-blue-600 ring-1 ring-blue-200">
                Required
              </span>
            ) : (
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Optional
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-slate-400">{meta.hint}</p>
        </div>

        {/* Status / upload button */}
        {existing ? (
          <StatusBadge verified={existing.verified} />
        ) : (
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
            className="shrink-0 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {uploading ? "Uploading…" : "Upload"}
          </button>
        )}
      </div>

      {/* Existing file info */}
      {existing && (
        <div className="mt-3 flex items-center justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2">
          <div className="flex items-center gap-2 min-w-0">
            {/* PDF / image icon */}
            <span className="text-slate-400">
              {existing.mime_type === "application/pdf" ? (
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
                  />
                </svg>
              ) : (
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z"
                  />
                </svg>
              )}
            </span>
            <span className="truncate text-xs font-medium text-slate-700">
              {existing.file_name}
            </span>
            <span className="shrink-0 text-xs text-slate-400">
              {formatBytes(existing.file_size)}
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <a
              href={existing.file_url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-md px-2 py-1 text-xs font-medium text-blue-600 ring-1 ring-blue-200 transition hover:bg-blue-50"
            >
              Preview
            </a>
            {/* Re-upload option */}
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
              className="rounded-md px-2 py-1 text-xs font-medium text-slate-500 ring-1 ring-slate-200 transition hover:bg-slate-100 disabled:opacity-50"
            >
              Replace
            </button>
          </div>
        </div>
      )}

      {/* Drop zone (shown when no existing doc) */}
      {!existing && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`mt-3 cursor-pointer rounded-lg border-2 border-dashed px-4 py-5 text-center transition
            ${
              dragOver
                ? "border-blue-400 bg-blue-50"
                : "border-slate-200 bg-slate-50 hover:border-blue-300 hover:bg-blue-50/50"
            }
            ${uploading ? "pointer-events-none opacity-60" : ""}
          `}
        >
          {uploading ? (
            <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
              <svg
                className="h-4 w-4 animate-spin"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"
                />
              </svg>
              Uploading…
            </div>
          ) : (
            <p className="text-xs text-slate-400">
              Drop file here or{" "}
              <span className="font-medium text-blue-600">browse</span>
            </p>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <p className="mt-2 rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs text-red-700">
          {error}
        </p>
      )}

      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept={meta.accept}
        className="hidden"
        onChange={handleFileChange}
      />
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function ShippingDocumentUpload({
  orderId,
  onAllUploaded,
}: ShippingDocumentUploadProps) {
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [check, setCheck] = useState<RequiredDocumentsCheck | null>(null);
  const [loadingCheck, setLoadingCheck] = useState(false);
  const [checkError, setCheckError] = useState("");

  // Fetch latest completion status
  const refreshCheck = useCallback(async () => {
    setLoadingCheck(true);
    setCheckError("");
    try {
      const res = await apiClient.get<RequiredDocumentsCheck>(
        `/shipping/${orderId}/documents/check`,
      );
      setCheck(res.data);
      if (res.data.all_uploaded) onAllUploaded?.();
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setCheckError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to fetch document status.",
        );
      } else {
        setCheckError("Failed to fetch document status.");
      }
    } finally {
      setLoadingCheck(false);
    }
  }, [orderId, onAllUploaded]);

  // Called when a single doc finishes uploading
  const handleUploaded = useCallback(
    (doc: UploadedDocument) => {
      setDocuments((prev) => {
        const filtered = prev.filter(
          (d) => d.document_type !== doc.document_type,
        );
        return [...filtered, doc];
      });
      void refreshCheck();
    },
    [refreshCheck],
  );

  // Find uploaded doc for a given type
  const findDoc = (type: DocumentType) =>
    documents.find((d) => {
      const mapped = docTypeFromUploaded(d.document_type);
      return mapped === type;
    });

  const requiredTypes = (
    Object.entries(DOCUMENT_TYPES) as [DocumentType, DocumentMeta][]
  ).filter(([, m]) => m.required);
  const optionalTypes = (
    Object.entries(DOCUMENT_TYPES) as [DocumentType, DocumentMeta][]
  ).filter(([, m]) => !m.required);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold text-slate-900">
          Shipping Documents
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Upload the required documents for this shipment. All required
          documents must be submitted before admin approval.
        </p>
      </div>

      {/* Progress card */}
      {check && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-medium text-slate-700">
              Upload Progress
            </span>
            <span className="text-sm font-semibold text-slate-900">
              {check.total_uploaded} / {check.total_required} required
            </span>
          </div>
          <ProgressBar pct={check.completion_percentage} />

          {check.all_uploaded ? (
            <p className="mt-2 flex items-center gap-1.5 text-xs font-medium text-emerald-600">
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                />
              </svg>
              All required documents uploaded — ready for admin review.
            </p>
          ) : (
            <p className="mt-2 text-xs text-slate-500">
              Missing:{" "}
              <span className="font-medium text-slate-700">
                {check.missing_documents.join(", ")}
              </span>
            </p>
          )}
        </div>
      )}

      {checkError && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {checkError}
        </div>
      )}

      {/* Required documents */}
      <div>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Required Documents
        </h3>
        <div className="space-y-3">
          {requiredTypes.map(([type, meta]) => (
            <UploadRow
              key={type}
              docType={type}
              meta={meta}
              existing={findDoc(type)}
              orderId={orderId}
              onUploaded={handleUploaded}
            />
          ))}
        </div>
      </div>

      {/* Optional documents */}
      <div>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Optional Documents
        </h3>
        <div className="space-y-3">
          {optionalTypes.map(([type, meta]) => (
            <UploadRow
              key={type}
              docType={type}
              meta={meta}
              existing={findDoc(type)}
              orderId={orderId}
              onUploaded={handleUploaded}
            />
          ))}
        </div>
      </div>

      {/* Check status button */}
      <button
        type="button"
        onClick={() => void refreshCheck()}
        disabled={loadingCheck}
        className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loadingCheck ? "Checking…" : "Check Upload Status"}
      </button>
    </div>
  );
}
