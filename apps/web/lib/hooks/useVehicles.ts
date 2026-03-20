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

const normalizeToken = (value: string | undefined) =>
  value?.trim().toLowerCase() ?? "";

const mapFuelFilter = (fuel: string | undefined) => {
  const token = normalizeToken(fuel);
  if (!token || token === "all") return undefined;
  if (["petrol", "gasoline", "gas"].includes(token)) return "petrol";
  if (
    ["hybrid", "gasoline/hybrid", "gasoline hybrid", "petrol/hybrid"].includes(
      token,
    )
  )
    return "hybrid";
  if (["plugin hybrid", "plug-in hybrid", "phev"].includes(token))
    return "plugin_hybrid";
  if (token === "diesel") return "diesel";
  if (["electric", "ev", "bev"].includes(token)) return "electric";
  if (token === "cng") return "cng";
  return fuel;
};

const mapStatusFilter = (status: string | undefined) => {
  const token = normalizeToken(status);
  if (!token || token === "all") return undefined;
  if (["live", "available"].includes(token)) return "AVAILABLE";
  if (token === "upcoming") return "RESERVED";
  if (token === "sold") return "SOLD";
  return undefined;
};

const mapSort = (sort: string | undefined) => {
  switch (sort) {
    case "price_asc":
    case "price_desc":
      return { sort_by: "price_jpy", sort_order: sort === "price_asc" ? "asc" : "desc" };
    case "year_desc":
      return { sort_by: "year", sort_order: "desc" };
    case "mileage_asc":
      return { sort_by: "mileage_km", sort_order: "asc" };
    default:
      return { sort_by: "created_at", sort_order: "desc" };
  }
};

const mapTransmissionFilter = (transmission: string | undefined) => {
  const token = normalizeToken(transmission);
  if (!token || token === "all") return undefined;
  if (["automatic", "auto", "at", "a/t"].includes(token)) return "automatic";
  if (["manual", "mt", "m/t"].includes(token)) return "manual";
  if (token === "cvt") return "cvt";
  return transmission;
};

const mapVehicleTypeFilter = (vehicleType: string | undefined) => {
  const token = normalizeToken(vehicleType);
  if (!token || token === "all") return undefined;
  if (["suv", "suvs", "sport utility vehicle"].includes(token)) return "suv";
  if (["sedan", "saloon"].includes(token)) return "sedan";
  if (["hatchback", "hatch"].includes(token)) return "hatchback";
  if (["van/minivan", "van", "minivan", "mini van", "mpv"].includes(token))
    return "van_minivan";
  if (["wagon", "estate"].includes(token)) return "wagon";
  if (["pickup", "pick up", "pickup truck", "truck"].includes(token))
    return "pickup";
  if (["coupe"].includes(token)) return "coupe";
  if (["convertible", "cabriolet"].includes(token)) return "convertible";
  if (["bike", "bikes", "motorcycle", "motorbike"].includes(token))
    return "bikes";
  if (["machinery", "equipment", "heavy machinery"].includes(token))
    return "machinery";
  return vehicleType;
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
      const { sort_by, sort_order } = mapSort(params.sort);

      const apiParams = {
        page: params.page,
        limit: params.limit,
        search: params.search || undefined,
        fuel_type: mapFuelFilter(params.fuel),
        status: mapStatusFilter(params.status),
        sort_by,
        sort_order,
        price_min: toJpy(params.minPrice),
        price_max: toJpy(params.maxPrice),
        year_min: params.minYear,
        year_max: params.maxYear,
        mileage_max: params.maxMileage,
        transmission: mapTransmissionFilter(params.transmission),
        vehicle_type: mapVehicleTypeFilter(params.vehicleType),
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
