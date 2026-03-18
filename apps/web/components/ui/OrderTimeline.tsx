import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import apiClient from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth";
import { AlertCircle, CheckCircle2, Clock3, PackageCheck } from "lucide-react";

interface TimelineEvent {
  id: string;
  from_status: string | null;
  to_status: string;
  notes: string | null;
  changed_by_name: string;
  changed_by_email: string;
  created_at: string;
}

interface OrderTimelineProps {
  orderId: string;
  onTimelineUpdate?: () => void;
}

const statusStyles: Record<string, string> = {
  CREATED: "border-sky-500/20 bg-sky-500/10 text-sky-200",
  PAYMENT_CONFIRMED: "border-emerald-500/20 bg-emerald-500/10 text-emerald-200",
  LC_REQUESTED: "border-amber-500/20 bg-amber-500/10 text-amber-200",
  LC_APPROVED: "border-emerald-500/20 bg-emerald-500/10 text-emerald-200",
  LC_REJECTED: "border-red-500/20 bg-red-500/10 text-red-200",
  ASSIGNED_TO_EXPORTER:
    "border-fuchsia-500/20 bg-fuchsia-500/10 text-fuchsia-200",
  SHIPMENT_DOCS_UPLOADED:
    "border-violet-500/20 bg-violet-500/10 text-violet-200",
  AWAITING_SHIPMENT_CONFIRMATION:
    "border-orange-500/20 bg-orange-500/10 text-orange-200",
  SHIPPED: "border-indigo-500/20 bg-indigo-500/10 text-indigo-200",
  IN_TRANSIT: "border-cyan-500/20 bg-cyan-500/10 text-cyan-200",
  ARRIVED_AT_PORT: "border-teal-500/20 bg-teal-500/10 text-teal-200",
  CUSTOMS_CLEARANCE: "border-yellow-500/20 bg-yellow-500/10 text-yellow-200",
  DELIVERED: "border-emerald-500/20 bg-emerald-500/10 text-emerald-100",
  CANCELLED: "border-red-500/20 bg-red-500/10 text-red-200",
};

function getStatusIcon(status: string) {
  const icons: Record<string, ReactNode> = {
    CREATED: <PackageCheck className="h-4 w-4" />,
    PAYMENT_CONFIRMED: <CheckCircle2 className="h-4 w-4" />,
    LC_REQUESTED: <Clock3 className="h-4 w-4" />,
    LC_APPROVED: <CheckCircle2 className="h-4 w-4" />,
    LC_REJECTED: <AlertCircle className="h-4 w-4" />,
    ASSIGNED_TO_EXPORTER: <PackageCheck className="h-4 w-4" />,
    SHIPMENT_DOCS_UPLOADED: <PackageCheck className="h-4 w-4" />,
    AWAITING_SHIPMENT_CONFIRMATION: <Clock3 className="h-4 w-4" />,
    SHIPPED: <PackageCheck className="h-4 w-4" />,
    IN_TRANSIT: <Clock3 className="h-4 w-4" />,
    ARRIVED_AT_PORT: <PackageCheck className="h-4 w-4" />,
    CUSTOMS_CLEARANCE: <Clock3 className="h-4 w-4" />,
    DELIVERED: <CheckCircle2 className="h-4 w-4" />,
    CANCELLED: <AlertCircle className="h-4 w-4" />,
  };

  return icons[status] ?? <Clock3 className="h-4 w-4" />;
}

export function OrderTimeline({
  orderId,
  onTimelineUpdate,
}: OrderTimelineProps) {
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const lastSnapshotRef = useRef<string | null>(null);
  const initialEventSkippedRef = useRef(false);

  useEffect(() => {
    void fetchTimeline();
  }, [orderId]);

  useEffect(() => {
    const accessToken = getAccessToken();
    const streamUrl = `${apiClient.defaults.baseURL}/orders/${orderId}/timeline/stream`;
    const controller = new AbortController();

    lastSnapshotRef.current = null;
    initialEventSkippedRef.current = false;

    if (!accessToken) {
      return () => controller.abort();
    }

    const subscribe = async () => {
      try {
        const response = await fetch(streamUrl, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
            Accept: "text/event-stream",
          },
          signal: controller.signal,
        });

        if (!response.ok || !response.body) {
          throw new Error("Realtime timeline stream unavailable");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (!controller.signal.aborted) {
          const { done, value } = await reader.read();
          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split("\n\n");
          buffer = events.pop() ?? "";

          for (const eventBlock of events) {
            if (!eventBlock.includes("event: timeline")) {
              continue;
            }
            const dataLine = eventBlock
              .split("\n")
              .find((line) => line.startsWith("data: "));
            const payload = dataLine?.replace("data: ", "").trim();

            if (payload) {
              if (!initialEventSkippedRef.current) {
                initialEventSkippedRef.current = true;
                lastSnapshotRef.current = payload;
                continue;
              }

              if (payload === lastSnapshotRef.current) {
                continue;
              }

              lastSnapshotRef.current = payload;
            }

            void fetchTimeline({ silent: true });
            onTimelineUpdate?.();
          }
        }
      } catch {
        // Keep the UI functional even if streaming is unavailable.
      }
    };

    void subscribe();

    return () => controller.abort();
  }, [orderId, onTimelineUpdate]);

  const fetchTimeline = async ({
    silent = false,
  }: { silent?: boolean } = {}) => {
    if (!silent) {
      setLoading(true);
      setError(null);
    }

    try {
      const { data } = await apiClient.get(`/orders/${orderId}/timeline`);
      setTimeline(data.timeline);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to fetch timeline";
      setError(message);
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="rounded-[24px] border border-[#c6c5b9]/50 bg-[#c6c5b9]/20 p-8 text-sm text-[#546a7b]">
        Loading timeline...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-[24px] border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-200">
        {error}
      </div>
    );
  }

  return (
    <div className="rounded-[24px] border border-[#c6c5b9]/50 bg-[#c6c5b9]/20 p-6">
      <h3 className="mb-6 text-xl font-semibold text-[#393d3f]">Order Timeline</h3>

      <div className="relative">
        <div className="absolute bottom-0 left-4 top-0 w-px bg-[#c6c5b9]/30"></div>

        <div className="space-y-6">
          {timeline.map((event) => (
            <div key={event.id} className="relative pl-10">
              <div className="absolute left-0 flex h-8 w-8 items-center justify-center rounded-full border border-[#62929e]/20 bg-[#fdfdff] text-[#62929e]">
                {getStatusIcon(event.to_status)}
              </div>

              <div className="rounded-2xl border border-[#c6c5b9]/50 bg-[#fdfdff] p-4">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <Badge
                      className={
                        statusStyles[event.to_status] ??
                        "border-[#c6c5b9]/50 bg-[#c6c5b9]/20 text-[#393d3f]"
                      }
                    >
                      {event.to_status.replace(/_/g, " ")}
                    </Badge>
                  </div>
                  <span className="text-sm text-[#546a7b]">
                    {formatDate(event.created_at)}
                  </span>
                </div>

                {event.notes && (
                  <p className="mb-2 text-sm text-[#546a7b]">{event.notes}</p>
                )}

                <p className="text-sm text-[#546a7b]">
                  Changed by{" "}
                  <span className="font-medium text-[#393d3f]">
                    {event.changed_by_name}
                  </span>
                  {" · "}
                  <span>{event.changed_by_email}</span>
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {timeline.length === 0 && (
        <p className="py-8 text-center text-[#546a7b]">No timeline events yet</p>
      )}
    </div>
  );
}

