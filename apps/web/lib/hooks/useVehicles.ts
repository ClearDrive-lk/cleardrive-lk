"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { VehicleResponse } from "@/types/vehicle";
import { mapBackendVehicleList } from "@/lib/vehicle-mapper";

type VehiclesQueryParams = {
  page?: number;
  limit?: number;
  search?: string;
  fuel?: string;
  status?: string;
  sort?: string;
  minPrice?: number;
  maxPrice?: number;
  minYear?: number;
  maxYear?: number;
  maxMileage?: number;
  transmission?: string;
  vehicleType?: string;
  priceCurrency?: "LKR" | "JPY";
  exchangeRate?: number;
};

const JPY_LKR_RATE = 2.25;

const lkrToJpy = (amount: number | undefined, rate: number) => {
  if (!amount || amount <= 0) return undefined;
  return Math.round(amount / rate);
};

export function useVehicles(params: VehiclesQueryParams) {
  return useQuery<VehicleResponse>({
    queryKey: [
      "vehicles",
      params.page,
      params.limit,
      params.search ?? "",
      params.fuel ?? "",
      params.status ?? "",
      params.sort ?? "",
      params.minPrice ?? "",
      params.maxPrice ?? "",
      params.minYear ?? "",
      params.maxYear ?? "",
      params.maxMileage ?? "",
      params.transmission ?? "",
      params.vehicleType ?? "",
      params.priceCurrency ?? "",
      params.exchangeRate ? Number(params.exchangeRate.toFixed(4)) : "",
    ],
    queryFn: async () => {
      const exchangeRate = params.exchangeRate || JPY_LKR_RATE;
      const priceCurrency = params.priceCurrency || "LKR";
      const toJpy = (value: number | undefined) =>
        priceCurrency === "JPY" ? value : lkrToJpy(value, exchangeRate);

      const apiParams = {
        page: params.page,
        limit: params.limit,
        search: params.search || undefined,
        fuel_type:
          params.fuel === "Petrol"
            ? "Gasoline"
            : params.fuel === "Gasoline"
              ? "Gasoline"
              : params.fuel === "Gasoline/Hybrid"
                ? "Gasoline/hybrid"
                : params.fuel === "Hybrid"
                  ? "Gasoline/hybrid"
                  : params.fuel === "All"
                    ? undefined
                    : params.fuel,
        status:
          params.status === "Sold"
            ? "SOLD"
            : params.status === "Upcoming"
              ? "RESERVED"
              : params.status === "Live" || params.status === "Available"
                ? "AVAILABLE"
                : undefined,
        sort_by:
          params.sort === "price_asc" || params.sort === "price_desc"
            ? "price_jpy"
            : params.sort === "year_desc"
              ? "year"
              : params.sort === "mileage_asc"
                ? "mileage_km"
                : "created_at",
        sort_order:
          params.sort === "price_asc" || params.sort === "mileage_asc"
            ? "asc"
            : "desc",
        price_min: toJpy(params.minPrice),
        price_max: toJpy(params.maxPrice),
        year_min: params.minYear,
        year_max: params.maxYear,
        mileage_max: params.maxMileage,
        transmission:
          params.transmission === "Automatic" || params.transmission === "AT"
            ? "Automatic"
            : params.transmission === "MT"
              ? "Manual"
              : params.transmission === "All"
                ? undefined
                : params.transmission,
        vehicle_type:
          params.vehicleType === "All" ? undefined : params.vehicleType,
      };

      const response = await apiClient.get("/vehicles", {
        params: apiParams,
      });
      return mapBackendVehicleList(response.data);
    },
    staleTime: 0,
    gcTime: 5 * 60_000,
    refetchOnWindowFocus: false,
    refetchOnMount: "always",
    retry: (failureCount, error) => {
      const status = (error as { response?: { status?: number } })?.response
        ?.status;
      if (status === 429) return false;
      return failureCount < 1;
    },
  });
}
