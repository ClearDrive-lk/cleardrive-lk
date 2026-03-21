"use client";

import { useEffect, useRef, useState } from "react";
import { isAxiosError } from "axios";
import { getAccessToken } from "@/lib/auth";
import { apiClient } from "@/lib/api-client";
import { UploadCloud, FileText, ExternalLink } from "lucide-react";

type TaxReferenceDocument = {
  id: string;
  title: string;
  issued_label: string;
  document_type?: string | null;
  description?: string | null;
  file_name: string;
  file_url: string;
  mime_type: string;
  display_order: number;
  is_active: boolean;
  created_at: string;
};

const defaultForm = {
  title: "",
  issuedLabel: "",
  documentType: "",
  description: "",
  displayOrder: "0",
  isActive: true,
};

function getApiErrorMessage(error: unknown): string {
  const data = (
    isAxiosError(error)
      ? error.response?.data
      : (
          error as
            | { response?: { data?: unknown; status?: number } }
            | null
            | undefined
        )?.response?.data
  ) as
    | { detail?: string | Array<{ msg?: string }> | { message?: string } }
    | undefined;
  const detail = data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => item?.msg)
      .filter((message): message is string => Boolean(message));
    if (messages.length > 0) {
      return messages.join(", ");
    }
  }

  if (detail && typeof detail === "object" && "message" in detail) {
    const message = detail.message;
    if (typeof message === "string" && message.trim()) {
      return message;
    }
  }

  const status = isAxiosError(error)
    ? error.response?.status
    : (error as { response?: { status?: number } } | null | undefined)?.response
        ?.status;

  return status === 422 ? "Invalid upload form data." : "Request failed.";
}

