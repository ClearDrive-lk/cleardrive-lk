"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { ArrowLeft, Loader2, Save, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api-client";
import { useToast } from "@/lib/hooks/use-toast";
import { mapBackendVehicle, normalizeImageUrl } from "@/lib/vehicle-mapper";
import type { Vehicle } from "@/types/vehicle";

type BackendPatchStatus = "AVAILABLE" | "RESERVED" | "SOLD";
type BackendFuelType =
  | "Gasoline"
  | "Gasoline/hybrid"
  | "Diesel"
  | "Electric"
  | "Plugin Hybrid";
type BackendTransmission = "Automatic" | "Manual" | "CVT";
type BackendVehicleType =
  | "Sedan"
  | "SUV"
  | "Hatchback"
  | "Van/minivan"
  | "Wagon"
  | "Pickup"
  | "Coupe"
  | "Convertible"
  | "Bikes"
  | "Machinery";

function useVehicle(id: string) {
  return useQuery<Vehicle>({
    queryKey: ["admin-vehicle", id],
    queryFn: async () => {
      const response = await apiClient.get(`/vehicles/${id}`);
      return mapBackendVehicle(response.data);
    },
    enabled: Boolean(id),
  });
}

function useVehicleImages(id: string) {
  return useQuery<string[]>({
    queryKey: ["admin-vehicle-images", id],
    queryFn: async () => {
      const response = await apiClient.get(`/vehicles/${id}/images`);
      const raw = Array.isArray(response.data?.images)
        ? response.data.images
        : [];
      return raw
        .map((item: string) => normalizeImageUrl(item) || null)
        .filter((item: string | null): item is string => Boolean(item));
    },
    enabled: Boolean(id),
  });
}

function mapFrontendStatusToBackend(
  status: Vehicle["status"],
): BackendPatchStatus {
  if (status === "Sold") return "SOLD";
  if (status === "Upcoming") return "RESERVED";
  return "AVAILABLE";
}

