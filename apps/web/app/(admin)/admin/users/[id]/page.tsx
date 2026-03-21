"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { isAxiosError } from "axios";
import { ArrowLeft, Mail, Phone } from "lucide-react";

import { apiClient } from "@/lib/api-client";
import Footer from "@/components/layout/Footer";

interface AdminUserDetail {
  id: string;
  email: string;
  name: string;
  phone: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
  deleted_at: string | null;
  kyc_status: string | null;
  kyc_submitted_at: string | null;
  kyc_reviewed_at: string | null;
  kyc_rejection_reason: string | null;
  total_orders: number;
  active_orders: number;
  delivered_orders: number;
  cancelled_orders: number;
  last_order_at: string | null;
}

function formatDate(value: string | null) {
  if (!value) return "N/A";
  return new Date(value).toLocaleString();
}

function roleBadgeClass(role: string) {
  const map: Record<string, string> = {
    CUSTOMER:
      "border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-200",
    ADMIN: "border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-200",
    EXPORTER:
      "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
    CLEARING_AGENT:
      "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-200",
    FINANCE_PARTNER:
      "border-purple-500/30 bg-purple-500/10 text-purple-700 dark:text-purple-200",
  };

  return map[role] ?? "border-[#546a7b]/65 bg-[#c6c5b9]/30 text-[#393d3f]";
}

function kycBadgeClass(status: string | null) {
  if (!status) return "border-[#546a7b]/65 bg-[#c6c5b9]/30 text-[#393d3f]";
  if (status === "APPROVED") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200";
  }
  if (status === "REJECTED") {
    return "border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-200";
  }
  return "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-200";
}

