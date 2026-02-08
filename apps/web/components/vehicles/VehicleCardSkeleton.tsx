import { Card, CardContent, CardFooter } from '@/components/ui/card';

export function VehicleCardSkeleton() {
  return (
    <Card className="border-white/5 bg-[#0A0A0A]">
      <div className="h-48 w-full bg-white/5 animate-pulse" />
      <CardContent className="p-4 space-y-3">
        <div className="space-y-2">
          <div className="h-5 w-3/4 bg-white/5 animate-pulse rounded" />
          <div className="h-3 w-1/2 bg-white/5 animate-pulse rounded" />
        </div>
        <div className="h-10 w-full bg-white/5 animate-pulse rounded my-2" />
        <div className="space-y-2 pt-2">
          <div className="h-4 w-full bg-white/5 animate-pulse rounded" />
          <div className="h-6 w-full bg-white/5 animate-pulse rounded" />
        </div>
      </CardContent>
      <CardFooter className="p-4 pt-0">
        <div className="h-9 w-full bg-white/5 animate-pulse rounded" />
      </CardFooter>
    </Card>
  );
}

export function VehicleGridSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {Array.from({ length: 8 }).map((_, i) => (
        <VehicleCardSkeleton key={i} />
      ))}
    </div>
  );
}