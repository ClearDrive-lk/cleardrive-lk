"use client";

import { useEffect, useState } from "react";
import AuthGuard from "@/components/auth/AuthGuard";
import Link from "next/link";
import { isAxiosError } from "axios";
import {
  Terminal,
  ShieldCheck,
  Upload,
  FileImage,
  AlertTriangle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { useLogout } from "@/lib/hooks/useLogout";

interface KycStatusResponse {
  has_kyc: boolean;
  status: string | null;
  submitted_at: string | null;
  reviewed_at: string | null;
  rejection_reason: string | null;
  nic_number: string | null;
  full_name: string | null;
}

interface KycUploadResponse {
  id: string;
  user_id: string;
  nic_number: string | null;
  full_name: string | null;
  date_of_birth: string | null;
  address: string | null;
  gender: string | null;
  status: string;
  nic_front_url: string;
  nic_back_url: string;
  selfie_url: string;
  user_provided_data?: Record<string, string | null>;
  extracted_data?: Record<string, unknown>;
  created_at: string;
}

const initialForm = {
  nic_number: "",
  full_name: "",
  date_of_birth: "",
  address: "",
  gender: "",
};

export default function DashboardKycPage() {
  const { logout, isLoading: logoutLoading } = useLogout();
  const [status, setStatus] = useState<KycStatusResponse | null>(null);
  const [documents, setDocuments] = useState<KycUploadResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [form, setForm] = useState(initialForm);
  const [files, setFiles] = useState<{
    nic_front: File | null;
    nic_back: File | null;
    selfie: File | null;
  }>({
    nic_front: null,
    nic_back: null,
    selfie: null,
  });

  useEffect(() => {
    const loadKyc = async () => {
      setLoading(true);
      setError(null);
      try {
        const [statusResponse, documentsResponse] = await Promise.allSettled([
          apiClient.get<KycStatusResponse>("/kyc/status"),
          apiClient.get<KycUploadResponse>("/kyc/my-documents"),
        ]);

        if (statusResponse.status === "fulfilled") {
          setStatus(statusResponse.value.data);
        }

        if (documentsResponse.status === "fulfilled") {
          setDocuments(documentsResponse.value.data);
          setForm({
            nic_number:
              documentsResponse.value.data.user_provided_data?.nic_number ?? "",
            full_name:
              documentsResponse.value.data.user_provided_data?.full_name ?? "",
            date_of_birth:
              documentsResponse.value.data.user_provided_data?.date_of_birth ??
              "",
            address:
              documentsResponse.value.data.user_provided_data?.address ?? "",
            gender:
              documentsResponse.value.data.user_provided_data?.gender ?? "",
          });
        }
      } catch {
        setError("Failed to load your KYC data.");
      } finally {
        setLoading(false);
      }
    };

    void loadKyc();
  }, []);

  const handleUpload = async () => {
    if (!files.nic_front || !files.nic_back || !files.selfie) {
      setError("Upload NIC front, NIC back, and a selfie.");
      return;
    }
    if (
      !form.nic_number.trim() ||
      !form.full_name.trim() ||
      !form.date_of_birth.trim() ||
      !form.address.trim() ||
      !form.gender.trim()
    ) {
      setError("Complete all identity fields before submitting KYC.");
      return;
    }

    const payload = new FormData();
    payload.append("nic_front", files.nic_front);
    payload.append("nic_back", files.nic_back);
    payload.append("selfie", files.selfie);
    payload.append("nic_number", form.nic_number.trim());
    payload.append("full_name", form.full_name.trim());
    payload.append("date_of_birth", form.date_of_birth);
    payload.append("address", form.address.trim());
    payload.append("gender", form.gender.trim());

    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      await apiClient.post("/kyc/upload", payload, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setSuccess("KYC submitted successfully.");
      const [statusResponse, documentsResponse] = await Promise.all([
        apiClient.get<KycStatusResponse>("/kyc/status"),
        apiClient.get<KycUploadResponse>("/kyc/my-documents"),
      ]);
      setStatus(statusResponse.data);
      setDocuments(documentsResponse.data);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to submit KYC.",
        );
      } else {
        setError("Failed to submit KYC.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const statusBadge = (() => {
    switch (status?.status) {
      case "APPROVED":
        return {
          label: "Approved",
          className: "bg-emerald-100 text-emerald-800",
        };
      case "REJECTED":
        return { label: "Rejected", className: "bg-red-100 text-red-800" };
      case "PENDING_MANUAL_REVIEW":
        return {
          label: "Pending Manual Review",
          className: "bg-amber-100 text-amber-800",
        };
      case "PENDING":
        return {
          label: "Pending Review",
          className: "bg-sky-100 text-sky-800",
        };
      default:
        return {
          label: "Not Submitted",
          className: "bg-slate-200 text-slate-700",
        };
    }
  })();

  return (
    <AuthGuard>
      <div className="min-h-screen bg-[#fdfdff] text-[#393d3f] selection:bg-[#62929e] selection:text-[#fdfdff] font-sans flex flex-col">
        <nav className="border-b border-[#546a7b]/65 bg-[#fdfdff]/80 backdrop-blur-md sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <Link
              href="/"
              className="font-bold text-xl tracking-tighter flex items-center gap-2"
            >
              <div className="w-8 h-8 bg-[#62929e]/10 border border-[#62929e]/20 rounded-md flex items-center justify-center">
                <Terminal className="w-4 h-4 text-[#62929e]" />
              </div>
              ClearDrive<span className="text-[#62929e]">.lk</span>
            </Link>
            <div className="hidden md:flex gap-8 text-sm font-medium text-[#546a7b]">
              <Link
                href="/dashboard"
                className="hover:text-[#393d3f] transition-colors"
              >
                Dashboard
              </Link>
              <Link
                href="/dashboard/orders"
                className="hover:text-[#393d3f] transition-colors"
              >
                Orders
              </Link>
              <Link
                href="/dashboard/vehicles"
                className="hover:text-[#393d3f] transition-colors"
              >
                Vehicles
              </Link>
              <Link
                href="/dashboard/kyc"
                className="text-[#393d3f] transition-colors flex items-center gap-2"
              >
                KYC
                <Badge
                  variant="outline"
                  className="text-[10px] border-[#62929e]/20 text-[#62929e] h-4 px-1"
                >
                  ACTIVE
                </Badge>
              </Link>
              <Link
                href="/dashboard/profile"
                className="hover:text-[#393d3f] transition-colors"
              >
                Profile
              </Link>
            </div>
            <Button
              onClick={logout}
              disabled={logoutLoading}
              className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
            >
              {logoutLoading ? "Signing out..." : "Sign Out"}
            </Button>
          </div>
        </nav>

        <section className="relative pt-20 pb-20 px-6 overflow-hidden flex-1">
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#c6c5b912_1px,transparent_1px),linear-gradient(to_bottom,#c6c5b912_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
          <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-[#62929e]/5 rounded-[100%] blur-[120px] pointer-events-none" />

          <div className="relative z-10 max-w-6xl mx-auto space-y-6">
            <header className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6">
              <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-[#c6c5b9]/20 border border-[#546a7b]/65 text-xs font-mono text-[#62929e] mb-6">
                <ShieldCheck className="h-3.5 w-3.5" />
                KYC SUBMISSION TERMINAL
              </div>
              <h1 className="text-5xl md:text-7xl font-bold tracking-tighter leading-[0.9]">
                VERIFY YOUR{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#62929e] to-[#c6c5b9]">
                  IDENTITY.
                </span>
              </h1>
              <p className="mt-4 max-w-2xl text-lg text-[#546a7b]">
                Submit your NIC and selfie once. Your entered details will be
                matched against extracted document data during admin review.
              </p>
            </header>

            <section className="grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
                <p className="text-sm text-[#546a7b]">Current Status</p>
                <span
                  className={`mt-3 inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusBadge.className}`}
                >
                  {statusBadge.label}
                </span>
              </div>
              <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
                <p className="text-sm text-[#546a7b]">Submitted At</p>
                <p className="mt-3 text-sm font-medium text-[#393d3f]">
                  {status?.submitted_at
                    ? new Date(status.submitted_at).toLocaleString()
                    : "Not submitted"}
                </p>
              </div>
              <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
                <p className="text-sm text-[#546a7b]">Reviewed At</p>
                <p className="mt-3 text-sm font-medium text-[#393d3f]">
                  {status?.reviewed_at
                    ? new Date(status.reviewed_at).toLocaleString()
                    : "Pending"}
                </p>
              </div>
            </section>

            {status?.rejection_reason ? (
              <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-100">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="mt-0.5 h-4 w-4" />
                  <div>
                    <p className="font-semibold">KYC Rejection Reason</p>
                    <p className="mt-1 text-red-100/90">
                      {status.rejection_reason}
                    </p>
                  </div>
                </div>
              </div>
            ) : null}

            <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
              <section className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6">
                <h2 className="text-2xl font-semibold text-[#393d3f]">
                  Submit KYC
                </h2>
                <p className="mt-2 text-sm text-[#546a7b]">
                  Upload clear images and provide the identity details exactly
                  as they appear on your NIC.
                </p>

                <div className="mt-6 grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-[#546a7b]">
                      NIC Number
                    </label>
                    <input
                      value={form.nic_number}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          nic_number: event.target.value,
                        }))
                      }
                      className="w-full rounded-2xl border border-[#546a7b]/65 bg-[#fdfdff]/30 px-4 py-3 text-sm text-[#393d3f]"
                      disabled={Boolean(status?.has_kyc)}
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-[#546a7b]">
                      Full Name
                    </label>
                    <input
                      value={form.full_name}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          full_name: event.target.value,
                        }))
                      }
                      className="w-full rounded-2xl border border-[#546a7b]/65 bg-[#fdfdff]/30 px-4 py-3 text-sm text-[#393d3f]"
                      disabled={Boolean(status?.has_kyc)}
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-[#546a7b]">
                      Date of Birth
                    </label>
                    <input
                      type="date"
                      value={form.date_of_birth}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          date_of_birth: event.target.value,
                        }))
                      }
                      className="w-full rounded-2xl border border-[#546a7b]/65 bg-[#fdfdff]/30 px-4 py-3 text-sm text-[#393d3f]"
                      disabled={Boolean(status?.has_kyc)}
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-[#546a7b]">
                      Gender
                    </label>
                    <input
                      value={form.gender}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          gender: event.target.value,
                        }))
                      }
                      className="w-full rounded-2xl border border-[#546a7b]/65 bg-[#fdfdff]/30 px-4 py-3 text-sm text-[#393d3f]"
                      disabled={Boolean(status?.has_kyc)}
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="mb-2 block text-sm font-medium text-[#546a7b]">
                      Address
                    </label>
                    <textarea
                      rows={3}
                      value={form.address}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          address: event.target.value,
                        }))
                      }
                      className="w-full rounded-2xl border border-[#546a7b]/65 bg-[#fdfdff]/30 px-4 py-3 text-sm text-[#393d3f]"
                      disabled={Boolean(status?.has_kyc)}
                    />
                  </div>
                </div>

                <div className="mt-6 grid gap-4 md:grid-cols-3">
                  {(
                    [
                      ["nic_front", "NIC Front"],
                      ["nic_back", "NIC Back"],
                      ["selfie", "Selfie"],
                    ] as const
                  ).map(([key, label]) => (
                    <label
                      key={key}
                      className="rounded-2xl border border-dashed border-[#546a7b]/50 bg-[#c6c5b9]/40 p-4"
                    >
                      <div className="flex items-center gap-2 text-sm font-medium text-[#393d3f]">
                        <FileImage className="h-4 w-4 text-[#62929e]" />
                        {label}
                      </div>
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        className="mt-4 block w-full text-xs text-[#546a7b]"
                        disabled={Boolean(status?.has_kyc)}
                        onChange={(event) =>
                          setFiles((current) => ({
                            ...current,
                            [key]: event.target.files?.[0] ?? null,
                          }))
                        }
                      />
                      <p className="mt-2 text-xs text-[#546a7b]">
                        {files[key]?.name ?? "No file selected"}
                      </p>
                    </label>
                  ))}
                </div>

                {error ? (
                  <div className="mt-5 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
                    {error}
                  </div>
                ) : null}
                {success ? (
                  <div className="mt-5 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                    {success}
                  </div>
                ) : null}

                <div className="mt-6">
                  <Button
                    onClick={handleUpload}
                    disabled={submitting || Boolean(status?.has_kyc)}
                    className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold"
                  >
                    <Upload className="mr-2 h-4 w-4" />
                    {submitting
                      ? "Submitting..."
                      : status?.has_kyc
                        ? "Already Submitted"
                        : "Submit KYC"}
                  </Button>
                </div>
              </section>

              <section className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6">
                <h2 className="text-2xl font-semibold text-[#393d3f]">
                  Submission Snapshot
                </h2>
                <p className="mt-2 text-sm text-[#546a7b]">
                  Review the last submitted identity data and uploaded document
                  links.
                </p>

                {loading ? (
                  <p className="mt-6 text-sm text-[#546a7b]">
                    Loading KYC data...
                  </p>
                ) : documents ? (
                  <div className="mt-6 space-y-4">
                    <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/40 p-4 text-sm">
                      <p className="text-[#546a7b]">Submitted Identity</p>
                      <div className="mt-3 space-y-2 text-[#393d3f]">
                        <p>
                          NIC:{" "}
                          {documents.user_provided_data?.nic_number ??
                            documents.nic_number ??
                            "N/A"}
                        </p>
                        <p>
                          Name:{" "}
                          {documents.user_provided_data?.full_name ??
                            documents.full_name ??
                            "N/A"}
                        </p>
                        <p>
                          DOB:{" "}
                          {documents.user_provided_data?.date_of_birth ??
                            documents.date_of_birth ??
                            "N/A"}
                        </p>
                        <p>
                          Gender:{" "}
                          {documents.user_provided_data?.gender ??
                            documents.gender ??
                            "N/A"}
                        </p>
                        <p>
                          Address:{" "}
                          {documents.user_provided_data?.address ??
                            documents.address ??
                            "N/A"}
                        </p>
                      </div>
                    </div>
                    <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/40 p-4 text-sm">
                      <p className="text-[#546a7b]">Uploaded Files</p>
                      <div className="mt-3 space-y-2">
                        <a
                          href={documents.nic_front_url}
                          target="_blank"
                          className="block text-[#62929e] hover:underline"
                          rel="noreferrer"
                        >
                          NIC Front
                        </a>
                        <a
                          href={documents.nic_back_url}
                          target="_blank"
                          className="block text-[#62929e] hover:underline"
                          rel="noreferrer"
                        >
                          NIC Back
                        </a>
                        <a
                          href={documents.selfie_url}
                          target="_blank"
                          className="block text-[#62929e] hover:underline"
                          rel="noreferrer"
                        >
                          Selfie
                        </a>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="mt-6 text-sm text-[#546a7b]">
                    No KYC submission found yet. Complete the form to start
                    verification.
                  </p>
                )}
              </section>
            </div>
          </div>
        </section>
      </div>
    </AuthGuard>
  );
}

