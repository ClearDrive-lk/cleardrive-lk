"use client";

import { useEffect, useState } from "react";
import { Download, ShieldCheck } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { getAccessToken, getRefreshToken } from "@/lib/auth";

interface ExportHistoryResponse {
  daily_limit: number;
  used_today: number;
  remaining_today: number;
}

export function GDPRDataExport() {
  const [loading, setLoading] = useState(false);
  const [quota, setQuota] = useState<ExportHistoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadQuota = async () => {
    try {
      const hasSession = Boolean(getAccessToken() || getRefreshToken());
      if (!hasSession) return;
      const res = await apiClient.get<ExportHistoryResponse>(
        "/gdpr/export/history",
      );
      setQuota(res.data);
    } catch (err) {
      setError("GDPR export service is unavailable right now.");
    }
  };

  useEffect(() => {
    void loadQuota();
  }, []);

  const exportData = async () => {
    if (quota?.remaining_today === 0) {
      setError("Daily export limit reached. Please try again tomorrow.");
      return;
    }

    const confirmed = window.confirm(
      "This will download all your personal data from ClearDrive. Continue?",
    );
    if (!confirmed) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const hasSession = Boolean(getAccessToken() || getRefreshToken());
      if (!hasSession) {
        setError("Please sign in again to export your data.");
        return;
      }
      const response = await apiClient.get("/gdpr/export", {
        responseType: "blob",
      });

      const contentDisposition = response.headers["content-disposition"] as
        | string
        | undefined;
      const filenameMatch = contentDisposition?.match(/filename="?(.+)"?/i);
      const filename = filenameMatch?.[1] ?? "cleardrive_data_export.json";

      const blob = new Blob([response.data], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      await loadQuota();
    } catch (err: unknown) {
      setError("Export failed. Please try again or contact support.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border border-[#546a7b]/65 bg-[#fdfdff] rounded-2xl p-6">
      <div className="flex items-start justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 text-xs font-mono text-[#62929e] mb-3">
            <ShieldCheck className="w-4 h-4" />
            GDPR DATA EXPORT
          </div>
          <h3 className="text-2xl font-bold text-[#393d3f] mb-2">
            Download Your Data
          </h3>
          <p className="text-sm text-[#546a7b] max-w-xl">
            Under GDPR Article 15, you can export all personal data stored in
            ClearDrive in a machine-readable JSON format.
          </p>
        </div>
      </div>

      {quota && (
        <div className="mt-4 text-xs font-mono text-[#546a7b]">
          Daily limit: {quota.used_today}/{quota.daily_limit} used -{" "}
          {quota.remaining_today} remaining today
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="mt-6">
        <Button
          onClick={exportData}
          disabled={loading || quota?.remaining_today === 0}
          className="bg-[#62929e] text-[#fdfdff] hover:bg-[#62929e]/90 font-bold gap-2"
        >
          <Download className="w-4 h-4" />
          {loading ? "Preparing Export..." : "Download My Data"}
        </Button>
      </div>
    </div>
  );
}