export default function AdminUserDetailPage() {
  const params = useParams<{ id: string }>();
  const userId = params.id;

  const [detail, setDetail] = useState<AdminUserDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadUser = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<AdminUserDetail>(
          `/admin/users/${userId}`,
        );
        setDetail(response.data);
      } catch (err: unknown) {
        if (isAxiosError(err)) {
          setError(
            (err.response?.data as { detail?: string } | undefined)?.detail ??
              "Failed to load user details.",
          );
        } else {
          setError("Failed to load user details.");
        }
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      void loadUser();
    }
  }, [userId]);

  const orderCompletionRate = useMemo(() => {
    if (!detail || detail.total_orders === 0) {
      return 0;
    }
    return Math.round((detail.delivered_orders / detail.total_orders) * 100);
  }, [detail]);

  if (loading) {
    return (
      <div className="cd-container py-6 text-[#546a7b]">
        Loading user profile...
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="cd-container py-6 space-y-4">
        <Link
          href="/admin/users"
          className="inline-flex items-center gap-2 rounded-xl border border-[#546a7b]/65 px-4 py-2 text-sm font-semibold text-[#393d3f] hover:bg-[#c6c5b9]/30"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Users
        </Link>
        <div className="rounded-2xl border border-red-500/35 bg-red-500/10 p-4 text-sm text-red-600 dark:text-red-300">
          {error ?? "User not found."}
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="cd-container space-y-6 py-6 text-[#393d3f]">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <Link
            href="/admin/users"
            className="inline-flex items-center gap-2 rounded-xl border border-[#546a7b]/65 px-4 py-2 text-sm font-semibold text-[#393d3f] hover:bg-[#c6c5b9]/30"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Users
          </Link>
          <span className="text-xs text-[#546a7b]">User ID: {detail.id}</span>
        </div>

        <header className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6 shadow-sm">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#62929e]">
                Admin User Overview
              </p>
              <h1 className="mt-2 text-3xl font-semibold text-[#393d3f]">
                {detail.name || "Unnamed User"}
              </h1>
              <div className="mt-3 space-y-2 text-sm text-[#546a7b]">
                <p className="inline-flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  {detail.email}
                </p>
                <p className="inline-flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  {detail.phone || "No phone provided"}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              <span
                className={`inline-flex items-center justify-center rounded-full border px-3 py-1 text-xs font-semibold ${roleBadgeClass(detail.role)}`}
              >
                {detail.role}
              </span>
              <span
                className={`inline-flex items-center justify-center rounded-full border px-3 py-1 text-xs font-semibold ${kycBadgeClass(detail.kyc_status)}`}
              >
                {detail.kyc_status || "KYC Not Submitted"}
              </span>
              <span className="inline-flex items-center justify-center rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-3 py-1 text-xs font-semibold text-[#393d3f]">
                {detail.is_active ? "Active Account" : "Inactive Account"}
              </span>
              <span className="inline-flex items-center justify-center rounded-full border border-[#546a7b]/65 bg-[#c6c5b9]/30 px-3 py-1 text-xs font-semibold text-[#393d3f]">
                Completion: {orderCompletionRate}%
              </span>
            </div>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
            <p className="text-sm text-[#546a7b]">Total Orders</p>
            <p className="mt-2 text-3xl font-semibold text-[#393d3f]">
              {detail.total_orders}
            </p>
          </div>
          <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
            <p className="text-sm text-[#546a7b]">Active Orders</p>
            <p className="mt-2 text-3xl font-semibold text-[#393d3f]">
              {detail.active_orders}
            </p>
          </div>
          <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
            <p className="text-sm text-[#546a7b]">Delivered</p>
            <p className="mt-2 text-3xl font-semibold text-[#393d3f]">
              {detail.delivered_orders}
            </p>
          </div>
          <div className="rounded-2xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-5">
            <p className="text-sm text-[#546a7b]">Cancelled</p>
            <p className="mt-2 text-3xl font-semibold text-[#393d3f]">
              {detail.cancelled_orders}
            </p>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <article className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-[#393d3f]">
              Account Timeline
            </h2>
            <div className="mt-4 space-y-3 text-sm">
              <p className="text-[#546a7b]">
                <span className="font-semibold text-[#393d3f]">Joined:</span>{" "}
                {formatDate(detail.created_at)}
              </p>
              <p className="text-[#546a7b]">
                <span className="font-semibold text-[#393d3f]">
                  Last Profile Update:
                </span>{" "}
                {formatDate(detail.updated_at)}
              </p>
              <p className="text-[#546a7b]">
                <span className="font-semibold text-[#393d3f]">
                  Last Login:
                </span>{" "}
                {formatDate(detail.last_login)}
              </p>
              <p className="text-[#546a7b]">
                <span className="font-semibold text-[#393d3f]">
                  Last Order:
                </span>{" "}
                {formatDate(detail.last_order_at)}
              </p>
              <p className="text-[#546a7b]">
                <span className="font-semibold text-[#393d3f]">
                  Account Deleted At:
                </span>{" "}
                {formatDate(detail.deleted_at)}
              </p>
            </div>
          </article>

          <article className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-[#393d3f]">
              KYC Summary
            </h2>
            <div className="mt-4 space-y-3 text-sm">
              <p className="text-[#546a7b]">
                <span className="font-semibold text-[#393d3f]">Status:</span>{" "}
                {detail.kyc_status || "Not Submitted"}
              </p>
              <p className="text-[#546a7b]">
                <span className="font-semibold text-[#393d3f]">Submitted:</span>{" "}
                {formatDate(detail.kyc_submitted_at)}
              </p>
              <p className="text-[#546a7b]">
                <span className="font-semibold text-[#393d3f]">Reviewed:</span>{" "}
                {formatDate(detail.kyc_reviewed_at)}
              </p>
              <p className="text-[#546a7b]">
                <span className="font-semibold text-[#393d3f]">
                  Rejection Reason:
                </span>{" "}
                {detail.kyc_rejection_reason || "N/A"}
              </p>
            </div>
          </article>
        </section>
      </div>
      <Footer />
    </>
  );
}