export default function AdminReferenceDocsPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [documents, setDocuments] = useState<TaxReferenceDocument[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [form, setForm] = useState(defaultForm);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [actingDocumentId, setActingDocumentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function loadDocuments() {
    setLoading(true);
    try {
      const response = await apiClient.get<TaxReferenceDocument[]>(
        "/admin/tax-reference-documents",
      );
      setDocuments(response.data);
    } catch {
      setError("Failed to load reference documents.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDocuments();
  }, []);

  async function sendMultipartDocumentUpdate(
    document: TaxReferenceDocument,
    nextActive: boolean,
  ) {
    const token = getAccessToken();
    const payload = new FormData();
    payload.append("title", document.title);
    payload.append("issued_label", document.issued_label);
    payload.append("document_type", document.document_type ?? "");
    payload.append("description", document.description ?? "");
    payload.append("display_order", String(document.display_order));
    payload.append("is_active", String(nextActive));

    const response = await fetch(
      `${apiClient.defaults.baseURL}/admin/tax-reference-documents/${document.id}`,
      {
        method: "PATCH",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: payload,
      },
    );

    if (!response.ok) {
      const responseData = (await response.json().catch(() => null)) as {
        detail?: string | Array<{ msg?: string }> | { message?: string };
      } | null;
      throw {
        response: {
          status: response.status,
          data: responseData,
        },
        isAxiosError: true,
      };
    }
  }

  async function handleToggleVisibility(document: TaxReferenceDocument) {
    setActingDocumentId(document.id);
    setError(null);
    setSuccess(null);
    try {
      await sendMultipartDocumentUpdate(document, !document.is_active);
      setSuccess(
        document.is_active
          ? "Reference document hidden from the public calculator."
          : "Reference document shown on the public calculator.",
      );
      await loadDocuments();
    } catch (actionError: unknown) {
      setError(getApiErrorMessage(actionError));
    } finally {
      setActingDocumentId(null);
    }
  }

  async function handleDelete(document: TaxReferenceDocument) {
    const confirmed = window.confirm(`Delete "${document.title}"?`);
    if (!confirmed) {
      return;
    }

    setActingDocumentId(document.id);
    setError(null);
    setSuccess(null);
    try {
      const token = getAccessToken();
      const response = await fetch(
        `${apiClient.defaults.baseURL}/admin/tax-reference-documents/${document.id}`,
        {
          method: "DELETE",
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        },
      );
      if (!response.ok) {
        const responseData = (await response.json().catch(() => null)) as {
          detail?: string | Array<{ msg?: string }> | { message?: string };
        } | null;
        throw {
          response: {
            status: response.status,
            data: responseData,
          },
          isAxiosError: true,
        };
      }
      setSuccess("Reference document deleted.");
      await loadDocuments();
    } catch (actionError: unknown) {
      setError(getApiErrorMessage(actionError));
    } finally {
      setActingDocumentId(null);
    }
  }

  async function handleUpload() {
    if (!form.title.trim()) {
      setError("Enter a title.");
      return;
    }

    if (!form.issuedLabel.trim()) {
      setError("Enter an issued label.");
      return;
    }

    if (!selectedFile) {
      setError("Choose a PDF first.");
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);
    try {
      const payload = new FormData();
      payload.append("title", form.title);
      payload.append("issued_label", form.issuedLabel);
      payload.append("document_type", form.documentType);
      payload.append("description", form.description);
      payload.append("display_order", form.displayOrder);
      payload.append("is_active", String(form.isActive));
      payload.append("file", selectedFile);
      const token = getAccessToken();
      const response = await fetch(
        `${apiClient.defaults.baseURL}/admin/tax-reference-documents`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          body: payload,
        },
      );
      if (!response.ok) {
        const responseData = (await response.json().catch(() => null)) as {
          detail?: string | Array<{ msg?: string }> | { message?: string };
        } | null;
        throw {
          response: {
            status: response.status,
            data: responseData,
          },
          isAxiosError: true,
        };
      }
      setSuccess("Reference document uploaded.");
      setSelectedFile(null);
      setForm(defaultForm);
      if (inputRef.current) inputRef.current.value = "";
      await loadDocuments();
    } catch (uploadError: unknown) {
      setError(getApiErrorMessage(uploadError));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#050505] px-6 py-8 text-white">
      <div className="mx-auto max-w-7xl space-y-8">
        <div className="space-y-3">
          <p className="text-xs uppercase tracking-[0.35em] text-gray-500">
            Admin
          </p>
          <h1 className="text-3xl font-semibold tracking-tight">
            Reference Documents
          </h1>
          <p className="max-w-3xl text-sm text-gray-400">
            Upload the PDFs that power the public tax calculator reference
            panel. This is the admin-managed replacement for the old static-file
            setup.
          </p>
        </div>

        <section className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="rounded-3xl border border-white/10 bg-[#0d0d0d] p-6">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl border border-[#FE7743]/20 bg-[#FE7743]/10 p-3 text-[#FE7743]">
                <UploadCloud className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Upload PDF</h2>
                <p className="text-sm text-gray-400">
                  Add a new document to the public calculator.
                </p>
              </div>
            </div>

            <div className="mt-6 space-y-4">
              <div className="space-y-2">
                <label className="text-sm text-gray-300">Title</label>
                <input
                  value={form.title}
                  onChange={(event) =>
                    setForm({ ...form, title: event.target.value })
                  }
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"
                />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm text-gray-300">Issued Label</label>
                  <input
                    value={form.issuedLabel}
                    onChange={(event) =>
                      setForm({ ...form, issuedLabel: event.target.value })
                    }
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-gray-300">Document Type</label>
                  <input
                    value={form.documentType}
                    onChange={(event) =>
                      setForm({ ...form, documentType: event.target.value })
                    }
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"
                  />
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-[1fr_120px]">
                <div className="space-y-2">
                  <label className="text-sm text-gray-300">Description</label>
                  <textarea
                    value={form.description}
                    onChange={(event) =>
                      setForm({ ...form, description: event.target.value })
                    }
                    rows={3}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-gray-300">Order</label>
                  <input
                    value={form.displayOrder}
                    onChange={(event) =>
                      setForm({ ...form, displayOrder: event.target.value })
                    }
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none"
                  />
                </div>
              </div>
              <label className="flex items-center gap-3 text-sm text-gray-300">
                <input
                  type="checkbox"
                  checked={form.isActive}
                  onChange={(event) =>
                    setForm({ ...form, isActive: event.target.checked })
                  }
                />
                Active on public calculator
              </label>
              <div className="space-y-2">
                <label className="text-sm text-gray-300">PDF File</label>
                <input
                  ref={inputRef}
                  type="file"
                  accept="application/pdf"
                  onChange={(event) =>
                    setSelectedFile(event.target.files?.[0] ?? null)
                  }
                  className="w-full rounded-xl border border-dashed border-white/10 bg-white/5 px-4 py-3 text-white outline-none"
                />
              </div>
              <button
                type="button"
                onClick={handleUpload}
                disabled={uploading}
                className="inline-flex items-center gap-2 rounded-xl bg-[#FE7743] px-5 py-3 font-semibold text-black disabled:opacity-60"
              >
                <UploadCloud className="h-4 w-4" />
                {uploading ? "Uploading..." : "Upload Document"}
              </button>
              {error ? <p className="text-sm text-red-300">{error}</p> : null}
              {success ? (
                <p className="text-sm text-emerald-300">{success}</p>
              ) : null}
            </div>
          </div>

          <div className="rounded-3xl border border-white/10 bg-[#0d0d0d] p-6">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-white">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">
                  Uploaded Documents
                </h2>
                <p className="text-sm text-gray-400">
                  These are what the public tax calculator will render.
                </p>
              </div>
            </div>

            <div className="mt-6 space-y-3">
              {loading ? (
                <div className="text-sm text-gray-400">Loading...</div>
              ) : null}
              {!loading && documents.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-white/10 bg-[#111] p-6 text-sm text-gray-400">
                  No reference documents uploaded yet.
                </div>
              ) : null}
              {documents.map((document) => (
                <div
                  key={document.id}
                  className="rounded-2xl border border-white/10 bg-[#121212] p-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <div className="text-sm font-semibold text-white">
                          {document.title}
                        </div>
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.18em] ${document.is_active ? "bg-emerald-500/10 text-emerald-300" : "bg-white/10 text-gray-400"}`}
                        >
                          {document.is_active ? "Shown" : "Hidden"}
                        </span>
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        {document.issued_label}
                      </div>
                      <div className="mt-2 text-xs text-gray-400">
                        {document.file_name}
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleToggleVisibility(document)}
                        disabled={actingDocumentId === document.id}
                        className="rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-white hover:bg-white/5 disabled:opacity-60"
                      >
                        {actingDocumentId === document.id
                          ? "Saving..."
                          : document.is_active
                            ? "Hide"
                            : "Show"}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(document)}
                        disabled={actingDocumentId === document.id}
                        className="rounded-lg border border-rose-500/20 px-3 py-2 text-xs font-medium text-rose-300 hover:bg-rose-500/10 disabled:opacity-60"
                      >
                        Delete
                      </button>
                      <a
                        href={document.file_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-2 text-sm text-[#FE7743] hover:text-orange-200"
                      >
                        View
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
