import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Vehicle } from "@/types/vehicle";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Fuel, Gauge, Calendar, Timer, Car, Trash2 } from "lucide-react";

interface VehicleCardProps {
  vehicle: Vehicle;
  href?: string;
  onDelete?: (vehicle: Vehicle) => void;
  deleteDisabled?: boolean;
}

export function VehicleCard({
  vehicle,
  href = `/dashboard/vehicles/${vehicle.id}`,
  onDelete,
  deleteDisabled = false,
}: VehicleCardProps) {
  const [imageError, setImageError] = useState(false);
  const router = useRouter();

  const formatJPY = new Intl.NumberFormat("ja-JP", {
    style: "currency",
    currency: "JPY",
    maximumSignificantDigits: 3,
  }).format;
  const formatLKR = new Intl.NumberFormat("en-LK", {
    style: "currency",
    currency: "LKR",
    maximumSignificantDigits: 3,
  }).format;
  const formatKm = new Intl.NumberFormat("en-US").format;

  const hasPrice = Number.isFinite(vehicle.priceJPY) && vehicle.priceJPY > 0;
  const isElectric = vehicle.fuel.toLowerCase().includes("electric");
  const engineLabel = isElectric
    ? "Electric"
    : typeof vehicle.engineCC === "number" && vehicle.engineCC > 0
      ? `${vehicle.engineCC}cc`
      : "Spec pending";

  // Mini Cost Calculator: Est. Duty = 30% of price (placeholder logic)
  const estDuty = hasPrice ? vehicle.estimatedLandedCostLKR * 0.3 : 0;
  const bidLabel = hasPrice ? formatJPY(vehicle.priceJPY) : "Bid pending";
  const landedLabel = hasPrice
    ? formatLKR(vehicle.estimatedLandedCostLKR)
    : "Awaiting bid";
  const dutyLabel = hasPrice ? formatLKR(estDuty) : "Pending";

  return (
    <Card
      role="link"
      tabIndex={0}
      onClick={() => router.push(href)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          router.push(href);
        }
      }}
      className="group relative flex h-full cursor-pointer flex-col overflow-hidden border-[#546a7b]/65 bg-[#fdfdff] transition-all duration-300 hover:border-[#62929e]/50 hover:shadow-[0_20px_40px_rgba(15,23,42,0.12)]"
    >
      {/* Image Section */}
      <div className="relative h-48 w-full overflow-hidden bg-gray-900 transition-transform duration-700 group-hover:scale-[1.07] group-hover:translate-x-1">
        <div className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          <div className="absolute inset-0 bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.18),transparent)] animate-shimmer" />
          <div className="absolute inset-0 bg-[repeating-linear-gradient(115deg,rgba(255,255,255,0.08)_0_2px,transparent_2px_18px)] opacity-40" />
        </div>
        {!imageError && vehicle.imageUrl ? (
          <Image
            src={vehicle.imageUrl}
            alt={`${vehicle.year} ${vehicle.make} ${vehicle.model}`}
            fill
            sizes="(max-width: 768px) 100vw, (max-width: 1280px) 50vw, 25vw"
            className="object-cover transition-transform duration-700 group-hover:scale-[1.04]"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-700 bg-gradient-to-br from-gray-800 to-black">
            <Car className="w-12 h-12 mb-2 opacity-50" />
            <span className="font-mono text-xs">NO IMAGE</span>
          </div>
        )}

        {/* Overlays */}
        <div className="absolute top-2 left-2 right-2 flex items-start justify-between gap-2 transition-transform duration-300 group-hover:-translate-y-0.5">
          <div className="flex flex-wrap gap-2">
            <Badge className="bg-[#fdfdff]/60 backdrop-blur text-[#393d3f] border-[#546a7b]/65 font-mono">
              {`Stock #${vehicle.lotNumber || "-"}`}
            </Badge>
            <Badge className="bg-[#62929e] text-[#fdfdff] font-bold border-0">
              Grade {vehicle.grade}
            </Badge>
            {vehicle.condition === "New" ? (
              <Badge className="bg-green-500/20 text-green-400 font-bold border-green-500/50">
                NEW
              </Badge>
            ) : (
              <Badge className="bg-gray-500/20 text-[#546a7b] font-bold border-gray-500/50">
                USED
              </Badge>
            )}
          </div>
          {onDelete ? (
            <button
              type="button"
              aria-label={`Delete ${vehicle.make} ${vehicle.model}`}
              disabled={deleteDisabled}
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
                onDelete(vehicle);
              }}
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-red-500/35 bg-black/45 text-red-200 backdrop-blur transition hover:bg-red-600 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          ) : null}
        </div>
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-3 transition-opacity duration-300 group-hover:opacity-90">
          <div className="flex items-center gap-1 text-[#62929e] text-xs font-mono">
            <Timer className="w-3 h-3" />
            <span>
              Ends on {new Date(vehicle.endTime).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {/* Content Section */}
      <CardContent className="flex-1 p-4 space-y-3">
        <div>
          <h3 className="text-lg font-bold text-[#393d3f] truncate">
            {vehicle.year} {vehicle.make} {vehicle.model}
          </h3>
          <p className="text-sm text-[#546a7b] truncate">
            {vehicle.trim} ({vehicle.chassisCode})
          </p>
        </div>

        {/* Specs Grid */}
        <div className="grid grid-cols-3 gap-2 text-xs text-[#546a7b] font-mono py-2 border-y border-[#546a7b]/40">
          <div className="flex flex-col items-center gap-1">
            <Calendar className="w-3 h-3 text-[#393d3f]" />
            {vehicle.year}
          </div>
          <div className="flex flex-col items-center gap-1 border-l border-[#546a7b]/40">
            <Gauge className="w-3 h-3 text-[#393d3f]" />
            {formatKm(vehicle.mileage)} km
          </div>
          <div className="flex flex-col items-center gap-1 border-l border-[#546a7b]/40">
            <Fuel className="w-3 h-3 text-[#393d3f]" />
            {engineLabel}
          </div>
        </div>

        {/* Price Section */}
        <div className="min-h-[100px] space-y-1">
          <div className="flex justify-between items-end">
            <span className="text-xs text-[#546a7b]">Current Bid (JPY)</span>
            <span className="text-sm font-medium text-[#546a7b]">
              {bidLabel}
            </span>
          </div>
          <div className="flex justify-between items-end">
            <span className="text-xs text-[#62929e]">Est. Landed (LKR)</span>
            <span className="text-lg font-bold text-[#393d3f]">
              {landedLabel}
            </span>
          </div>
          <div className="text-right">
            <span className="text-[10px] text-[#546a7b]">
              Est. Duty: {dutyLabel}
            </span>
          </div>
        </div>
      </CardContent>

      <CardFooter className="mt-auto p-4 pt-0">
        <Link
          href={href}
          onClick={(event) => event.stopPropagation()}
          className="flex h-9 w-full items-center justify-center rounded-md border border-[#546a7b]/65 bg-[#c6c5b9]/20 font-mono text-xs text-[#393d3f] transition-colors hover:bg-[#62929e] hover:text-[#fdfdff]"
        >
          VIEW DETAILS &gt;
        </Link>
      </CardFooter>
    </Card>
  );
}
