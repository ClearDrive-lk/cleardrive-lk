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
};

export function useVehicles(params: VehiclesQueryParams) {
  return useQuery<VehicleResponse>({
    queryKey: ["vehicles", params],
    queryFn: async () => {
      const apiParams = {
        page: params.page,
        limit: params.limit,
        search: params.search,
        fuel_type:
          params.fuel === "Petrol"
            ? "Gasoline"
            : params.fuel === "All"
              ? undefined
              : params.fuel,
        status:
          params.status === "Sold"
            ? "SOLD"
            : params.status === "Upcoming"
              ? "RESERVED"
              : params.status === "Live"
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
        price_min: params.minPrice,
        price_max: params.maxPrice,
        year_min: params.minYear,
        year_max: params.maxYear,
        recent_only: params.minYear === undefined ? true : undefined,
        mileage_max: params.maxMileage,
        transmission:
          params.transmission === "AT"
            ? "Automatic"
            : params.transmission === "MT"
              ? "Manual"
              : params.transmission === "All"
                ? undefined
                : params.transmission,
      };

      const response = await apiClient.get("/vehicles", {
        params: apiParams,
      });
      return mapBackendVehicleList(response.data);
    },
  });
}