export default function AdminVehicleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const vehicleQuery = useVehicle(id);
  const imagesQuery = useVehicleImages(id);

  const [stockNo, setStockNo] = useState("");
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [year, setYear] = useState("");
  const [grade, setGrade] = useState("");
  const [chassis, setChassis] = useState("");
  const [priceJPY, setPriceJPY] = useState("");
  const [mileageKM, setMileageKM] = useState("");
  const [engineCC, setEngineCC] = useState("");
  const [fuelType, setFuelType] = useState<BackendFuelType>("Gasoline");
  const [transmission, setTransmission] =
    useState<BackendTransmission>("Automatic");
  const [vehicleType, setVehicleType] = useState<BackendVehicleType>("Sedan");
  const [status, setStatus] = useState<BackendPatchStatus>("AVAILABLE");
  const [imageUrl, setImageUrl] = useState("");
  const [color, setColor] = useState("");
  const [location, setLocation] = useState("");
  const [options, setOptions] = useState("");
  const [otherRemarks, setOtherRemarks] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const vehicle = vehicleQuery.data;
    if (!vehicle) return;
    setStockNo(vehicle.lotNumber ?? "");
    setMake(vehicle.make ?? "");
    setModel(vehicle.model ?? "");
    setYear(vehicle.year ? String(vehicle.year) : "");
    setGrade(vehicle.grade && vehicle.grade !== "-" ? vehicle.grade : "");
    setChassis(
      vehicle.chassisCode && vehicle.chassisCode !== "-"
        ? vehicle.chassisCode
        : "",
    );
    setPriceJPY(vehicle.priceJPY > 0 ? String(vehicle.priceJPY) : "");
    setMileageKM(vehicle.mileage > 0 ? String(vehicle.mileage) : "");
    setEngineCC(vehicle.engineCC ? String(vehicle.engineCC) : "");
    setFuelType(
      vehicle.fuel === "Diesel" ||
        vehicle.fuel === "Electric" ||
        vehicle.fuel === "Plugin Hybrid" ||
        vehicle.fuel === "Gasoline/hybrid"
        ? vehicle.fuel
        : "Gasoline",
    );
    setTransmission(
      vehicle.transmission === "Manual" || vehicle.transmission === "CVT"
        ? vehicle.transmission
        : "Automatic",
    );
    setVehicleType(
      vehicle.vehicleType === "SUV" ||
        vehicle.vehicleType === "Hatchback" ||
        vehicle.vehicleType === "Van/minivan" ||
        vehicle.vehicleType === "Wagon" ||
        vehicle.vehicleType === "Pickup" ||
        vehicle.vehicleType === "Coupe" ||
        vehicle.vehicleType === "Convertible" ||
        vehicle.vehicleType === "Bikes" ||
        vehicle.vehicleType === "Machinery"
        ? vehicle.vehicleType
        : "Sedan",
    );
    setStatus(mapFrontendStatusToBackend(vehicle.status));
    setImageUrl(vehicle.imageUrl ?? "");
    setColor(vehicle.color ?? "");
    setLocation(vehicle.location ?? "");
    setOptions(vehicle.options ?? "");
    setOtherRemarks(vehicle.otherRemarks ?? "");
  }, [vehicleQuery.data]);

  const gallery = useMemo(() => {
    if (imagesQuery.data?.length) return imagesQuery.data;
    if (vehicleQuery.data?.imageUrl) return [vehicleQuery.data.imageUrl];
    return [];
  }, [imagesQuery.data, vehicleQuery.data?.imageUrl]);

  const saveChanges = async () => {
    if (!id) return;
    const parsedYear = Number(year);
    const parsedPrice = Number(priceJPY);
    const parsedMileage = Number(mileageKM);
    const parsedEngineCC = Number(engineCC);
    if (!stockNo.trim() || !make.trim() || !model.trim()) {
      toast({
        title: "Missing vehicle identity",
        description: "Stock number, make, and model are required.",
        variant: "destructive",
      });
      return;
    }
    if (
      !Number.isFinite(parsedYear) ||
      parsedYear < 1980 ||
      parsedYear > 2027
    ) {
      toast({
        title: "Invalid year",
        description: "Year must be between 1980 and 2027.",
        variant: "destructive",
      });
      return;
    }
    if (!Number.isFinite(parsedPrice) || parsedPrice <= 0) {
      toast({
        title: "Invalid price",
        description: "Price must be a positive JPY amount.",
        variant: "destructive",
      });
      return;
    }
    if (mileageKM && (!Number.isFinite(parsedMileage) || parsedMileage < 0)) {
      toast({
        title: "Invalid mileage",
        description: "Mileage must be zero or a positive number.",
        variant: "destructive",
      });
      return;
    }
    if (engineCC && (!Number.isFinite(parsedEngineCC) || parsedEngineCC < 0)) {
      toast({
        title: "Invalid engine size",
        description: "Engine CC must be zero or a positive number.",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);
    try {
      await apiClient.patch(`/vehicles/${id}`, {
        stock_no: stockNo.trim(),
        make: make.trim(),
        model: model.trim(),
        year: parsedYear,
        grade: grade.trim() || null,
        chassis: chassis.trim() || null,
        price_jpy: parsedPrice,
        mileage_km: mileageKM ? parsedMileage : null,
        engine_cc: engineCC ? parsedEngineCC : null,
        fuel_type: fuelType,
        transmission,
        vehicle_type: vehicleType,
        status,
        image_url: imageUrl.trim() || null,
        color: color.trim() || null,
        location: location.trim() || null,
        options: options.trim() || null,
        other_remarks: otherRemarks.trim() || null,
      });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["vehicles"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-vehicle", id] }),
        queryClient.invalidateQueries({ queryKey: ["vehicle", id] }),
        queryClient.invalidateQueries({
          queryKey: ["admin-vehicle-images", id],
        }),
        queryClient.invalidateQueries({ queryKey: ["vehicle-images", id] }),
      ]);
      toast({
        title: "Vehicle updated",
        description: "Admin changes were saved successfully.",
        variant: "success",
      });
      await vehicleQuery.refetch();
      await imagesQuery.refetch();
    } catch (error: unknown) {
      toast({
        title: "Update failed",
        description: isAxiosError(error)
          ? ((error.response?.data as { detail?: string } | undefined)
              ?.detail ?? "Failed to save vehicle changes.")
          : "Failed to save vehicle changes.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  if (vehicleQuery.isLoading) {
    return (
      <div className="cd-container flex min-h-[70vh] items-center justify-center py-6">
        <div className="rounded-3xl border border-[#546a7b]/65 bg-[#fdfdff]/70 p-6 text-[#393d3f]">
          <Loader2 className="mx-auto mb-3 h-8 w-8 animate-spin text-[#62929e]" />
          Loading vehicle editor...
        </div>
      </div>
    );
  }

  if (vehicleQuery.isError || !vehicleQuery.data) {
    return (
      <div className="cd-container py-6">
        <div className="rounded-3xl border border-red-500/35 bg-red-500/10 p-6">
          <p className="text-lg font-semibold text-[#393d3f]">
            Vehicle not available
          </p>
          <p className="mt-2 text-sm text-red-700">
            {isAxiosError(vehicleQuery.error)
              ? ((
                  vehicleQuery.error.response?.data as
                    | { detail?: string }
                    | undefined
                )?.detail ?? vehicleQuery.error.message)
              : "The vehicle could not be loaded."}
          </p>
          <div className="mt-4">
            <Button asChild variant="outline">
              <Link href="/admin/vehicles">Back to vehicles</Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const vehicle = vehicleQuery.data;

  return (
    <div className="cd-container space-y-6 py-6 text-[#393d3f]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button asChild variant="outline">
          <Link href="/admin/vehicles">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to vehicles
          </Link>
        </Button>
        <Badge variant="secondary" className="rounded-xl px-3 py-2">
          <ShieldCheck className="h-3.5 w-3.5" />
          Admin editor
        </Badge>
      </div>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <article className="rounded-3xl border border-[#546a7b]/65 bg-[#fdfdff]/70 p-6">
          <div className="flex flex-col gap-4 lg:flex-row">
            <div className="relative h-72 w-full overflow-hidden rounded-2xl border border-[#546a7b]/40 bg-[#c6c5b9]/20 lg:h-96 lg:flex-1">
              {gallery[0] ? (
                <Image
                  src={gallery[0]}
                  alt={`${vehicle.year} ${vehicle.make} ${vehicle.model}`}
                  fill
                  sizes="(max-width: 1024px) 100vw, 60vw"
                  className="object-cover"
                />
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-[#546a7b]">
                  No gallery image available
                </div>
              )}
            </div>
            <div className="w-full space-y-4 lg:max-w-sm">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#62929e]">
                  Listing
                </p>
                <h1 className="mt-2 text-3xl font-semibold">
                  {vehicle.year} {vehicle.make} {vehicle.model}
                </h1>
                <p className="mt-1 text-sm text-[#546a7b]">
                  Stock #{vehicle.lotNumber} • {vehicle.status} •{" "}
                  {vehicle.location ?? "Japan"}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-[#546a7b]/40 bg-[#c6c5b9]/20 p-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-[#546a7b]">
                    Current Bid
                  </p>
                  <p className="mt-1 text-lg font-semibold">
                    {vehicle.priceJPY > 0
                      ? `${vehicle.priceJPY.toLocaleString()} JPY`
                      : "Pending"}
                  </p>
                </div>
                <div className="rounded-2xl border border-[#546a7b]/40 bg-[#c6c5b9]/20 p-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-[#546a7b]">
                    Mileage
                  </p>
                  <p className="mt-1 text-lg font-semibold">
                    {vehicle.mileage.toLocaleString()} km
                  </p>
                </div>
                <div className="rounded-2xl border border-[#546a7b]/40 bg-[#c6c5b9]/20 p-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-[#546a7b]">
                    Fuel
                  </p>
                  <p className="mt-1 text-lg font-semibold">{vehicle.fuel}</p>
                </div>
                <div className="rounded-2xl border border-[#546a7b]/40 bg-[#c6c5b9]/20 p-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-[#546a7b]">
                    Transmission
                  </p>
                  <p className="mt-1 text-lg font-semibold">
                    {vehicle.transmission}
                  </p>
                </div>
              </div>

              {gallery.length > 1 ? (
                <div className="grid grid-cols-3 gap-2">
                  {gallery.slice(1, 7).map((image, index) => (
                    <div
                      key={`${image}-${index}`}
                      className="relative h-24 overflow-hidden rounded-xl border border-[#546a7b]/40"
                    >
                      <Image
                        src={image}
                        alt={`Vehicle gallery ${index + 2}`}
                        fill
                        sizes="96px"
                        className="object-cover"
                      />
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        </article>

        <aside className="rounded-3xl border border-[#546a7b]/65 bg-[#fdfdff]/70 p-6">
          <div className="mb-5">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#62929e]">
              Admin Edit Panel
            </p>
            <h2 className="mt-2 text-2xl font-semibold">
              Update vehicle fields
            </h2>
            <p className="mt-2 text-sm text-[#546a7b]">
              This writes directly to the admin vehicle update endpoint. Keep
              edits limited to verified listing data.
            </p>
          </div>

          <div className="space-y-4">
            <label className="block space-y-2">
              <span className="text-sm font-medium text-[#393d3f]">
                Price (JPY)
              </span>
              <Input
                value={priceJPY}
                onChange={(event) => setPriceJPY(event.target.value)}
              />
            </label>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2">
                <span className="text-sm font-medium text-[#393d3f]">
                  Stock number
                </span>
                <Input
                  value={stockNo}
                  onChange={(event) => setStockNo(event.target.value)}
                />
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-[#393d3f]">Year</span>
                <Input
                  value={year}
                  onChange={(event) => setYear(event.target.value)}
                />
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2">
                <span className="text-sm font-medium text-[#393d3f]">Make</span>
                <Input
                  value={make}
                  onChange={(event) => setMake(event.target.value)}
                />
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-[#393d3f]">
                  Model
                </span>
                <Input
                  value={model}
                  onChange={(event) => setModel(event.target.value)}
                />
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2">
                <span className="text-sm font-medium text-[#393d3f]">
                  Grade
                </span>
                <Input
                  value={grade}
                  onChange={(event) => setGrade(event.target.value)}
                />
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-[#393d3f]">
                  Chassis
                </span>
                <Input
                  value={chassis}
                  onChange={(event) => setChassis(event.target.value)}
                />
              </label>
            </div>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-[#393d3f]">
                Mileage (km)
              </span>
              <Input
                value={mileageKM}
                onChange={(event) => setMileageKM(event.target.value)}
              />
            </label>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2">
                <span className="text-sm font-medium text-[#393d3f]">
                  Engine CC
                </span>
                <Input
                  value={engineCC}
                  onChange={(event) => setEngineCC(event.target.value)}
                />
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-[#393d3f]">
                  Fuel type
                </span>
                <select
                  value={fuelType}
                  onChange={(event) =>
                    setFuelType(event.target.value as BackendFuelType)
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs"
                >
                  <option value="Gasoline">Gasoline</option>
                  <option value="Gasoline/hybrid">Gasoline/hybrid</option>
                  <option value="Diesel">Diesel</option>
                  <option value="Electric">Electric</option>
                  <option value="Plugin Hybrid">Plugin Hybrid</option>
                </select>
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2">
                <span className="text-sm font-medium text-[#393d3f]">
                  Transmission
                </span>
                <select
                  value={transmission}
                  onChange={(event) =>
                    setTransmission(event.target.value as BackendTransmission)
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs"
                >
                  <option value="Automatic">Automatic</option>
                  <option value="Manual">Manual</option>
                  <option value="CVT">CVT</option>
                </select>
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-[#393d3f]">
                  Vehicle type
                </span>
                <select
                  value={vehicleType}
                  onChange={(event) =>
                    setVehicleType(event.target.value as BackendVehicleType)
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs"
                >
                  <option value="Sedan">Sedan</option>
                  <option value="SUV">SUV</option>
                  <option value="Hatchback">Hatchback</option>
                  <option value="Van/minivan">Van/minivan</option>
                  <option value="Wagon">Wagon</option>
                  <option value="Pickup">Pickup</option>
                  <option value="Coupe">Coupe</option>
                  <option value="Convertible">Convertible</option>
                  <option value="Bikes">Bikes</option>
                  <option value="Machinery">Machinery</option>
                </select>
              </label>
            </div>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-[#393d3f]">Status</span>
              <select
                value={status}
                onChange={(event) =>
                  setStatus(event.target.value as BackendPatchStatus)
                }
                className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs"
              >
                <option value="AVAILABLE">AVAILABLE</option>
                <option value="RESERVED">RESERVED</option>
                <option value="SOLD">SOLD</option>
              </select>
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-[#393d3f]">
                Primary image URL
              </span>
              <Input
                value={imageUrl}
                onChange={(event) => setImageUrl(event.target.value)}
              />
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-[#393d3f]">Color</span>
              <Input
                value={color}
                onChange={(event) => setColor(event.target.value)}
              />
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-[#393d3f]">
                Location
              </span>
              <Input
                value={location}
                onChange={(event) => setLocation(event.target.value)}
              />
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-[#393d3f]">
                Options
              </span>
              <textarea
                value={options}
                onChange={(event) => setOptions(event.target.value)}
                rows={4}
                className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs"
              />
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-[#393d3f]">
                Other remarks
              </span>
              <textarea
                value={otherRemarks}
                onChange={(event) => setOtherRemarks(event.target.value)}
                rows={4}
                className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs"
              />
            </label>

            <Button
              type="button"
              onClick={() => void saveChanges()}
              disabled={saving}
              className="w-full bg-[#62929e] text-[#fdfdff] hover:bg-[#4f7d87]"
            >
              {saving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save vehicle changes
            </Button>
          </div>
        </aside>
      </section>

      <section className="rounded-3xl border border-[#546a7b]/65 bg-[#fdfdff]/70 p-6">
        <h3 className="text-lg font-semibold text-[#393d3f]">Listing notes</h3>
        <p className="mt-2 text-sm text-[#546a7b] whitespace-pre-wrap">
          {vehicle.otherRemarks ||
            vehicle.options ||
            "No notes attached to this vehicle."}
        </p>
        <div className="mt-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push("/admin/vehicles")}
          >
            Return to catalog
          </Button>
        </div>
      </section>
    </div>
  );
}
