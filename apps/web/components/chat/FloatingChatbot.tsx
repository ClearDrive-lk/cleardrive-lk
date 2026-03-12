"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { useQueries } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import { useAppSelector } from "@/lib/store/store";
import { mapBackendVehicle } from "@/lib/vehicle-mapper";
import { Vehicle } from "@/types/vehicle";
import { VehicleCard } from "@/components/vehicles/VehicleCard";
import { MessageCircle, Send, Sparkles, X } from "lucide-react";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  role: ChatRole;
  content: string;
  vehicleIds?: string[];
  suggestedAction?: string | null;
};

type ChatApiResponse = {
  message: string;
  vehicle_ids: string[];
  suggested_action?: string | null;
};

const STARTER_PROMPTS = [
  "Find me a hybrid SUV",
  "Best family car under JPY 2,000,000",
  "Show practical city cars",
];

function buildHistory(messages: ChatMessage[]) {
  return messages.map((message) => ({
    role: message.role,
    content: message.content,
  }));
}

export default function FloatingChatbot() {
  const pathname = usePathname();
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "I can help you shortlist vehicles by budget, body type, and general preferences. I do not handle documents or tax calculations.",
    },
  ]);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const vehicleIds = useMemo(() => {
    const ids = new Set<string>();
    messages.forEach((message) => {
      message.vehicleIds?.forEach((vehicleId) => ids.add(vehicleId));
    });
    return Array.from(ids);
  }, [messages]);

  const vehicleQueries = useQueries({
    queries: vehicleIds.map((vehicleId) => ({
      queryKey: ["chat-vehicle", vehicleId],
      queryFn: async () => {
        const response = await apiClient.get(`/vehicles/${vehicleId}`);
        return mapBackendVehicle(response.data);
      },
      enabled: isOpen,
      staleTime: 1000 * 60 * 2,
    })),
  });

  const vehicleLookup = useMemo(() => {
    const lookup = new Map<string, Vehicle>();
    vehicleIds.forEach((vehicleId, index) => {
      const vehicle = vehicleQueries[index]?.data;
      if (vehicle) {
        lookup.set(vehicleId, vehicle);
      }
    });
    return lookup;
  }, [vehicleIds, vehicleQueries]);

  const isHiddenRoute = useMemo(() => {
    return (
      pathname.startsWith("/admin") ||
      pathname.startsWith("/login") ||
      pathname.startsWith("/register") ||
      pathname.startsWith("/verify-otp") ||
      pathname.startsWith("/forgot-password")
    );
  }, [pathname]);

  useEffect(() => {
    if (!scrollRef.current) {
      return;
    }
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isOpen]);

  if (!isAuthenticated || isHiddenRoute) {
    return null;
  }

  async function sendMessage(rawMessage?: string) {
    const message = (rawMessage ?? input).trim();
    if (!message || isSending) {
      return;
    }

    const nextMessages: ChatMessage[] = [
      ...messages,
      {
        role: "user",
        content: message,
      },
    ];

    setMessages(nextMessages);
    setInput("");
    setError(null);
    setIsSending(true);

    try {
      const { data } = await apiClient.post<ChatApiResponse>("/chat/message", {
        message,
        conversation_history: buildHistory(nextMessages).slice(-10),
      });

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.message,
          vehicleIds: data.vehicle_ids,
          suggestedAction: data.suggested_action ?? null,
        },
      ]);
    } catch (requestError: unknown) {
      const status = (requestError as { response?: { status?: number } })
        .response?.status;
      if (status === 429) {
        setError("Too many messages. Wait a minute and try again.");
      } else {
        setError("The vehicle assistant is unavailable right now.");
      }
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="fixed bottom-5 right-5 z-[70]">
      {isOpen ? (
        <div className="w-[min(24rem,calc(100vw-1.5rem))] overflow-hidden rounded-[1.5rem] border border-white/10 bg-[#0a0a0a]/95 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl">
          <div className="relative overflow-hidden border-b border-white/10 bg-[radial-gradient(circle_at_top_left,rgba(254,119,67,0.22),transparent_45%),linear-gradient(135deg,rgba(255,255,255,0.06),rgba(255,255,255,0.01))] p-4">
            <div className="absolute right-0 top-0 h-20 w-20 rounded-full bg-[#FE7743]/10 blur-2xl" />
            <div className="relative flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.28em] text-[#FE7743]">
                  <Sparkles className="h-3.5 w-3.5" />
                  Vehicle Assistant
                </div>
                <p className="mt-2 max-w-[16rem] text-sm text-gray-300">
                  Ask about vehicle types, budget, or preferences. Tax and
                  document questions are intentionally blocked.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="rounded-full border border-white/10 bg-white/5 p-2 text-gray-300 transition hover:bg-white/10 hover:text-white"
                aria-label="Close chat"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div
            ref={scrollRef}
            className="max-h-[24rem] space-y-3 overflow-y-auto p-4"
          >
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div className="max-w-[85%] space-y-3">
                  <div
                    className={`rounded-2xl px-4 py-3 text-sm leading-6 ${
                      message.role === "user"
                        ? "bg-[#FE7743] text-black"
                        : "border border-white/10 bg-white/5 text-gray-100"
                    }`}
                  >
                    <p>{message.content}</p>
                    {message.suggestedAction === "open_tax_calculator" ? (
                      <Link
                        href={
                          message.vehicleIds?.length
                            ? `/dashboard/vehicles/${message.vehicleIds[0]}#cost-calculator`
                            : "/dashboard/vehicles"
                        }
                        className="mt-3 inline-flex rounded-full border border-[#FE7743]/30 bg-[#FE7743]/10 px-3 py-1 text-xs font-medium text-[#FE7743] transition hover:bg-[#FE7743]/15"
                      >
                        Calculate Tax
                      </Link>
                    ) : null}
                  </div>

                  {message.vehicleIds?.length ? (
                    <div className="space-y-3">
                      {message.vehicleIds.map((vehicleId) => {
                        const vehicle = vehicleLookup.get(vehicleId);
                        if (!vehicle) {
                          return (
                            <div
                              key={vehicleId}
                              className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-xs text-gray-400"
                            >
                              Loading vehicle details...
                            </div>
                          );
                        }
                        return (
                          <div key={vehicleId} className="space-y-2">
                            <VehicleCard vehicle={vehicle} />
                            <Link
                              href={`/dashboard/vehicles/${vehicleId}#cost-calculator`}
                              className="inline-flex rounded-full border border-[#FE7743]/30 bg-[#FE7743]/10 px-3 py-1 text-xs font-medium text-[#FE7743] transition hover:bg-[#FE7743]/15"
                            >
                              Calculate Tax
                            </Link>
                          </div>
                        );
                      })}
                    </div>
                  ) : null}
                </div>
              </div>
            ))}
            {isSending ? (
              <div className="flex justify-start">
                <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-gray-400">
                  Thinking...
                </div>
              </div>
            ) : null}
          </div>

          <div className="border-t border-white/10 p-4">
            {messages.length === 1 ? (
              <div className="mb-3 flex flex-wrap gap-2">
                {STARTER_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => void sendMessage(prompt)}
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-gray-300 transition hover:border-[#FE7743]/30 hover:text-white"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            ) : null}

            {error ? (
              <p className="mb-3 text-xs text-red-300">{error}</p>
            ) : null}

            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void sendMessage();
                  }
                }}
                rows={1}
                maxLength={500}
                placeholder="Ask about family SUVs, hybrids, or budget..."
                className="min-h-11 flex-1 resize-none rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-gray-500 focus:border-[#FE7743]/40"
              />
              <button
                type="button"
                onClick={() => void sendMessage()}
                disabled={isSending || !input.trim()}
                className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-[#FE7743] text-black transition hover:bg-[#ff885a] disabled:cursor-not-allowed disabled:opacity-50"
                aria-label="Send message"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className="ml-auto flex h-16 w-16 items-center justify-center rounded-full border border-[#FE7743]/30 bg-[radial-gradient(circle_at_30%_30%,#ffb08f,#FE7743_55%,#a63f12)] text-black shadow-[0_20px_50px_rgba(254,119,67,0.35)] transition hover:scale-[1.03]"
        aria-label="Open vehicle assistant"
      >
        <MessageCircle className="h-7 w-7" />
      </button>
    </div>
  );
}
