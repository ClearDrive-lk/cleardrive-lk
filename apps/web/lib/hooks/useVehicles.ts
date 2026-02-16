"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { VehicleResponse } from "@/types/vehicle";

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
      const response = await apiClient.get<VehicleResponse>("/vehicles", {
        params,
      });
      return response.data;
    },
  });
}
