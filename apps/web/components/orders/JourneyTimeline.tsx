import { cn } from "@/lib/utils";

const JOURNEY_STEPS = [
  "Order Placed",
  "Auction Won",
  "Export Customs Cleared",
  "Shipped",
  "Arrived at Port",
  "Cleared Customs",
  "Ready for Delivery",
] as const;

interface JourneyTimelineProps {
  currentStep: number;
}

export function JourneyTimeline({ currentStep }: JourneyTimelineProps) {
  const activeStep = Math.max(1, Math.min(currentStep, JOURNEY_STEPS.length));

  return (
    <ol className="relative ml-3 border-s border-zinc-700 pl-8">
      {JOURNEY_STEPS.map((step, index) => {
        const stepNumber = index + 1;
        const isCompleted = stepNumber < activeStep;
        const isCurrent = stepNumber === activeStep;

        return (
          <li key={step} className="mb-8 last:mb-0">
            <span
              className={cn(
                "absolute -start-[10px] mt-1 h-5 w-5 rounded-full border",
                isCompleted && "border-emerald-400 bg-emerald-500",
                isCurrent && "border-blue-300 bg-blue-500 animate-pulse",
                !isCompleted && !isCurrent && "border-zinc-500 bg-zinc-700",
              )}
            />

            <p
              className={cn(
                "text-xs uppercase tracking-widest",
                isCompleted && "text-emerald-300",
                isCurrent && "text-blue-300",
                !isCompleted && !isCurrent && "text-zinc-500",
              )}
            >
              Step {stepNumber}
            </p>

            <p
              className={cn(
                "text-sm font-medium",
                isCompleted && "text-emerald-100",
                isCurrent && "text-blue-100",
                !isCompleted && !isCurrent && "text-zinc-400",
              )}
            >
              {step}
            </p>
          </li>
        );
      })}
    </ol>
  );
}
