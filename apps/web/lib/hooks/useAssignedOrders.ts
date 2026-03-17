"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { isAxiosError } from "axios";
import apiClient from "@/lib/api-client";

export type AssignedOrder = {
  id: string;
  status: string;
  payment_status: string;
  total_cost_lkr: number | null;
  created_at: string;
};

const EXPORTER_STATUSES = new Set([
  "ASSIGNED_TO_EXPORTER",
  "AWAITING_SHIPMENT_CONFIRMATION",
  "SHIPPED",
  "IN_TRANSIT",
  "ARRIVED_AT_PORT",
  "CUSTOMS_CLEARANCE",
  "DELIVERED",
  "CANCELLED",
]);

const isExporterStatus = (status: string) => EXPORTER_STATUSES.has(status);

export function useAssignedOrders() {
  const [orders, setOrders] = useState<AssignedOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await apiClient.get<AssignedOrder[]>("/orders");
      setOrders(data);
    } catch (err) {
      if (isAxiosError(err)) {
        if (err.response?.status === 403) {
          setError(
            "Permission denied. The exporter role needs access to assigned orders. Ask the backend to expose an exporter order list endpoint or allow VIEW_ASSIGNED_ORDERS.",
          );
          return;
        }
        setError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            err.message,
        );
      } else {
        setError("Failed to load assigned orders.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const visibleOrders = useMemo(() => {
    const filtered = orders.filter((order) => isExporterStatus(order.status));
    return filtered.length > 0 ? filtered : orders;
  }, [orders]);

  const stats = useMemo(() => {
    const total = visibleOrders.length;
    const awaitingDetails = visibleOrders.filter(
      (order) => order.status === "ASSIGNED_TO_EXPORTER",
    ).length;
    const awaitingApproval = visibleOrders.filter(
      (order) => order.status === "AWAITING_SHIPMENT_CONFIRMATION",
    ).length;
    const inTransit = visibleOrders.filter((order) =>
      ["SHIPPED", "IN_TRANSIT", "ARRIVED_AT_PORT"].includes(order.status),
    ).length;
    const delivered = visibleOrders.filter(
      (order) => order.status === "DELIVERED",
    ).length;

    return { total, awaitingDetails, awaitingApproval, inTransit, delivered };
  }, [visibleOrders]);

  return {
    orders: visibleOrders,
    rawOrders: orders,
    loading,
    error,
    reload,
    stats,
  };
}
