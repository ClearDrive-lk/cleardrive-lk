"use client";

import { isAxiosError } from "axios";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Loader2, Mail, ShieldCheck } from "lucide-react";
import { getAccessToken } from "@/lib/auth";
import apiClient from "@/lib/api-client";
import { useToast } from "@/lib/hooks/use-toast";
import { useAppSelector } from "@/lib/store/store";

function PaymentForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [otpRequested, setOtpRequested] = useState(false);
  const [otpRequestLoading, setOtpRequestLoading] = useState(false);
  const [otpVerifying, setOtpVerifying] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSeconds, setResendSeconds] = useState(0);
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const { toast } = useToast();
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const email = useAppSelector((state) => state.auth.user?.email);

  const orderId = searchParams.get("orderId");
  const otpCode = useMemo(() => otp.join(""), [otp]);

  useEffect(() => {
    const handlePopState = () => {
      window.history.pushState(null, "", window.location.href);
    };
    window.history.pushState(null, "", window.location.href);
    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  useEffect(() => {
    if (resendSeconds <= 0) return;
    const timer = window.setInterval(() => {
      setResendSeconds((prev) => (prev <= 1 ? 0 : prev - 1));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [resendSeconds]);

  const getPaymentIdempotencyKey = (currentOrderId: string): string => {
    const storageKey = `payment:idempotency:${currentOrderId}`;
    const existing = sessionStorage.getItem(storageKey);
    if (existing) return existing;

    const generated = crypto.randomUUID();
    sessionStorage.setItem(storageKey, generated);
    return generated;
  };

  const redirectToPayHere = (
    paymentUrl: string,
    payhereParams: Record<string, string>,
  ) => {
    toast({
      title: "Redirecting to PayHere",
      description: "Complete payment to continue your order.",
    });
    const form = document.createElement("form");
    form.method = "POST";
    form.action = paymentUrl;
    Object.keys(payhereParams).forEach((key) => {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = key;
      input.value = payhereParams[key];
      form.appendChild(input);
    });
    document.body.appendChild(form);
    form.submit();
  };

  const initiatePayment = async () => {
    if (!orderId) {
      setError("Order ID is required");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error("Please log in to continue payment");
      }
      const idempotencyKey = getPaymentIdempotencyKey(orderId);

      const { data } = await apiClient.post(
        "/payments/initiate",
        {
          order_id: orderId,
          idempotency_key: idempotencyKey,
        },
        {
          headers: {
            "Idempotency-Key": idempotencyKey,
            Authorization: `Bearer ${token}`,
          },
        },
      );

      const { payment_url, payhere_params } = data as {
        payment_url: string;
        payhere_params: Record<string, string>;
      };

      redirectToPayHere(payment_url, payhere_params);
    } catch (err) {
      const message = isAxiosError(err)
        ? (
            err.response?.data as
              | { detail?: string; message?: string }
              | undefined
          )?.detail ||
          (
            err.response?.data as
              | { detail?: string; message?: string }
              | undefined
          )?.message ||
          err.message ||
          "Payment failed. Please try again."
        : err instanceof Error
          ? err.message
          : "Payment failed. Please try again.";
      setError(message);
      toast({
        title: "Payment failed",
        description: message,
        variant: "destructive",
      });
      setLoading(false);
    }
  };

  const requestOtp = async (resend = false) => {
    if (!orderId) {
      setError("Order ID is required");
      return;
    }

    if (resend) {
      setResendLoading(true);
    } else {
      setOtpRequestLoading(true);
    }
    setError(null);
    setStatusMessage(null);

    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error("Please log in to continue payment");
      }

      await apiClient.post(
        "/payments/request-otp",
        { order_id: orderId },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );
      setOtpRequested(true);
      setOtp(["", "", "", "", "", ""]);
      setResendSeconds(30);
      setStatusMessage(
        resend
          ? "A new payment OTP has been sent to your email."
          : "A payment OTP has been sent to your email.",
      );
      inputRefs.current[0]?.focus();
    } catch (err) {
      const message = isAxiosError(err)
        ? (
            err.response?.data as
              | { detail?: string; message?: string }
              | undefined
          )?.detail ||
          (
            err.response?.data as
              | { detail?: string; message?: string }
              | undefined
          )?.message ||
          err.message ||
          "Failed to send payment OTP."
        : err instanceof Error
          ? err.message
          : "Failed to send payment OTP.";
      setError(message);
    } finally {
      setOtpRequestLoading(false);
      setResendLoading(false);
    }
  };

  const verifyOtpAndPay = async () => {
    if (!orderId || otpCode.length !== 6) return;

    setOtpVerifying(true);
    setError(null);
    setStatusMessage(null);

    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error("Please log in to continue payment");
      }

      await apiClient.post(
        "/payments/verify-otp",
        { order_id: orderId, otp: otpCode },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );
      setStatusMessage("Payment OTP verified. Redirecting to PayHere...");
      await initiatePayment();
    } catch (err) {
      const message = isAxiosError(err)
        ? (
            err.response?.data as
              | { detail?: string; message?: string }
              | undefined
          )?.detail ||
          (
            err.response?.data as
              | { detail?: string; message?: string }
              | undefined
          )?.message ||
          err.message ||
          "Payment OTP verification failed."
        : err instanceof Error
          ? err.message
          : "Payment OTP verification failed.";
      setError(message);
    } finally {
      setOtpVerifying(false);
    }
  };

  const handleChange = (index: number, value: string) => {
    if (!/^\d?$/.test(value)) return;
    const nextOtp = [...otp];
    nextOtp[index] = value;
    setOtp(nextOtp);
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (
    index: number,
    e: React.KeyboardEvent<HTMLInputElement>,
  ) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (
    index: number,
    e: React.ClipboardEvent<HTMLInputElement>,
  ) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "");
    if (!pasted) return;

    const nextOtp = [...otp];
    let cursor = index;
    for (const digit of pasted) {
      if (cursor > 5) break;
      nextOtp[cursor] = digit;
      cursor += 1;
    }
    setOtp(nextOtp);
    inputRefs.current[Math.min(cursor, 5)]?.focus();
  };

  if (!orderId) {
    return (
      <Card className="max-w-md mx-auto bg-slate-900 border-slate-700">
        <CardHeader>
          <CardTitle className="text-[#393d3f]">Payment Error</CardTitle>
          <CardDescription>No order ID provided</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => router.push("/")} className="w-full">
            Return to Home
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="max-w-md mx-auto bg-slate-900 border-slate-800 shadow-2xl">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl text-[#393d3f]">
          Verify and Pay
        </CardTitle>
        <CardDescription className="text-slate-400">
          Order ID: {orderId}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4 text-left">
          <div className="flex items-center gap-3 text-slate-100">
            <ShieldCheck className="h-5 w-5 text-blue-400" />
            <div>
              <p className="text-sm font-medium">Payment OTP required</p>
              <p className="text-xs text-slate-400">
                We&apos;ll send a 6-digit verification code to{" "}
                <span className="font-mono text-slate-300">
                  {email || "your account email"}
                </span>{" "}
                before opening PayHere.
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded text-sm">
            {error}
          </div>
        )}

        {statusMessage && (
          <div className="bg-emerald-500/10 border border-emerald-500/40 text-emerald-300 px-4 py-3 rounded text-sm">
            {statusMessage}
          </div>
        )}

        {!otpRequested ? (
          <Button
            onClick={() => void requestOtp()}
            disabled={otpRequestLoading}
            className="w-full bg-blue-600 hover:bg-blue-500 py-6 text-lg"
          >
            {otpRequestLoading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Sending OTP...
              </>
            ) : (
              <>
                <Mail className="mr-2 h-5 w-5" /> Send Payment OTP
              </>
            )}
          </Button>
        ) : (
          <>
            <div className="flex gap-2 justify-center">
              {otp.map((digit, index) => (
                <Input
                  key={index}
                  ref={(el) => {
                    inputRefs.current[index] = el;
                  }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  onPaste={(e) => handlePaste(index, e)}
                  className="h-12 w-12 border-slate-700 bg-slate-950 text-center text-lg font-mono text-slate-100"
                />
              ))}
            </div>

            <Button
              onClick={() => void verifyOtpAndPay()}
              disabled={loading || otpVerifying || otpCode.length !== 6}
              className="w-full bg-blue-600 hover:bg-blue-500 py-6 text-lg"
            >
              {loading || otpVerifying ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Verifying...
                </>
              ) : (
                "Verify OTP and Continue"
              )}
            </Button>

            <Button
              variant="ghost"
              onClick={() => void requestOtp(true)}
              disabled={
                resendLoading || resendSeconds > 0 || loading || otpVerifying
              }
              className="w-full text-slate-300 hover:bg-slate-800"
            >
              {resendLoading
                ? "Sending..."
                : resendSeconds > 0
                  ? `Resend OTP in ${resendSeconds}s`
                  : "Resend OTP"}
            </Button>
          </>
        )}

        <Button
          variant="outline"
          onClick={() => router.back()}
          className="w-full border-slate-700 text-slate-300 hover:bg-slate-800"
          disabled={
            loading || otpVerifying || otpRequestLoading || resendLoading
          }
        >
          Cancel
        </Button>
      </CardContent>
    </Card>
  );
}

export default function PaymentPage() {
  return (
    <div className="min-h-screen bg-[#fdfdff] flex items-center justify-center p-4">
      <Suspense
        fallback={<div className="text-[#393d3f]">Loading payment...</div>}
      >
        <PaymentForm />
      </Suspense>
    </div>
  );
}
