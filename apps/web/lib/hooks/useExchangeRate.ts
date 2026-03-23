"use client";

import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";

export type ExchangeRateResponse = {
  base: string;
  target: string;
  rate: number | null;
  date: string | null;
  provider: string;
  source?: string | null;
  rate_type?: string | null;
  error?: string | null;
  fetched_at: string;
};

export function useExchangeRate() {
  return useQuery<ExchangeRateResponse>({
    queryKey: ["exchange-rate", "JPY", "LKR"],
    queryFn: async () => {
      const response = await apiClient.get("/vehicles/exchange-rate", {
        params: { base: "JPY", symbols: "LKR" },
      });
      return response.data as ExchangeRateResponse;
    },
    staleTime: 6 * 60 * 60 * 1000,
    gcTime: 12 * 60 * 60 * 1000,
    retry: 1,
  });
}
