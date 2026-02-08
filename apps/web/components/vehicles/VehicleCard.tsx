import Link from 'next/link';
import { Vehicle } from '@/types/vehicle';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Fuel, Gauge, Calendar, Timer } from 'lucide-react';

interface VehicleCardProps {
  vehicle: Vehicle;
}

export function VehicleCard({ vehicle }: VehicleCardProps) {
  const formatJPY = new Intl.NumberFormat('ja-JP', { style: 'currency', currency: 'JPY', maximumSignificantDigits: 3 }).format;
  const formatLKR = new Intl.NumberFormat('en-LK', { style: 'currency', currency: 'LKR', maximumSignificantDigits: 3 }).format;
  const formatKm = new Intl.NumberFormat('en-US').format;

  return (
    <Card className="group relative overflow-hidden border-white/10 bg-[#0A0A0A] hover:border-[#FE7743]/50 transition-all duration-300 hover:shadow-[0_0_20px_rgba(254,119,67,0.1)]">
      
      {/* Image Section */}
      <div className="relative h-48 w-full overflow-hidden bg-gray-900">
         <div className="absolute inset-0 flex items-center justify-center text-gray-700 font-mono text-xs bg-gradient-to-br from-gray-800 to-black">
            NO IMAGE DATA
         </div>
         
         {/* Overlays */}
         <div className="absolute top-2 left-2 flex gap-2">
            <Badge className="bg-black/60 backdrop-blur text-white border-white/20 font-mono">{vehicle.lotNumber}</Badge>
            <Badge className="bg-[#FE7743] text-black font-bold border-0">Grade {vehicle.grade}</Badge>
         </div>
         <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-3">
             <div className="flex items-center gap-1 text-[#FE7743] text-xs font-mono">
                <Timer className="w-3 h-3" />
                <span>Ends in 14h 32m</span>
             </div>
         </div>
      </div>

      {/* Content Section */}
      <CardContent className="p-4 space-y-3">
        <div>
            <h3 className="text-lg font-bold text-white truncate">{vehicle.year} {vehicle.make} {vehicle.model}</h3>
            <p className="text-sm text-gray-400 truncate">{vehicle.trim} ({vehicle.chassisCode})</p>
        </div>

        {/* Specs Grid */}
        <div className="grid grid-cols-3 gap-2 text-xs text-gray-500 font-mono py-2 border-y border-white/5">
            <div className="flex flex-col items-center gap-1">
                <Calendar className="w-3 h-3 text-gray-600" />
                {vehicle.year}
            </div>
            <div className="flex flex-col items-center gap-1 border-l border-white/5">
                <Gauge className="w-3 h-3 text-gray-600" />
                {formatKm(vehicle.mileage)} km
            </div>
            <div className="flex flex-col items-center gap-1 border-l border-white/5">
                <Fuel className="w-3 h-3 text-gray-600" />
                {vehicle.engineCC}cc
            </div>
        </div>

        {/* Price Section */}
        <div className="space-y-1">
            <div className="flex justify-between items-end">
                <span className="text-xs text-gray-500">Current Bid (JPY)</span>
                <span className="text-sm font-medium text-gray-300">{formatJPY(vehicle.priceJPY)}</span>
            </div>
            <div className="flex justify-between items-end">
                <span className="text-xs text-[#FE7743]">Est. Landed (LKR)</span>
                <span className="text-lg font-bold text-white">{formatLKR(vehicle.estimatedLandedCostLKR)}</span>
            </div>
        </div>
      </CardContent>

      <CardFooter className="p-4 pt-0">
        <Link href={`/vehicles/${vehicle.id}`} className="w-full">
            <Button className="w-full bg-white/5 hover:bg-[#FE7743] hover:text-black text-white border border-white/10 transition-colors font-mono text-xs h-9">
                VIEW DETAILS &gt;
            </Button>
        </Link>
      </CardFooter>
    </Card>
  );
}