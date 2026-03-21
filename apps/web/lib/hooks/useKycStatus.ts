"use client";

import { useEffect, useState } from "react";

import apiClient from "@/lib/api-client";

type KycStatusResponse = {
  has_kyc: boolean;
  status: string | null;
  submitted_at: string | null;
  reviewed_at: string | null;
  rejection_reason: string | null;
  nic_number: string | null;
  full_name: string | null;
};

export function useKycStatus(enabled = true) {
  const [status, setStatus] = useState<KycStatusResponse | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    const loadStatus = async () => {
      setLoading(true);
      setError(null);

      try {
        const { data } = await apiClient.get<KycStatusResponse>("/kyc/status");
        if (!cancelled) {
          setStatus(data);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : "Failed to load KYC status.";
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadStatus();

    return () => {
      cancelled = true;
    };
  }, [enabled]);

  const normalizedStatus = status?.status?.toUpperCase() ?? null;
  const isApproved = normalizedStatus === "APPROVED";

  return {
    status,
    loading,
    error,
    isApproved,
    normalizedStatus,
  };
}
