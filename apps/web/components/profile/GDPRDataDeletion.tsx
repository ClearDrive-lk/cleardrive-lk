"use client";

import { useEffect, useState } from "react";
import apiClient from "@/lib/api-client";
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
  const [step, setStep] = useState<"initial" | "confirm">("initial");
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

      removeTokens();
      dispatch(logoutAction());
      window.location.href = "/";
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
    <div className="mt-12 border border-red-500/30 bg-red-950/20 p-6">
      <h3 className="text-xl font-bold text-red-300">
        Delete My Account (GDPR)
      </h3>
      <p className="mt-3 text-sm text-red-100/80">
        This action is permanent. Your personal data will be anonymized, KYC
        files removed, and all sessions revoked.
      </p>

      {blockers && blockers.can_delete === false && (
        <div className="mt-4 border border-yellow-500/40 bg-yellow-950/30 p-3 text-sm text-yellow-200">
          Deletion blocked: {blockers.reason}
        </div>
      )}

      {step === "initial" && (
        <button
          onClick={() => setStep("confirm")}
          disabled={Boolean(blockers && blockers.can_delete === false)}
          className="mt-5 border border-red-400/40 bg-red-600/80 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          Proceed to Delete Account
        </button>
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
            className="w-full border border-white/20 bg-black/30 px-3 py-2 font-mono text-sm text-white"
            placeholder="DELETE MY ACCOUNT"
          />
          {error && <p className="text-sm text-red-300">{error}</p>}
          <div className="flex gap-2">
            <button
              onClick={() => {
                setStep("initial");
                setConfirmation("");
                setError(null);
              }}
              disabled={loading}
              className="border border-white/20 px-4 py-2 text-sm text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              disabled={loading || confirmation !== "DELETE MY ACCOUNT"}
              className="border border-red-400/40 bg-red-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Deleting..." : "Delete My Account Forever"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
