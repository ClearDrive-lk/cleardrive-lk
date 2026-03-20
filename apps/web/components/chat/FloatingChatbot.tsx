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
import {
  Gauge,
  ListFilter,
  MessageCircle,
  RefreshCw,
  Send,
  Sparkles,
  X,
} from "lucide-react";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  role: ChatRole;
  content: string;
  vehicleIds?: string[];
  suggestedAction?: string | null;
  quickReplies?: string[];
};

type ChatApiResponse = {
  message: string;
  vehicle_ids: string[];
  suggested_action?: string | null;
};

const INITIAL_ASSISTANT_MESSAGE: ChatMessage = {
  role: "assistant",
  content:
    "I can shortlist vehicles by budget, body style, fuel type, and use case.\n" +
    "Share your priorities, and I will narrow options with clear trade-offs.\n" +
    "I do not handle tax or document questions in chat.",
  quickReplies: [
    "Find me a hybrid SUV",
    "Best family car under JPY 2,000,000",
    "Show practical city cars",
  ],
};

const DISCOVERY_PROMPTS = [
  {
    label: "Hybrid SUV",
    prompt: "Find me a hybrid SUV with low running cost",
  },
  {
    label: "Family 7-Seater",
    prompt: "Show 7-seater family vehicles under JPY 3,000,000",
  },
  {
    label: "City Commute",
    prompt: "Recommend compact city cars with good fuel economy",
  },
  {
    label: "Value Picks",
    prompt: "Give me the best value vehicles under JPY 2,000,000",
  },
];

function buildHistory(messages: ChatMessage[]) {
  return messages.map((message) => ({
    role: message.role,
    content: message.content,
  }));
}

function buildQuickReplies(message: string, hasVehicles: boolean): string[] {
  const lowered = message.toLowerCase();

  if (lowered.includes("tax calculator")) {
    return [
      "Show vehicles under JPY 2,000,000",
      "Hybrid options for family use",
      "City-friendly hatchbacks",
    ];
  }

  if (hasVehicles) {
    return [
      "Show cheaper options",
      "Only 2020 or newer",
      "Prioritize fuel efficiency",
      "Compare family comfort",
    ];
  }

  if (
    lowered.includes("could not find") ||
    lowered.includes("no vehicles") ||
    lowered.includes("no matching")
  ) {
    return [
      "SUV under JPY 2,000,000",
      "Hybrid sedan for city use",
      "Family vehicle with more space",
      "Low-maintenance daily driver",
    ];
  }

  return [
    "Recommend practical hybrids",
    "Best family SUV options",
    "Show compact city cars",
  ];
}

