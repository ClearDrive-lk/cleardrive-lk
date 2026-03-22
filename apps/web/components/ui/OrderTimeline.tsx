import type { ReactNode } from "react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import apiClient from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth";
import { getOrderStatusBadgeClass } from "@/lib/order-status-badge";
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
  const fetchTimeline = useCallback(
    async ({ silent = false }: { silent?: boolean } = {}) => {
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
    },
    [orderId],
  );

  useEffect(() => {
    void fetchTimeline();
  }, [fetchTimeline]);

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
  }, [orderId, onTimelineUpdate, fetchTimeline]);

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
      <div className="rounded-[24px] border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-8 text-sm text-[#546a7b]">
        Loading timeline...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-[24px] border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-200">
        {error}
      </div>
    );
  }

  return (
    <div className="rounded-[24px] border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6">
      <h3 className="mb-6 text-xl font-semibold text-[#393d3f]">
        Order Timeline
      </h3>

      <div className="relative">
        <div className="absolute bottom-0 left-4 top-0 w-px bg-[#c6c5b9]/30"></div>

        <div className="space-y-6">
          {timeline.map((event) => (
            <div key={event.id} className="relative pl-10">
              <div className="absolute left-0 flex h-8 w-8 items-center justify-center rounded-full border border-[#62929e]/20 bg-[#fdfdff] text-[#62929e]">
                {getStatusIcon(event.to_status)}
              </div>

              <div className="rounded-2xl border border-[#546a7b]/65 bg-[#fdfdff] p-4">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <Badge
                      className={getOrderStatusBadgeClass(event.to_status)}
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
        <p className="py-8 text-center text-[#546a7b]">
          No timeline events yet
        </p>
      )}
    </div>
  );
}
