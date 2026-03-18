import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { Vehicle } from "@/types/vehicle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Fuel, Gauge, Calendar, Timer, Car } from "lucide-react";

interface VehicleCardProps {
  vehicle: Vehicle;
}

export function VehicleCard({ vehicle }: VehicleCardProps) {
  const [imageError, setImageError] = useState(false);

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

  // Mini Cost Calculator: Est. Duty = 30% of price (placeholder logic)
  const estDuty = hasPrice ? vehicle.estimatedLandedCostLKR * 0.3 : 0;

  return (
    <Card className="group relative overflow-hidden border-[#546a7b]/65 bg-[#fdfdff] hover:border-[#62929e]/50 transition-all duration-300 hover:shadow-[0_20px_40px_rgba(15,23,42,0.12)]">
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
        <div className="absolute top-2 left-2 flex gap-2 transition-transform duration-300 group-hover:-translate-y-0.5">
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
      <CardContent className="p-4 space-y-3">
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
            {vehicle.engineCC}cc
          </div>
        </div>

        {/* Price Section */}
        <div className="space-y-1">
          {hasPrice ? (
            <>
              <div className="flex justify-between items-end">
                <span className="text-xs text-[#546a7b]">Current Bid (JPY)</span>
                <span className="text-sm font-medium text-[#546a7b]">
                  {formatJPY(vehicle.priceJPY)}
                </span>
              </div>
              <div className="flex justify-between items-end">
                <span className="text-xs text-[#62929e]">
                  Est. Landed (LKR)
                </span>
                <span className="text-lg font-bold text-[#393d3f]">
                  {formatLKR(vehicle.estimatedLandedCostLKR)}
                </span>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-[#546a7b]">
                  Est. Duty: {formatLKR(estDuty)}
                </span>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-between text-xs text-[#546a7b]">
              <span>Price</span>
              <span className="text-[#546a7b]">Pending</span>
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter className="p-4 pt-0">
        <Link href={`/dashboard/vehicles/${vehicle.id}`} className="w-full">
          <Button className="w-full bg-[#c6c5b9]/20 hover:bg-[#62929e] hover:text-[#fdfdff] text-[#393d3f] border border-[#546a7b]/65 transition-colors font-mono text-xs h-9">
            VIEW DETAILS &gt;
          </Button>
        </Link>
      </CardFooter>
    </Card>
  );
}

