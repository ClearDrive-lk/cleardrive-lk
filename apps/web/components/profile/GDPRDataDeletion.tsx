"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, ShieldAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { removeTokens } from "@/lib/auth";
import { logout as logoutAction } from "@/lib/store/features/auth/authSlice";
import { useAppDispatch } from "@/lib/store/store";

type DeletionCheckResponse = {
  can_delete: boolean;
  blocked?: boolean;
  reason?: string;
  message?: string;
};

export default function GDPRDataDeletion() {
  const dispatch = useAppDispatch();
  const [step, setStep] = useState<"initial" | "confirm" | "done">("initial");
  const [confirmation, setConfirmation] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [blockers, setBlockers] = useState<DeletionCheckResponse | null>(null);

  useEffect(() => {
    const run = async () => {
      try {
        const { data } = await apiClient.get<DeletionCheckResponse>(
          "/gdpr/deletion-check",
        );
        setBlockers(data);
      } catch {
        setBlockers({
          can_delete: false,
          blocked: true,
          reason: "Could not validate deletion eligibility right now.",
        });
      }
    };
    void run();
  }, []);

  const handleDelete = async () => {
    if (confirmation !== "DELETE MY ACCOUNT") {
      setError("Please type exactly: DELETE MY ACCOUNT");
      return;
    }

    const accepted = window.confirm(
      "Final warning: this permanently deletes your account data and cannot be undone.",
    );
    if (!accepted) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await apiClient.delete("/gdpr/delete", {
        params: { confirmation },
      });

      setStep("done");

      window.setTimeout(() => {
        removeTokens();
        dispatch(logoutAction());
        window.location.href = "/";
      }, 1800);
    } catch (err: unknown) {
      if (
        typeof err === "object" &&
        err !== null &&
        "response" in err &&
        typeof (err as { response?: { data?: { detail?: string } } }).response
          ?.data?.detail === "string"
      ) {
        setError(
          (err as { response: { data: { detail: string } } }).response.data
            .detail,
        );
      } else {
        setError("Failed to delete account.");
      }
      setLoading(false);
    }
  };

  return (
    <div className="rounded-3xl border border-red-500/25 bg-red-950/15 p-6">
      <div className="flex items-start gap-3">
        <div className="rounded-full border border-red-500/30 bg-red-500/10 p-2 text-red-300">
          <ShieldAlert className="h-4 w-4" />
        </div>
        <div>
          <h3 className="text-xl font-semibold text-red-200">
            Delete My Account
          </h3>
          <p className="mt-2 text-sm text-red-100/80">
            This permanently anonymizes your personal data, removes stored KYC
            files, and revokes all sessions.
          </p>
        </div>
      </div>

      {blockers && blockers.can_delete === false && (
        <div className="mt-4 flex items-start gap-2 rounded-2xl border border-yellow-500/35 bg-yellow-950/30 p-3 text-sm text-yellow-200">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>Deletion blocked: {blockers.reason}</span>
        </div>
      )}

      {step === "initial" && (
        <Button
          onClick={() => setStep("confirm")}
          disabled={Boolean(blockers && blockers.can_delete === false)}
          className="mt-5 bg-red-600 text-white hover:bg-red-500"
        >
          Proceed to Delete Account
        </Button>
      )}

      {step === "confirm" && (
        <div className="mt-5 space-y-3">
          <p className="text-sm text-white">
            Type{" "}
            <code className="rounded bg-black/30 px-1 py-0.5">
              DELETE MY ACCOUNT
            </code>{" "}
            to confirm:
          </p>
          <input
            type="text"
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            className="w-full rounded-2xl border border-white/20 bg-black/30 px-3 py-2 font-mono text-sm text-white"
            placeholder="DELETE MY ACCOUNT"
          />
          {error && <p className="text-sm text-red-300">{error}</p>}
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setStep("initial");
                setConfirmation("");
                setError(null);
              }}
              disabled={loading}
              className="border-white/20 text-white hover:bg-white/5"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleDelete}
              disabled={loading || confirmation !== "DELETE MY ACCOUNT"}
              className="bg-red-600 text-white hover:bg-red-500 disabled:opacity-50"
            >
              {loading ? "Deleting..." : "Delete My Account Forever"}
            </Button>
          </div>
        </div>
      )}

      {step === "done" && (
        <div className="mt-5 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">
          Your deletion request has been processed. You are being signed out.
        </div>
      )}
    </div>
  );
}
