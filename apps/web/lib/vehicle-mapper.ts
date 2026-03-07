import { Vehicle, VehicleResponse } from "@/types/vehicle";

type BackendVehicle = {
  id: string;
  stock_no: string;
  chassis: string | null;
  make: string;
  model: string;
  year: number;
  grade: string | null;
  price_jpy: string | number;
  mileage_km: number | null;
  fuel_type: string | null;
  transmission: string | null;
  engine_cc: number | null;
  image_url: string | null;
  status: "AVAILABLE" | "RESERVED" | "SOLD";
  created_at: string;
  updated_at: string;
  color: string | null;
  reg_year: string | null;
  vehicle_type: string | null;
  steering: string | null;
  drive: string | null;
  seats: number | null;
  doors: number | null;
  location: string | null;
  options: string | null;
  other_remarks: string | null;
};

type BackendVehicleList = {
  vehicles: BackendVehicle[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
};

function apiOrigin(): string {
  const base =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  try {
    return new URL(base).origin;
  } catch {
    return "http://localhost:8000";
  }
}

function isAllowedRemoteHost(hostname: string): boolean {
  const host = hostname.toLowerCase();
  if (host.endsWith(".supabase.co")) return true;

  const allowed = new Set([
    "www.ramadbk.com",
    "images.unsplash.com",
    "lh3.googleusercontent.com",
    "localhost",
    "127.0.0.1",
  ]);
  return allowed.has(host);
}

export function normalizeImageUrl(imageUrl: string | null): string | undefined {
  if (!imageUrl) return undefined;
  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) {
    try {
      const url = new URL(imageUrl);
      if (!isAllowedRemoteHost(url.hostname)) return undefined;
      return imageUrl;
    } catch {
      return undefined;
    }
  }
  return `${apiOrigin()}/${imageUrl.replace(/^\/+/, "")}`;
}

function mapStatus(status: BackendVehicle["status"]): Vehicle["status"] {
  if (status === "SOLD") return "Sold";
  if (status === "RESERVED") return "Upcoming";
  return "Live";
}

export function mapBackendVehicle(v: BackendVehicle): Vehicle {
  const yearNow = new Date().getFullYear();
  const priceJPY =
    typeof v.price_jpy === "string" ? Number(v.price_jpy) : v.price_jpy;

  return {
    id: v.id,
    make: v.make,
    model: v.model,
    year: v.year,
    price: priceJPY,
    mileage: v.mileage_km ?? 0,
    fuel: v.fuel_type ?? "Unknown",
    transmission: v.transmission ?? "Unknown",
    status: mapStatus(v.status),
    condition: v.year >= yearNow ? "New" : "Used",
    imageUrl: normalizeImageUrl(v.image_url),
    lotNumber: v.stock_no,
    grade: v.grade || "-",
    estimatedLandedCostLKR: Math.round(priceJPY * 2.2),
    priceJPY,
    trim: v.model,
    chassisCode: v.chassis || "-",
    engineCC: v.engine_cc ?? 0,
    endTime: v.updated_at || v.created_at,
    firstRegistrationDate: v.reg_year ?? undefined,
    color: v.color ?? undefined,
    vehicleType: v.vehicle_type ?? undefined,
    steering: v.steering ?? undefined,
    drive: v.drive ?? undefined,
    seats: v.seats ?? undefined,
    doors: v.doors ?? undefined,
    location: v.location ?? undefined,
    options: v.options ?? undefined,
    otherRemarks: v.other_remarks ?? undefined,
  };
}

export function mapBackendVehicleList(
  payload: BackendVehicleList,
): VehicleResponse {
  return {
    data: payload.vehicles.map(mapBackendVehicle),
    total: payload.pagination.total,
    page: payload.pagination.page,
    limit: payload.pagination.limit,
  };
}