export default function FloatingChatbot() {
  const pathname = usePathname();
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    INITIAL_ASSISTANT_MESSAGE,
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

  function resetChat() {
    setMessages([INITIAL_ASSISTANT_MESSAGE]);
    setInput("");
    setError(null);
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

      const quickReplies = buildQuickReplies(
        data.message,
        Boolean(data.vehicle_ids?.length),
      );
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.message,
          vehicleIds: data.vehicle_ids,
          suggestedAction: data.suggested_action ?? null,
          quickReplies,
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
        <div className="w-[min(28rem,calc(100vw-1rem))] overflow-hidden rounded-[1.5rem] border border-[#5d7385]/70 bg-[#0c1116]/95 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl">
          <div className="relative overflow-hidden border-b border-[#5d7385]/70 bg-[radial-gradient(circle_at_top_left,rgba(98,146,158,0.28),transparent_45%),linear-gradient(135deg,rgba(255,255,255,0.08),rgba(255,255,255,0.01))] p-4">
            <div className="absolute right-0 top-0 h-20 w-20 rounded-full bg-[#62929e]/15 blur-2xl" />
            <div className="relative flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.28em] text-[#62929e]">
                  <Sparkles className="h-3.5 w-3.5" />
                  Vehicle Assistant
                </div>
                <p className="mt-1 text-xs text-[#9cb1be]">
                  Live inventory guidance
                </p>
                <p className="mt-2 max-w-[18rem] text-sm leading-6 text-[#d7e1e8]">
                  Tell me your budget, use case, and preferences. I will
                  shortlist and refine options quickly.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={resetChat}
                  className="inline-flex items-center gap-1 rounded-full border border-[#5d7385]/65 bg-[#c6c5b9]/15 px-2.5 py-1 text-[11px] text-[#d7e1e8] transition hover:bg-[#c6c5b9]/25"
                  aria-label="Start new chat"
                >
                  <RefreshCw className="h-3 w-3" />
                  New chat
                </button>
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="rounded-full border border-[#5d7385]/65 bg-[#c6c5b9]/15 p-2 text-[#9cb1be] transition hover:bg-[#c6c5b9]/25 hover:text-[#d7e1e8]"
                  aria-label="Close chat"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="relative mt-3 grid grid-cols-3 gap-2 text-[11px] text-[#b6c6d1]">
              <div className="flex items-center gap-1.5 rounded-lg border border-[#5d7385]/50 bg-[#0b151d]/50 px-2 py-1.5">
                <Gauge className="h-3.5 w-3.5 text-[#8ac2d2]" />
                Budget fit
              </div>
              <div className="flex items-center gap-1.5 rounded-lg border border-[#5d7385]/50 bg-[#0b151d]/50 px-2 py-1.5">
                <ListFilter className="h-3.5 w-3.5 text-[#8ac2d2]" />
                Use-case match
              </div>
              <div className="flex items-center gap-1.5 rounded-lg border border-[#5d7385]/50 bg-[#0b151d]/50 px-2 py-1.5">
                <Sparkles className="h-3.5 w-3.5 text-[#8ac2d2]" />
                Smart follow-ups
              </div>
            </div>
          </div>

          <div
            ref={scrollRef}
            className="max-h-[26rem] space-y-3 overflow-y-auto p-4"
          >
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div className="max-w-[90%] space-y-2.5">
                  <div
                    className={`rounded-2xl px-4 py-3 text-sm leading-6 ${
                      message.role === "user"
                        ? "bg-[linear-gradient(135deg,#62929e,#4f7583)] text-[#f8fbff]"
                        : "border border-[#5d7385]/65 bg-[#15212b]/70 text-[#e8eff4]"
                    }`}
                  >
                    <p className="whitespace-pre-line">{message.content}</p>
                    {message.suggestedAction === "open_tax_calculator" ? (
                      <Link
                        href={
                          message.vehicleIds?.length
                            ? `/dashboard/vehicles/${message.vehicleIds[0]}#cost-calculator`
                            : "/dashboard/vehicles"
                        }
                        className="mt-3 inline-flex rounded-full border border-[#62929e]/35 bg-[#62929e]/15 px-3 py-1 text-xs font-medium text-[#8fd0e0] transition hover:bg-[#62929e]/20"
                      >
                        Calculate Tax
                      </Link>
                    ) : null}
                  </div>

                  {message.role === "assistant" && message.quickReplies?.length ? (
                    <div className="flex flex-wrap gap-2">
                      {message.quickReplies.map((reply) => (
                        <button
                          key={`${index}-${reply}`}
                          type="button"
                          onClick={() => void sendMessage(reply)}
                          className="rounded-full border border-[#5d7385]/65 bg-[#c6c5b9]/10 px-3 py-1.5 text-xs text-[#b9ccd8] transition hover:border-[#62929e]/50 hover:bg-[#62929e]/15 hover:text-[#dbeaf2]"
                        >
                          {reply}
                        </button>
                      ))}
                    </div>
                  ) : null}

                  {message.vehicleIds?.length ? (
                    <div className="space-y-3">
                      {message.vehicleIds.map((vehicleId) => {
                        const vehicle = vehicleLookup.get(vehicleId);
                        if (!vehicle) {
                          return (
                            <div
                              key={vehicleId}
                              className="rounded-2xl border border-[#5d7385]/65 bg-[#c6c5b9]/15 px-4 py-3 text-xs text-[#9cb1be]"
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
                              className="inline-flex rounded-full border border-[#62929e]/35 bg-[#62929e]/15 px-3 py-1 text-xs font-medium text-[#8fd0e0] transition hover:bg-[#62929e]/20"
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
                <div className="rounded-2xl border border-[#5d7385]/65 bg-[#15212b]/70 px-4 py-3 text-sm text-[#c7d6e0]">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1">
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#8fd0e0]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#8fd0e0] [animation-delay:0.12s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#8fd0e0] [animation-delay:0.24s]" />
                    </span>
                    Matching inventory and preparing recommendations...
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          <div className="border-t border-[#5d7385]/65 p-4">
            {messages.length === 1 ? (
              <div className="mb-3 flex flex-wrap gap-2">
                {DISCOVERY_PROMPTS.map((prompt) => (
                  <button
                    key={prompt.label}
                    type="button"
                    onClick={() => void sendMessage(prompt.prompt)}
                    className="rounded-full border border-[#5d7385]/65 bg-[#c6c5b9]/10 px-3 py-1.5 text-xs text-[#c5d6df] transition hover:border-[#62929e]/45 hover:bg-[#62929e]/15 hover:text-[#e4edf3]"
                  >
                    {prompt.label}
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
                className="min-h-11 flex-1 resize-none rounded-2xl border border-[#5d7385]/65 bg-[#0f1b24] px-4 py-3 text-sm text-[#ebf3f8] outline-none placeholder:text-[#8ea2b0] focus:border-[#62929e]/40"
              />
              <button
                type="button"
                onClick={() => void sendMessage()}
                disabled={isSending || !input.trim()}
                className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-[#62929e] text-[#fdfdff] transition hover:bg-[#546a7b] disabled:cursor-not-allowed disabled:opacity-50"
                aria-label="Send message"
              >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            <div className="mt-2 flex items-center justify-between px-1 text-[11px] text-[#8ea2b0]">
              <span>Press Enter to send, Shift+Enter for a new line</span>
              <span>{input.length}/500</span>
            </div>
          </div>
        </div>
      ) : null}

      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className="ml-auto flex h-16 w-16 items-center justify-center rounded-full border border-[#62929e]/30 bg-[radial-gradient(circle_at_30%_30%,#fdfdff,#62929e_55%,#546a7b)] text-[#393d3f] shadow-[0_20px_50px_rgba(98,146,158,0.35)] transition hover:scale-[1.03] hover:shadow-[0_24px_58px_rgba(98,146,158,0.45)]"
        aria-label="Open vehicle assistant"
      >
        <MessageCircle className="h-7 w-7" />
      </button>
    </div>
  );
}
