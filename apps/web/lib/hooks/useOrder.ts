"use client";

import { useEffect, useState } from "react";
import axios from "axios";

import { apiClient } from "@/lib/api-client";

export interface OrderTrackingData {
  id: string;
  currentStep: number;
  vehicle: {
    id: string;
    make: string;
    model: string;
    year: number;
    lotNumber?: string | null;
    color?: string | null;
    imageUrl?: string | null;
  };
  etaCountdown?: string | null;
  documents: Array<{
    id?: string;
    key?: string;
    name: string;
    downloadUrl?: string | null;
  }>;
}

export function useOrder(id: string) {
  const [data, setData] = useState<OrderTrackingData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setData(null);
      setError(null);
      setIsLoading(false);
      return;
    }

    let isMounted = true;
    const fetchOrder = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await apiClient.get(`/orders/${id}`);
        const orderPayload = response.data?.data ?? response.data;

        if (!isMounted) return;
        setData(orderPayload as OrderTrackingData);
      } catch (fetchError) {
        if (!isMounted) return;
        setData(null);

        if (axios.isAxiosError(fetchError)) {
          const apiMessage =
            (fetchError.response?.data as { detail?: string; message?: string } | undefined)
              ?.detail ??
            (fetchError.response?.data as { detail?: string; message?: string } | undefined)
              ?.message;

          setError(apiMessage || fetchError.message || "Failed to load order.");
        } else {
          setError(
            fetchError instanceof Error
              ? fetchError.message
              : "Failed to load order.",
          );
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void fetchOrder();

    return () => {
      isMounted = false;
    };
  }, [id]);

  return { data, isLoading, error };
}

